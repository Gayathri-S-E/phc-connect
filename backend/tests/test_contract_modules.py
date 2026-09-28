import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication
from app.models.identity import Role, ScopeLevel, User, UserRole
from app.models.intelligence import ForecastRecord


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def ctx(db_session: AsyncSession, seeded_data: dict) -> dict:
    """seeded_data plus a second GLOBAL admin (for segregation-of-duties checks) and a stocked medication."""
    admin_role = (await db_session.execute(select(Role).where(Role.code == "SUPER_ADMIN"))).scalar_one()
    approver = User(
        id=uuid.uuid4(),
        email="approver@test.gov.in",
        hashed_password=get_password_hash("ApproverPass123!"),
        full_name="Approver",
        organization_id=seeded_data["org"].id,
        facility_id=seeded_data["facility"].id,
        is_active=True,
        is_verified=True,
    )
    other_fac = Facility(
        id=uuid.uuid4(),
        organization_id=seeded_data["org"].id,
        name="Test CHC Other District",
        code="TEST-CHC-OTHER",
        facility_type=FacilityType.CHC,
        state="Tamil Nadu",
        district="Madurai",
        is_active=True,
    )
    med = Medication(id=uuid.uuid4(), name="Oxytocin 10IU", code="MED-OXY-10", dosage_form="Vial",
                     strength="10IU", is_active=True)
    db_session.add_all([approver, other_fac, med])
    await db_session.flush()
    db_session.add(UserRole(user_id=approver.id, role_id=admin_role.id, organization_id=seeded_data["org"].id,
                            facility_id=seeded_data["facility"].id, scope_level=ScopeLevel.GLOBAL))
    await db_session.commit()
    return {
        **seeded_data,
        "approver_token": create_access_token(approver.id),
        "other_facility": other_fac,
        "med": med,
    }


async def receive(client: AsyncClient, token: str, facility_id, med_id, qty=100, lot="LOT-001", days=200, **extra):
    res = await client.post(
        "/api/v1/inventory/batches",
        json={
            "facility_id": str(facility_id),
            "medication_id": str(med_id),
            "batch_number": lot,
            "manufacture_date": str(date.today() - timedelta(days=30)),
            "expiry_date": str(date.today() + timedelta(days=days)),
            "quantity": qty,
            **extra,
        },
        headers=auth(token),
    )
    assert res.status_code == 201, res.text
    return res.json()["data"]


async def issued_po(client: AsyncClient, c: dict) -> dict:
    admin, approver, fac = c["admin_token"], c["approver_token"], c["facility"]
    sup = await client.post("/api/v1/suppliers", json={"name": "Cold Pharma Ltd", "code": "SUP-COLD"},
                            headers=auth(admin))
    assert sup.status_code == 201, sup.text
    po = await client.post("/api/v1/procurement/orders", json={
        "supplier_id": sup.json()["data"]["id"], "destination_facility_id": str(fac.id), "total_amount": "1500.00",
    }, headers=auth(admin))
    assert po.status_code == 201, po.text
    ok = await client.post(f"/api/v1/procurement/orders/{po.json()['data']['id']}/approve", headers=auth(approver))
    assert ok.status_code == 200, ok.text
    return ok.json()["data"]


