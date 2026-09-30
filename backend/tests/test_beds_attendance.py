import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.core.permissions import SystemPermissions as P
from app.core.role_catalog import ROLE_BY_CODE
from app.core.security import create_access_token, get_password_hash
from app.models.beds import BedCensusLog, BedInventory, WardType
from app.models.facility import Facility, FacilityType
from app.models.healthcare import AttendanceStatus, StaffAttendance
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.models.organization import Organization, OrganizationType

pytestmark = pytest.mark.asyncio
BASE = "/api/v1/capacity"


async def _facility(db, org, code, state, district):
    f = Facility(organization_id=org.id, name=f"{code} PHC", code=code, facility_type=FacilityType.PHC,
                 state=state, district=district, is_active=True)
    db.add(f)
    await db.flush()
    return f


async def _user(db, org, fac, role_code, scope, perms=None):
    """User whose role permissions come from the production role catalogue unless `perms` is given."""
    perms = perms if perms is not None else ROLE_BY_CODE[role_code]["permissions"]
    role = Role(name=f"{role_code}-{uuid.uuid4().hex[:6]}", code=f"{role_code}_{uuid.uuid4().hex[:6]}",
                is_system=False, is_active=True)
    db.add(role)
    await db.flush()
    for code in perms:
        pid = (await db.execute(select(Permission.id).where(Permission.code == code))).scalar_one()
        db.add(RolePermission(role_id=role.id, permission_id=pid))
    u = User(email=f"{uuid.uuid4().hex[:8]}@t.gov.in", hashed_password=get_password_hash("x"), full_name=role_code,
             organization_id=org.id, facility_id=fac.id, is_active=True, is_verified=True)
    db.add(u)
    await db.flush()
    db.add(UserRole(user_id=u.id, role_id=role.id, organization_id=org.id, facility_id=fac.id, scope_level=scope))
    await db.flush()
    return u, {"Authorization": f"Bearer {create_access_token(u.id, extra_claims={'email': u.email})}"}


@pytest_asyncio.fixture
async def world(db_session, seeded_data):
    db = db_session
    org = seeded_data["org"]
    a = seeded_data["facility"]  # Tamil Nadu / Chengalpattu
    b = await _facility(db, org, "B-MDU", "Tamil Nadu", "Madurai")
    c = await _facility(db, org, "C-EKM", "Kerala", "Ernakulam")
    users = {
        "nurse": await _user(db, org, a, "NURSE", ScopeLevel.FACILITY),
        "doctor": await _user(db, org, a, "DOCTOR", ScopeLevel.FACILITY),
        "incharge": await _user(db, org, a, "PHC_IN_CHARGE", ScopeLevel.FACILITY),
        "incharge_b": await _user(db, org, b, "PHC_IN_CHARGE", ScopeLevel.FACILITY),
        "dho": await _user(db, org, a, "DISTRICT_HEALTH_OFFICER", ScopeLevel.DISTRICT),
        "state": await _user(db, org, a, "STATE_HEALTH_ADMIN", ScopeLevel.STATE),
        "national": await _user(db, org, a, "NATIONAL_HEALTH_AUTHORITY", ScopeLevel.GLOBAL),
    }
    await db.commit()
    return {"a": a, "b": b, "c": c, "org": org, **{k: v[1] for k, v in users.items()},
            **{f"{k}_user": v[0] for k, v in users.items()}}


async def _set_beds(db, fac, ward, total, occupied, age=timedelta(0), user_id=None):
    ts = datetime.now(timezone.utc) - age
    db.add(BedInventory(facility_id=fac.id, ward_type=ward, total_beds=total, occupied_beds=occupied,
                        last_updated_by=user_id, created_at=ts, updated_at=ts))
    await db.commit()