@pytest.mark.asyncio
async def test_procurement_request_to_po_with_segregation_of_duties(async_client: AsyncClient, ctx: dict):
    admin, approver, fac = ctx["admin_token"], ctx["approver_token"], ctx["facility"]

    sup = await async_client.post("/api/v1/suppliers", json={
        "name": "National Pharma Distributors", "code": "SUP-NPD", "contact_email": "ops@npd.example",
        "reliability_score": "0.95",
    }, headers=auth(admin))
    assert sup.status_code == 201, sup.text
    supplier_id = sup.json()["data"]["id"]
    dup = await async_client.post("/api/v1/suppliers", json={"name": "Dup", "code": "SUP-NPD"}, headers=auth(admin))
    assert dup.status_code == 409
    listed = await async_client.get("/api/v1/suppliers?search=national", headers=auth(admin))
    assert listed.json()["pagination"]["total"] == 1

    pr = await async_client.post("/api/v1/procurement/requests", json={
        "facility_id": str(fac.id), "urgency": "URGENT", "total_estimated_cost": "12000", "notes": "Monsoon buffer",
    }, headers=auth(admin))
    assert pr.status_code == 201, pr.text
    pr_id = pr.json()["data"]["id"]

    # PO cannot be raised from an unapproved request
    early = await async_client.post("/api/v1/procurement/orders", json={
        "supplier_id": supplier_id, "destination_facility_id": str(fac.id), "purchase_request_id": pr_id,
    }, headers=auth(admin))
    assert early.status_code == 400

    self_approve = await async_client.post(f"/api/v1/procurement/requests/{pr_id}/approve", json={},
                                           headers=auth(admin))
    assert self_approve.status_code == 400
    approved = await async_client.post(f"/api/v1/procurement/requests/{pr_id}/approve",
                                       json={"notes": "Within district budget"}, headers=auth(approver))
    assert approved.json()["data"]["status"] == "DISTRICT_APPROVED"

    po = await async_client.post("/api/v1/procurement/orders", json={
        "supplier_id": supplier_id, "destination_facility_id": str(fac.id), "purchase_request_id": pr_id,
        "total_amount": "11800.50", "expected_delivery_date": str(date.today() + timedelta(days=10)),
    }, headers=auth(admin))
    assert po.status_code == 201, po.text
    po_data = po.json()["data"]
    assert po_data["status"] == "DRAFT" and po_data["po_number"].startswith("PO-")

    requests = await async_client.get("/api/v1/procurement/requests?status=CONVERTED_TO_PO", headers=auth(admin))
    assert requests.json()["pagination"]["total"] == 1

    assert (await async_client.post(f"/api/v1/procurement/orders/{po_data['id']}/approve",
                                    headers=auth(admin))).status_code == 400
    issued = await async_client.post(f"/api/v1/procurement/orders/{po_data['id']}/approve", headers=auth(approver))
    assert issued.json()["data"]["status"] == "ISSUED"
    assert (await async_client.post(f"/api/v1/procurement/orders/{po_data['id']}/approve",
                                    headers=auth(approver))).status_code == 400

    orders = await async_client.get("/api/v1/procurement/orders?status=ISSUED", headers=auth(admin))
    assert orders.json()["pagination"]["total"] == 1
    assert (await async_client.get("/api/v1/procurement/orders", headers=auth(ctx["doctor_token"]))).status_code == 403


@pytest.mark.asyncio
async def test_shipment_lifecycle_cold_chain_alert_and_acknowledgement(async_client: AsyncClient, ctx: dict):
    admin = ctx["admin_token"]
    po = await issued_po(async_client, ctx)

    both = await async_client.post("/api/v1/shipments", json={
        "purchase_order_id": po["id"], "transfer_id": str(uuid.uuid4()),
    }, headers=auth(admin))
    assert both.status_code == 422

    shp = await async_client.post("/api/v1/shipments", json={
        "purchase_order_id": po["id"], "carrier_name": "ColdLine Logistics", "temperature_monitored": True,
    }, headers=auth(admin))
    assert shp.status_code == 201, shp.text
    shipment = shp.json()["data"]
    assert shipment["status"] == "PENDING" and shipment["tracking_number"].startswith("SHP-")
    sid = shipment["id"]

    dep = await async_client.post(f"/api/v1/shipments/{sid}/events", json={
        "event_type": "DEPARTED", "location_name": "Chennai CMS", "latitude": "13.08", "longitude": "80.27",
    }, headers=auth(admin))
    assert dep.status_code == 201, dep.text
    assert dep.json()["data"]["status"] == "IN_TRANSIT" and dep.json()["data"]["dispatched_at"]
    orders = await async_client.get("/api/v1/procurement/orders?status=IN_TRANSIT", headers=auth(admin))
    assert orders.json()["pagination"]["total"] == 1

    no_temp = await async_client.post(f"/api/v1/shipments/{sid}/events", json={"event_type": "TEMPERATURE_EXCURSION"},
                                      headers=auth(admin))
    assert no_temp.status_code == 400
    exc = await async_client.post(f"/api/v1/shipments/{sid}/events", json={
        "event_type": "TEMPERATURE_EXCURSION", "recorded_temp": "11.5", "location_name": "Tindivanam toll",
    }, headers=auth(admin))
    assert exc.status_code == 201

    alerts = await async_client.get("/api/v1/alerts?alert_type=COLD_CHAIN_BREACH", headers=auth(admin))
    assert alerts.json()["pagination"]["total"] == 1
    alert = alerts.json()["data"][0]
    assert alert["severity"] == "CRITICAL" and not alert["is_acknowledged"]

    ack = await async_client.post(f"/api/v1/alerts/{alert['id']}/ack", json={"notes": "Stock quarantined"},
                                  headers=auth(admin))
    assert ack.status_code == 200 and ack.json()["data"]["is_acknowledged"]
    assert (await async_client.post(f"/api/v1/alerts/{alert['id']}/ack", headers=auth(admin))).status_code == 409
    active = await async_client.get("/api/v1/alerts", headers=auth(admin))
    assert active.json()["pagination"]["total"] == 0
    everything = await async_client.get("/api/v1/alerts?state=all", headers=auth(admin))
    assert everything.json()["pagination"]["total"] == 1

    done = await async_client.post(f"/api/v1/shipments/{sid}/events", json={"event_type": "DELIVERED"},
                                   headers=auth(admin))
    body = done.json()["data"]
    assert body["status"] == "DELIVERED" and body["delivered_at"] and len(body["events"]) == 3
    fulfilled = await async_client.get("/api/v1/procurement/orders?status=FULFILLED", headers=auth(admin))
    assert fulfilled.json()["pagination"]["total"] == 1
    late = await async_client.post(f"/api/v1/shipments/{sid}/events", json={"event_type": "DELAY_REPORTED"},
                                   headers=auth(admin))
    assert late.status_code == 400

    listed = await async_client.get("/api/v1/shipments?status=DELIVERED", headers=auth(admin))
    assert listed.json()["pagination"]["total"] == 1


@pytest.mark.asyncio
async def test_shortage_escalation_is_upward_only_and_raises_alert(async_client: AsyncClient, ctx: dict):
    admin, fac, med = ctx["admin_token"], ctx["facility"], ctx["med"]
    rep = await async_client.post("/api/v1/shortages", json={
        "facility_id": str(fac.id), "medication_id": str(med.id), "severity": "CRITICAL",
        "description": "Oxytocin stock exhausted in labour ward",
    }, headers=auth(admin))
    assert rep.status_code == 201, rep.text
    iid = rep.json()["data"]["id"]

    d = await async_client.post(f"/api/v1/shortages/{iid}/escalate",
                                json={"level": "DISTRICT", "notes": "No surplus in block"}, headers=auth(admin))
    assert d.status_code == 200, d.text
    assert d.json()["data"]["status"] == "ESCALATED_DISTRICT"
    again = await async_client.post(f"/api/v1/shortages/{iid}/escalate",
                                    json={"level": "DISTRICT", "notes": "Repeat escalation"}, headers=auth(admin))
    assert again.status_code == 400
    s = await async_client.post(f"/api/v1/shortages/{iid}/escalate",
                                json={"level": "STATE", "notes": "District buffer exhausted"}, headers=auth(admin))
    assert s.json()["data"]["status"] == "ESCALATED_STATE"

    alerts = await async_client.get("/api/v1/alerts?alert_type=CRITICAL_SHORTAGE", headers=auth(admin))
    assert alerts.json()["pagination"]["total"] == 2
    assert {a["severity"] for a in alerts.json()["data"]} == {"EMERGENCY"}

    resolved = await async_client.post(f"/api/v1/shortages/{iid}/resolve",
                                       json={"resolution_notes": "State buffer transfer received"},
                                       headers=auth(admin))
    assert resolved.status_code == 200 and resolved.json()["data"]["status"] == "RESOLVED"
    closed = await async_client.post(f"/api/v1/shortages/{iid}/escalate",
                                     json={"level": "STATE", "notes": "Too late now"}, headers=auth(admin))
    assert closed.status_code == 400