# ------------------------------------------------------------------ facility endpoints
async def test_incharge_registers_ward_nurse_updates_occupancy_and_log_is_appended(async_client, world, db_session):
    a = world["a"]
    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/GENERAL", headers=world["incharge"],
                               json={"total_beds": 10, "occupied_beds": 4})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["available_beds"] == 6

    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/GENERAL", headers=world["nurse"],
                               json={"occupied_beds": 7, "note": "evening census"})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["available_beds"] == 3
    assert r.json()["data"]["last_updated_by"] == str(world["nurse_user"].id)

    rows = (await db_session.execute(select(BedCensusLog).order_by(BedCensusLog.recorded_at))).scalars().all()
    assert [(x.occupied_beds, x.previous_occupied_beds) for x in rows] == [(4, None), (7, 4)]

    r = await async_client.get(f"{BASE}/facilities/{a.id}/beds/history", headers=world["nurse"])
    assert r.status_code == 200 and len(r.json()["data"]) == 2

    r = await async_client.get(f"{BASE}/facilities/{a.id}/beds", headers=world["doctor"])
    d = r.json()["data"]
    assert (d["status"], d["total_beds"], d["occupied_beds"], d["available_beds"]) == ("FRESH", 10, 7, 3)


async def test_permission_denials(async_client, world, db_session):
    a = world["a"]
    # doctor holds beds.read only
    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/GENERAL", headers=world["doctor"],
                               json={"occupied_beds": 1})
    assert r.status_code == 403
    # nurse cannot register a ward or change capacity
    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/ICU", headers=world["nurse"],
                               json={"total_beds": 4, "occupied_beds": 1})
    assert r.status_code == 404
    await _set_beds(db_session, a, WardType.GENERAL, 10, 2)
    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/GENERAL", headers=world["nurse"],
                               json={"total_beds": 50, "occupied_beds": 2})
    assert r.status_code == 403
    # occupancy over capacity is rejected
    r = await async_client.put(f"{BASE}/facilities/{a.id}/beds/GENERAL", headers=world["nurse"],
                               json={"occupied_beds": 11})
    assert r.status_code == 400
    # unauthenticated
    assert (await async_client.get(f"{BASE}/facilities/{a.id}/beds")).status_code in (401, 403)
    # governance roll-ups need governance permissions
    for path in ("district", "state", "national"):
        assert (await async_client.get(f"{BASE}/{path}", headers=world["nurse"])).status_code == 403


async def test_facility_scope_isolation(async_client, world, db_session):
    a, b = world["a"], world["b"]
    await _set_beds(db_session, b, WardType.GENERAL, 8, 3)
    assert (await async_client.get(f"{BASE}/facilities/{b.id}/beds", headers=world["nurse"])).status_code == 403
    assert (await async_client.put(f"{BASE}/facilities/{b.id}/beds/GENERAL", headers=world["incharge"],
                                   json={"occupied_beds": 1})).status_code == 403
    assert (await async_client.get(f"{BASE}/facilities/{b.id}/beds/history", headers=world["nurse"])).status_code == 403
    # DHO of Chengalpattu cannot read Madurai beds; the Madurai in-charge can
    assert (await async_client.get(f"{BASE}/facilities/{b.id}/beds", headers=world["dho"])).status_code == 403
    assert (await async_client.get(f"{BASE}/facilities/{b.id}/beds", headers=world["incharge_b"])).status_code == 200
    assert (await async_client.get(f"{BASE}/facilities/{uuid.uuid4()}/beds", headers=world["national"])).status_code == 404


# ------------------------------------------------------------------ roll-ups
async def _attendance(db, fac, user_id, age=timedelta(hours=2), status=AttendanceStatus.PRESENT):
    ts = datetime.now(timezone.utc) - age
    db.add(StaffAttendance(user_id=user_id, facility_id=fac.id, attendance_date=ts.date(), check_in_time=ts,
                           status=status, shift="GENERAL"))
    await db.commit()