@pytest.mark.asyncio
async def test_forecast_risk_analysis_and_dashboards(async_client: AsyncClient, db_session: AsyncSession, ctx: dict):
    admin, fac, med = ctx["admin_token"], ctx["facility"], ctx["med"]
    await receive(async_client, admin, fac.id, med.id, qty=50, lot="OXY-SOON", days=20)

    fc = await async_client.post("/api/v1/ai/forecast", json={"facility_id": str(fac.id), "horizon_days": 60},
                                 headers=auth(admin))
    assert fc.status_code == 200, fc.text
    data = fc.json()["data"]
    assert data["horizon_days"] == 60 and len(data["items"]) == 1 and data["disclaimer"]
    item = data["items"][0]
    assert item["confidence_interval_lower"] <= item["predicted_consumption"] <= item["confidence_interval_upper"]
    stored = (await db_session.execute(select(func.count(ForecastRecord.id)))).scalar_one()
    assert stored == 1
    bad = await async_client.post("/api/v1/ai/forecast", json={"horizon_days": 45}, headers=auth(admin))
    assert bad.status_code == 422

    risk = await async_client.post("/api/v1/ai/risk-analysis", json={}, headers=auth(admin))
    assert risk.status_code == 200, risk.text
    r = risk.json()["data"]
    assert 0 <= r["risk_score"] <= 100 and len(r["factors"]) == 6 and r["recommendations"]
    expiring = next(f for f in r["factors"] if f["factor"] == "expiring_batch_ratio")
    assert expiring["value"] == 1.0

    phc = await async_client.get("/api/v1/dashboards/phc", headers=auth(admin))
    assert phc.status_code == 200, phc.text
    assert phc.json()["data"]["batches_expiring_30d"] == 1

    sc = await async_client.get("/api/v1/dashboards/supply-chain", headers=auth(admin))
    assert sc.status_code == 200, sc.text
    body = sc.json()["data"]
    assert body["scope"] == "GLOBAL" and body["facilities_in_scope"] == 2
    row = next(f for f in body["facilities"] if f["facility_id"] == str(fac.id))
    assert row["items_tracked"] == 1

    doctor = auth(ctx["doctor_token"])
    assert (await async_client.get("/api/v1/dashboards/supply-chain", headers=doctor)).status_code == 403
    assert (await async_client.post("/api/v1/ai/risk-analysis", json={}, headers=doctor)).status_code == 403