async def test_rollup_scoping_across_district_state_national(async_client, world, db_session):
    a, b, c = world["a"], world["b"], world["c"]
    await _set_beds(db_session, a, WardType.GENERAL, 10, 4)
    await _set_beds(db_session, b, WardType.GENERAL, 20, 5)
    await _set_beds(db_session, c, WardType.ICU, 6, 6)

    r = await async_client.get(f"{BASE}/district", headers=world["dho"])
    d = r.json()["data"]
    assert r.status_code == 200
    assert (d["beds"]["total"], d["beds"]["occupied"], d["beds"]["available"]) == (10, 4, 6)
    assert {f["facility_id"] for f in d["breakdown"]} == {str(a.id)}
    # cannot widen to another district / state via query params, nor call the state roll-up
    assert (await async_client.get(f"{BASE}/district?state=Tamil Nadu&district=Madurai", headers=world["dho"])).status_code == 403
    assert (await async_client.get(f"{BASE}/district?state=Kerala&district=Ernakulam", headers=world["dho"])).status_code == 403
    assert (await async_client.get(f"{BASE}/state", headers=world["dho"])).status_code == 403

    r = await async_client.get(f"{BASE}/state", headers=world["state"])
    d = r.json()["data"]
    assert r.status_code == 200
    assert (d["beds"]["total"], d["beds"]["occupied"]) == (30, 9)  # Kerala excluded
    assert {(x["state"], x["district"]) for x in d["breakdown"]} == {("Tamil Nadu", "Chengalpattu"), ("Tamil Nadu", "Madurai")}
    assert (await async_client.get(f"{BASE}/state?state=Kerala", headers=world["state"])).status_code == 403
    assert (await async_client.get(f"{BASE}/national", headers=world["state"])).status_code == 403
    r = await async_client.get(f"{BASE}/district?district=Madurai", headers=world["state"])
    assert r.status_code == 200 and r.json()["data"]["beds"]["total"] == 20

    r = await async_client.get(f"{BASE}/national", headers=world["national"])
    d = r.json()["data"]
    assert r.status_code == 200
    assert (d["beds"]["total"], d["beds"]["occupied"], d["beds"]["available"]) == (36, 15, 21)
    assert {x["state"] for x in d["breakdown"]} == {"Tamil Nadu", "Kerala"}
    assert d["beds"]["by_ward"]["ICU"] == {"total": 6, "occupied": 6, "available": 0}
    r = await async_client.get(f"{BASE}/state?state=Kerala", headers=world["national"])
    assert r.status_code == 200 and r.json()["data"]["beds"]["total"] == 6
    assert (await async_client.get(f"{BASE}/state", headers=world["national"])).status_code == 400  # state required


async def test_staleness_and_no_data_flags_never_fabricate(async_client, world, db_session):
    a, b, c = world["a"], world["b"], world["c"]
    await _set_beds(db_session, a, WardType.GENERAL, 10, 4, age=timedelta(hours=1))         # fresh
    await _set_beds(db_session, b, WardType.GENERAL, 20, 5, age=timedelta(hours=30))        # stale
    # facility c: no bed rows at all
    r = await async_client.get(f"{BASE}/national", headers=world["national"])
    d = r.json()["data"]
    beds = d["beds"]
    assert beds["facilities_fresh"] == 1 and beds["facilities_stale"] == 1 and beds["facilities_no_data"] == 1
    # totals count recorded values only; the no-data facility contributes nothing (not a made-up 0-bed ward)
    assert beds["total"] == 30 and beds["occupied"] == 9
    assert (beds["fresh_total"], beds["fresh_occupied"], beds["fresh_available"]) == (10, 4, 6)
    flagged = {f["facility_id"]: f for f in d["flagged_facilities"]}
    assert flagged[str(b.id)]["beds_status"] == "STALE" and flagged[str(c.id)]["beds_status"] == "NO_DATA"
    assert d["as_of"] and d["stale_after_hours"] == 24
    assert flagged[str(c.id)]["beds_last_updated_at"] is None

    # the facility view of a no-data facility returns nulls, not zeros
    r = await async_client.get(f"{BASE}/facilities/{c.id}/beds", headers=world["national"])
    fd = r.json()["data"]
    assert fd["status"] == "NO_DATA" and fd["total_beds"] is None and fd["available_beds"] is None and fd["wards"] == []

    # occupancy update refreshes a stale facility
    r = await async_client.put(f"{BASE}/facilities/{b.id}/beds/GENERAL", headers=world["incharge_b"],
                               json={"occupied_beds": 5})
    assert r.status_code == 200
    d = (await async_client.get(f"{BASE}/national", headers=world["national"])).json()["data"]
    assert d["beds"]["facilities_stale"] == 0 and d["beds"]["facilities_fresh"] == 2