@pytest.mark.asyncio
async def test_identity_contract_endpoints(async_client: AsyncClient, ctx: dict):
    admin = ctx["admin_token"]

    login = await async_client.post("/api/v1/auth/login",
                                    json={"email": "doctor@test.gov.in", "password": "DoctorPass123!"})
    refresh_token = login.json()["data"]["refresh_token"]
    doctor = auth(login.json()["data"]["access_token"])

    wrong = await async_client.post("/api/v1/auth/change-password",
                                    json={"current_password": "nope-nope", "new_password": "NewDoctor123!"},
                                    headers=doctor)
    assert wrong.status_code == 400
    ok = await async_client.post("/api/v1/auth/change-password",
                                 json={"current_password": "DoctorPass123!", "new_password": "NewDoctor123!"},
                                 headers=doctor)
    assert ok.status_code == 200
    assert (await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})).status_code == 401
    assert (await async_client.post("/api/v1/auth/login", json={
        "email": "doctor@test.gov.in", "password": "NewDoctor123!"})).status_code == 200

    roles = (await async_client.get("/api/v1/roles", headers=auth(admin))).json()["data"]
    doctor_role = next(r for r in roles if r["code"] == "DOCTOR")
    admin_role = next(r for r in roles if r["code"] == "SUPER_ADMIN")
    renamed = await async_client.patch(f"/api/v1/roles/{doctor_role['id']}", json={"name": "Medical Officer (MO)"},
                                       headers=auth(admin))
    assert renamed.status_code == 200 and renamed.json()["data"]["name"] == "Medical Officer (MO)"
    assert (await async_client.patch(f"/api/v1/roles/{admin_role['id']}", json={"is_active": False},
                                     headers=auth(admin))).status_code == 400

    fac = await async_client.patch(f"/api/v1/facilities/{ctx['facility'].id}",
                                   json={"name": "Test PHC Kovalam (Upgraded)", "latitude": 12.79},
                                   headers=auth(admin))
    assert fac.status_code == 200 and fac.json()["data"]["name"] == "Test PHC Kovalam (Upgraded)"

    doctor_id = ctx["doctor_user"].id
    assert (await async_client.get("/api/v1/prescriptions", headers=doctor)).status_code == 200
    revoke = await async_client.delete(f"/api/v1/users/{doctor_id}/roles/{doctor_role['id']}", headers=auth(admin))
    assert revoke.status_code == 204
    assert (await async_client.get("/api/v1/prescriptions", headers=doctor)).status_code == 403
    assert (await async_client.delete(f"/api/v1/users/{doctor_id}/roles/{doctor_role['id']}",
                                      headers=auth(admin))).status_code == 404
    admin_id = ctx["admin_user"].id
    assert (await async_client.delete(f"/api/v1/users/{admin_id}/roles/{admin_role['id']}",
                                      headers=auth(admin))).status_code == 400


@pytest.mark.asyncio
async def test_list_endpoints_scope_and_inventory_aliases(async_client: AsyncClient, ctx: dict):
    admin, fac, other, med = ctx["admin_token"], ctx["facility"], ctx["other_facility"], ctx["med"]
    doctor = auth(ctx["doctor_token"])

    rx = await async_client.get("/api/v1/prescriptions?page_size=5", headers=doctor)
    assert rx.status_code == 200 and rx.json()["pagination"]["page_size"] == 5
    assert (await async_client.get(f"/api/v1/prescriptions?facility_id={other.id}", headers=doctor)).status_code == 403
    labs = await async_client.get("/api/v1/labs/orders?status=ORDERED", headers=doctor)
    assert labs.status_code == 200 and labs.json()["data"] == []
    assert (await async_client.get(f"/api/v1/labs/orders?facility_id={other.id}", headers=doctor)).status_code == 403

    sup = await async_client.post("/api/v1/suppliers", json={"name": "Batch Supplier", "code": "SUP-BATCH"},
                                  headers=auth(admin))
    batch = await receive(async_client, admin, fac.id, med.id, qty=80, lot="OXY-A", days=60,
                          supplier_id=sup.json()["data"]["id"], unit_cost="42.50")
    assert batch["supplier_name"] == "Batch Supplier"
    await receive(async_client, admin, fac.id, med.id, qty=20, lot="OXY-B", days=400)

    expiring = await async_client.get("/api/v1/inventory/batches/expiring?days=90", headers=auth(admin))
    assert [b["batch_number"] for b in expiring.json()["data"]] == ["OXY-A"]

    wrong_type = await async_client.post("/api/v1/inventory/movements", json={
        "batch_id": batch["id"], "quantity": -5, "movement_type": "ADJUSTMENT", "notes": "count fix",
    }, headers=auth(admin))
    assert wrong_type.status_code == 400
    damage = await async_client.post("/api/v1/inventory/movements", json={
        "batch_id": batch["id"], "quantity": -5, "movement_type": "DAMAGE", "notes": "Vials broken in transit",
    }, headers=auth(admin))
    assert damage.status_code == 201, damage.text
    adjust = await async_client.post("/api/v1/inventory/adjustments", json={
        "batch_id": batch["id"], "quantity": -1, "movement_type": "ADJUSTMENT", "notes": "Physical count",
    }, headers=auth(admin))
    assert adjust.status_code == 200, adjust.text
    assert adjust.json()["data"]["balance_after"] == 94

    tr = await async_client.post("/api/v1/inventory/transfers", json={
        "source_facility_id": str(fac.id), "destination_facility_id": str(other.id), "medication_id": str(med.id),
        "requested_quantity": 10, "urgency": "EMERGENCY_SHORTAGE",
    }, headers=auth(admin))
    assert tr.status_code == 201, tr.text
    assert tr.json()["data"]["urgency"] == "EMERGENCY_SHORTAGE"
    appr = await async_client.post(f"/api/v1/inventory/transfers/{tr.json()['data']['id']}/approve", json={},
                                   headers=auth(admin))
    assert appr.status_code == 200 and appr.json()["data"]["status"] == "APPROVED"
    listed = await async_client.get("/api/v1/inventory/transfers", headers=auth(admin))
    assert listed.status_code == 200 and len(listed.json()["data"]) == 1


@pytest.mark.asyncio
async def test_district_scope_limits_supply_dashboard_and_alerts(
    async_client: AsyncClient, db_session: AsyncSession, ctx: dict
):
    from app.core.permissions import SystemPermissions as P
    from app.models.identity import Permission, RolePermission

    fac, other = ctx["facility"], ctx["other_facility"]
    same_district = Facility(id=uuid.uuid4(), organization_id=ctx["org"].id, name="Test SC Thiruporur",
                             code="TEST-SC-003", facility_type=FacilityType.PHC, state="  tamil nadu ",
                             district="CHENGALPATTU", is_active=True)
    role = Role(id=uuid.uuid4(), name="District Supply Officer", code="DSO", is_system=False, is_active=True)
    officer = User(id=uuid.uuid4(), email="dso@test.gov.in", hashed_password=get_password_hash("DsoPass123!"),
                   full_name="DSO", organization_id=ctx["org"].id, facility_id=fac.id, is_active=True,
                   is_verified=True)
    db_session.add_all([same_district, role, officer])
    await db_session.flush()
    for code in (P.DASHBOARDS_SUPPLY_VIEW, P.ALERTS_READ, P.SHIPMENTS_READ):
        perm = (await db_session.execute(select(Permission).where(Permission.code == code))).scalar_one()
        db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db_session.add(UserRole(user_id=officer.id, role_id=role.id, organization_id=ctx["org"].id,
                            facility_id=fac.id, scope_level=ScopeLevel.DISTRICT))
    await db_session.commit()
    token = auth(create_access_token(officer.id))

    # Alert at a facility in another district must stay invisible
    admin = ctx["admin_token"]
    rep = await async_client.post("/api/v1/shortages", json={
        "facility_id": str(other.id), "medication_id": str(ctx["med"].id), "severity": "HIGH",
        "description": "Stockout in Madurai",
    }, headers=auth(admin))
    await async_client.post(f"/api/v1/shortages/{rep.json()['data']['id']}/escalate",
                            json={"level": "DISTRICT", "notes": "Needs district help"}, headers=auth(admin))
    assert (await async_client.get("/api/v1/alerts?state=all", headers=auth(admin))).json()["pagination"]["total"] == 1
    assert (await async_client.get("/api/v1/alerts?state=all", headers=token)).json()["pagination"]["total"] == 0

    dash = await async_client.get("/api/v1/dashboards/supply-chain", headers=token)
    assert dash.status_code == 200, dash.text
    body = dash.json()["data"]
    assert body["scope"] == "DISTRICT"
    assert {f["facility_id"] for f in body["facilities"]} == {str(fac.id), str(same_district.id)}
    assert body["open_shortages_by_severity"] == {}