async def test_empty_jurisdiction_has_null_percentages(async_client, world, db_session):
    d = (await async_client.get(f"{BASE}/national", headers=world["national"])).json()["data"]
    assert d["beds"]["total"] == 0 and d["beds"]["occupancy_pct"] is None
    assert d["staff"]["availability_pct"] is None and d["staff"]["present_today"] == 0
    assert d["beds"]["facilities_no_data"] == 3 and d["flagged_facilities_count"] == 3


async def test_staff_attendance_rollup_only_counts_reporting_facilities(async_client, world, db_session):
    a, b, c = world["a"], world["b"], world["c"]
    # facility a: 7 active users (from fixtures + seeded_data) assigned; two present today
    await _attendance(db_session, a, world["nurse_user"].id)
    await _attendance(db_session, a, world["doctor_user"].id, status=AttendanceStatus.HALF_DAY)
    await _attendance(db_session, a, world["incharge_user"].id, status=AttendanceStatus.ON_LEAVE)
    # facility b: last attendance 3 days ago -> stale, present unknown
    await _attendance(db_session, b, world["incharge_b_user"].id, age=timedelta(days=3))
    d = (await async_client.get(f"{BASE}/national", headers=world["national"])).json()["data"]
    staff = d["staff"]
    assigned_a = (await db_session.execute(
        select(func.count(User.id)).where(User.facility_id == a.id, User.is_active.is_(True)))).scalar_one()
    assert staff["present_today"] == 2
    assert staff["assigned_in_reporting_facilities"] == assigned_a
    assert staff["availability_pct"] == round(100 * 2 / assigned_a, 1)
    assert (staff["facilities_attendance_fresh"], staff["facilities_attendance_stale"],
            staff["facilities_attendance_no_data"]) == (1, 1, 1)
    rows = {x["facility_id"]: x for x in
            (await async_client.get(f"{BASE}/district?district=Madurai", headers=world["state"])).json()["data"]["breakdown"]}
    assert rows[str(b.id)]["staff"]["present_today"] is None  # unknown, not 0


# ------------------------------------------------------------------ seed script
async def test_seed_india_demo_is_idempotent_and_feeds_rollups(async_client, world, db_session):
    from scripts.seed_india_demo import NETWORK, seed_india_demo
    from app.models.pharmacy import InventoryItem, StockMovement, StockMovementType

    first = await seed_india_demo(db_session, states=["Kerala", "Bihar"], history_days=7)
    assert first["facilities"] == 18 and first["bed_rows"] > 0 and first["dispense_movements"] > 0
    assert first["inventory_items"] == 18 * 15
    second = await seed_india_demo(db_session, states=["Kerala", "Bihar"], history_days=7)
    assert second == {k: 0 for k in first}

    assert (await db_session.execute(select(func.count(Facility.id)).where(Facility.code.like("IN-%")))).scalar_one() == 18
    disp = (await db_session.execute(select(func.count(StockMovement.id)).where(
        StockMovement.movement_type == StockMovementType.DISPENSE))).scalar_one()
    assert disp == first["dispense_movements"]
    # ledger reconciles with stock on hand
    item = (await db_session.execute(select(InventoryItem).limit(1))).scalar_one()
    last = (await db_session.execute(select(StockMovement.balance_after).where(
        StockMovement.inventory_item_id == item.id).order_by(StockMovement.created_at.desc()).limit(1))).scalar_one()
    assert last == item.quantity_on_hand
    assert len(NETWORK) == 8

    d = (await async_client.get(f"{BASE}/national", headers=world["national"])).json()["data"]
    assert {"Kerala", "Bihar", "Tamil Nadu"} <= {x["state"] for x in d["breakdown"]}
    assert d["beds"]["total"] > 0
    assert d["beds"]["facilities_stale"] >= 1 and d["beds"]["facilities_no_data"] >= 1  # deliberate gaps
    r = await async_client.get(f"{BASE}/state?state=Kerala", headers=world["national"])
    assert {x["district"] for x in r.json()["data"]["breakdown"]} == {"Thiruvananthapuram", "Ernakulam", "Kozhikode"}
