"""Idempotent India-wide DEMO seed: PHC/CHC network, beds, staff attendance, medicine stock and dispensing history.

All data is SYNTHETIC and labelled: facility codes start with "IN-", staff e-mails end in
@india-demo.smarthealth.local, medicines use "INDIA-" codes, stock movements carry reference_id
"SEED-INDIA". Some facilities deliberately have stale or missing bed/attendance data so the
freshness flags can be demonstrated. Staff accounts get an unusable random password (no logins).

Usage:  python scripts/seed_india_demo.py            (ENVIRONMENT must be development or demo)
Tests call seed_india_demo(session, ...) directly against the sqlite test database.
"""
import asyncio
import os
import random
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.beds import BedCensusLog, BedInventory, WardType
from app.models.facility import Facility, FacilityType
from app.models.healthcare import AttendanceStatus, Medication, StaffAttendance
from app.models.identity import User
from app.models.organization import Organization, OrganizationType
from app.models.pharmacy import (
    BatchStatus, InventoryBatch, InventoryItem, StockMovement, StockMovementType,
)

STAFF_DOMAIN = "india-demo.smarthealth.local"
SEED_REF = "SEED-INDIA"

# state -> (code, [(district, code, lat, lon, [CHC, PHC, PHC])])
NETWORK = {
    "Tamil Nadu": ("TN", [
        ("Chengalpattu", "CGL", 12.69, 79.98, ["Madurantakam", "Thirukalukundram", "Guduvanchery"]),
        ("Coimbatore", "CBE", 11.00, 76.96, ["Pollachi", "Annur", "Sulur"]),
        ("Madurai", "MDU", 9.93, 78.12, ["Melur", "Alanganallur", "Thirumangalam"]),
    ]),
    "Kerala": ("KL", [
        ("Thiruvananthapuram", "TVM", 8.52, 76.94, ["Nedumangad", "Vellanad", "Kattakada"]),
        ("Ernakulam", "EKM", 9.98, 76.28, ["Perumbavoor", "Kalady", "Vazhakulam"]),
        ("Kozhikode", "KKD", 11.25, 75.78, ["Koyilandy", "Balussery", "Thamarassery"]),
    ]),
    "Karnataka": ("KA", [
        ("Mysuru", "MYS", 12.30, 76.64, ["Hunsur", "Bilikere", "Nanjangud"]),
        ("Belagavi", "BGM", 15.85, 74.50, ["Gokak", "Khanapur", "Saundatti"]),
        ("Dharwad", "DWD", 15.46, 75.01, ["Kundgol", "Navalgund", "Annigeri"]),
    ]),
    "Maharashtra": ("MH", [
        ("Pune", "PNQ", 18.52, 73.86, ["Junnar", "Otur", "Bhor"]),
        ("Nashik", "NSK", 20.00, 73.79, ["Igatpuri", "Dindori", "Peth"]),
        ("Nagpur", "NGP", 21.15, 79.09, ["Kamptee", "Hingna", "Katol"]),
    ]),
    "Uttar Pradesh": ("UP", [
        ("Lucknow", "LKO", 26.85, 80.95, ["Malihabad", "Bakshi Ka Talab", "Mohanlalganj"]),
        ("Varanasi", "VNS", 25.32, 82.97, ["Pindra", "Cholapur", "Arajiline"]),
        ("Gorakhpur", "GKP", 26.76, 83.37, ["Campierganj", "Sahjanwa", "Pipraich"]),
    ]),
    "Bihar": ("BR", [
        ("Patna", "PAT", 25.59, 85.14, ["Masaurhi", "Paliganj", "Phulwari Sharif"]),
        ("Gaya", "GAY", 24.79, 85.00, ["Sherghati", "Bodh Gaya", "Tekari"]),
        ("Muzaffarpur", "MZF", 26.12, 85.39, ["Motipur", "Kanti", "Sakra"]),
    ]),
    "Rajasthan": ("RJ", [
        ("Jaipur", "JAI", 26.91, 75.79, ["Chomu", "Sanganer", "Amer"]),
        ("Jodhpur", "JDH", 26.24, 73.02, ["Bilara", "Osian", "Mandor"]),
        ("Udaipur", "UDR", 24.58, 73.68, ["Kotra", "Jhadol", "Girwa"]),
    ]),
    "West Bengal": ("WB", [
        ("North 24 Parganas", "N24", 22.72, 88.48, ["Basirhat", "Habra", "Bongaon"]),
        ("Darjeeling", "DJL", 27.04, 88.26, ["Kurseong", "Mirik", "Matigara"]),
        ("Murshidabad", "MSD", 24.18, 88.27, ["Lalgola", "Jangipur", "Domkal"]),
    ]),
}

# (code, generic name, strength, form, unit, base daily dispense at a PHC, category)
MEDICINES = [
    ("PCM-500", "Paracetamol", "500 mg", "Tablet", "Tablet", 60, "Analgesic"),
    ("ORS-21", "Oral Rehydration Salts", "20.5 g", "Sachet", "Sachet", 25, "Rehydration"),
    ("AMX-500", "Amoxicillin", "500 mg", "Capsule", "Capsule", 30, "Antibiotic"),
    ("MET-500", "Metformin", "500 mg", "Tablet", "Tablet", 45, "Antidiabetic"),
    ("AML-5", "Amlodipine", "5 mg", "Tablet", "Tablet", 40, "Antihypertensive"),
    ("ATN-50", "Atenolol", "50 mg", "Tablet", "Tablet", 20, "Antihypertensive"),
    ("AZI-500", "Azithromycin", "500 mg", "Tablet", "Tablet", 15, "Antibiotic"),
    ("CTZ-10", "Cetirizine", "10 mg", "Tablet", "Tablet", 25, "Antihistamine"),
    ("OMP-20", "Omeprazole", "20 mg", "Capsule", "Capsule", 30, "Antacid"),
    ("IBU-400", "Ibuprofen", "400 mg", "Tablet", "Tablet", 30, "Analgesic"),
    ("FE-FA", "Iron and Folic Acid", "100 mg/500 mcg", "Tablet", "Tablet", 50, "Supplement"),
    ("ZNC-20", "Zinc Sulphate", "20 mg", "Dispersible tablet", "Tablet", 12, "Supplement"),
    ("SAL-100", "Salbutamol", "100 mcg", "Inhaler", "Inhaler", 6, "Respiratory"),
    ("CPM-500", "Ciprofloxacin", "500 mg", "Tablet", "Tablet", 14, "Antibiotic"),
    ("ALB-400", "Albendazole", "400 mg", "Tablet", "Tablet", 10, "Anthelmintic"),
]

PHC_ROLES = ["Medical Officer", "Staff Nurse", "Pharmacist", "Lab Technician"]
CHC_ROLES = PHC_ROLES + ["Staff Nurse", "Staff Nurse", "ANM", "Medical Officer"]


def _ward_plan(ftype: FacilityType, rng: random.Random) -> Dict[WardType, int]:
    if ftype == FacilityType.CHC:
        return {WardType.GENERAL: rng.randint(20, 30), WardType.MATERNITY: rng.randint(6, 10),
                WardType.PAEDIATRIC: rng.randint(6, 10), WardType.ISOLATION: rng.randint(2, 4),
                WardType.ICU: rng.randint(2, 4)}
    return {WardType.GENERAL: rng.randint(6, 12), WardType.MATERNITY: rng.randint(2, 4),
            WardType.ISOLATION: rng.randint(1, 2)}


async def _get_or_create_org(session: AsyncSession, state: str, code: str) -> Organization:
    org_code = f"IN-{code}-DOH"
    org = (await session.execute(select(Organization).where(Organization.code == org_code))).scalar_one_or_none()
    if org is None:
        org = Organization(name=f"[DEMO] {state} Department of Health", code=org_code,
                           org_type=OrganizationType.STATE_HEALTH_DEPT, is_active=True)
        session.add(org)
        await session.flush()
    return org


async def seed_india_demo(
    session: AsyncSession,
    states: Optional[Iterable[str]] = None,
    history_days: int = 30,
    now: Optional[datetime] = None,
    seed: int = 20260930,
) -> Dict[str, int]:
    """Seed (or top up) the demo network. Safe to re-run; returns counts of rows created."""
    now = now or datetime.now(timezone.utc)
    wanted = set(states) if states else set(NETWORK)
    rng = random.Random(seed)
    counts = {"facilities": 0, "staff": 0, "bed_rows": 0, "attendance": 0, "inventory_items": 0, "dispense_movements": 0}
    unusable_hash = get_password_hash(secrets.token_urlsafe(32))

    meds: Dict[str, Medication] = {}
    for code, name, strength, form, unit, _base, category in MEDICINES:
        full = f"INDIA-{code}"
        m = (await session.execute(select(Medication).where(Medication.code == full))).scalar_one_or_none()
        if m is None:
            m = Medication(code=full, generic_name=name, brand_name=f"[DEMO] {name}", strength=strength,
                           dosage_form=form, route="Oral", unit=unit, category=category, is_essential=True, is_active=True)
            session.add(m)
            await session.flush()
        meds[code] = m

    fac_index = 0
    for state, (scode, districts) in NETWORK.items():
        if state not in wanted:
            continue
        org = await _get_or_create_org(session, state, scode)
        for district, dcode, lat, lon, names in districts:
            for i, name in enumerate(names):
                fac_index += 1
                ftype = FacilityType.CHC if i == 0 else FacilityType.PHC
                fcode = f"IN-{scode}-{dcode}-{i + 1:02d}"
                fac = (await session.execute(select(Facility).where(Facility.code == fcode))).scalar_one_or_none()
                if fac is None:
                    fac = Facility(
                        organization_id=org.id, code=fcode, name=f"{name} {'CHC' if i == 0 else 'PHC'}",
                        facility_type=ftype, state=state, district=district,
                        address=f"{name}, {district}, {state}",
                        latitude=round(lat + rng.uniform(-0.25, 0.25), 6),
                        longitude=round(lon + rng.uniform(-0.25, 0.25), 6), is_active=True)
                    session.add(fac)
                    await session.flush()
                    counts["facilities"] += 1
                await _seed_staff_and_attendance(session, fac, fac_index, org, unusable_hash, now, rng, counts)
                await _seed_beds(session, fac, fac_index, now, rng, counts)
                await _seed_stock(session, fac, meds, history_days, now, rng, counts)
        await session.flush()
    await session.commit()
    return counts


async def _seed_staff_and_attendance(session, fac, idx, org, pw_hash, now, rng, counts) -> None:
    roles = CHC_ROLES if fac.facility_type == FacilityType.CHC else PHC_ROLES
    staff: List[User] = []
    for n, role in enumerate(roles, start=1):
        email = f"{fac.code.lower()}.staff{n}@{STAFF_DOMAIN}"
        u = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if u is None:
            u = User(email=email, hashed_password=pw_hash, full_name=f"[DEMO] {role} {fac.name} #{n}",
                     organization_id=org.id, facility_id=fac.id, is_active=True, is_verified=True)
            session.add(u)
            counts["staff"] += 1
        staff.append(u)
    await session.flush()

    # attendance profile: every 9th facility never reports, every 9th+1 last reported 3 days ago
    if idx % 9 == 0:
        return
    day_offset = 3 if idx % 9 == 1 else 0
    att_date = (now - timedelta(days=day_offset)).date()
    existing = set((await session.execute(
        select(StaffAttendance.user_id).where(StaffAttendance.facility_id == fac.id,
                                              StaffAttendance.attendance_date == att_date))).scalars().all())
    for u in staff:
        if u.id in existing:
            continue
        r = rng.random()
        status = (AttendanceStatus.PRESENT if r < 0.78 else AttendanceStatus.HALF_DAY if r < 0.86
                  else AttendanceStatus.ON_DUTY_CAMP if r < 0.90 else AttendanceStatus.ON_LEAVE)
        check_in = now - timedelta(days=day_offset, hours=rng.randint(1, 6), minutes=rng.randint(0, 59))
        session.add(StaffAttendance(user_id=u.id, facility_id=fac.id, attendance_date=att_date, check_in_time=check_in,
                                    status=status, shift="GENERAL", notes="Synthetic demo attendance"))
        counts["attendance"] += 1


async def _seed_beds(session, fac, idx, now, rng, counts) -> None:
    if idx % 11 == 0:
        return  # never reported: stays NO_DATA
    exists = (await session.execute(select(BedInventory.id).where(BedInventory.facility_id == fac.id).limit(1))).first()
    if exists:
        return
    stale = idx % 7 == 3
    updated = now - (timedelta(days=2, hours=rng.randint(0, 5)) if stale else timedelta(minutes=rng.randint(5, 600)))
    for ward, total in _ward_plan(fac.facility_type, rng).items():
        occupied = min(total, int(total * rng.uniform(0.2, 1.0)))
        session.add(BedInventory(facility_id=fac.id, ward_type=ward, total_beds=total, occupied_beds=occupied,
                                 created_at=updated, updated_at=updated))
        session.add(BedCensusLog(facility_id=fac.id, ward_type=ward, total_beds=total, occupied_beds=occupied,
                                 note="Synthetic demo census", recorded_at=updated))
        counts["bed_rows"] += 1


async def _seed_stock(session, fac, meds, history_days, now, rng, counts) -> None:
    actor = (await session.execute(select(User.id).where(User.facility_id == fac.id).order_by(User.email).limit(1))).scalar_one()
    scale = 2.0 if fac.facility_type == FacilityType.CHC else 1.0
    for code, med in meds.items():
        base = next(m[5] for m in MEDICINES if m[0] == code)
        item = (await session.execute(select(InventoryItem).where(
            InventoryItem.facility_id == fac.id, InventoryItem.medication_id == med.id))).scalar_one_or_none()
        if item is not None:
            continue
        daily = [max(0, int(base * scale * rng.uniform(0.6, 1.4))) for _ in range(history_days)]
        dispensed = sum(daily)
        # remaining stock ranges from stock-out to ~6 weeks of cover so alerts and forecasts have variety
        cover_days = rng.choice([0, 2, 5, 12, 25, 40])
        on_hand = int(base * scale * cover_days)
        reorder = max(int(base * scale * 10), 10)
        item = InventoryItem(facility_id=fac.id, medication_id=med.id, quantity_on_hand=on_hand, quantity_reserved=0,
                             reorder_level=reorder, critical_level=max(int(reorder / 3), 1),
                             minimum_stock_level=max(int(reorder / 2), 1),
                             maximum_stock_level=max(int(base * scale * 60), reorder), unit_cost=1)
        session.add(item)
        await session.flush()
        counts["inventory_items"] += 1
        batch = None
        if on_hand > 0:
            batch = InventoryBatch(inventory_item_id=item.id, batch_number=f"IN-{fac.code[-9:]}-{code}",
                                   manufacture_date=(now - timedelta(days=150)).date(),
                                   expiry_date=(now + timedelta(days=rng.randint(60, 540))).date(),
                                   initial_quantity=on_hand, current_quantity=on_hand, status=BatchStatus.AVAILABLE,
                                   supplier_name="[DEMO] State Medical Services Corporation")
            session.add(batch)
            await session.flush()
        # ledger: one opening receipt, then one dispense row per day; balances reconcile to on_hand
        balance = on_hand + dispensed
        start = now - timedelta(days=history_days)
        session.add(StockMovement(facility_id=fac.id, inventory_item_id=item.id, movement_type=StockMovementType.RECEIPT,
                                  quantity=balance, balance_after=balance, reference_id=SEED_REF,
                                  notes="Synthetic opening stock", actor_id=actor, created_at=start))
        for d, qty in enumerate(daily):
            if qty == 0:
                continue
            balance -= qty
            session.add(StockMovement(
                facility_id=fac.id, inventory_item_id=item.id, movement_type=StockMovementType.DISPENSE,
                quantity=-qty, balance_after=balance, reference_id=SEED_REF, notes="Synthetic daily dispensing",
                actor_id=actor, created_at=start + timedelta(days=d + 1) - timedelta(hours=1)))
            counts["dispense_movements"] += 1
    await session.flush()


async def main() -> None:
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal

    if settings.ENVIRONMENT not in ("development", "demo"):
        raise SystemExit(f"Refusing to seed demo data in ENVIRONMENT={settings.ENVIRONMENT!r}.")
    async with AsyncSessionLocal() as session:
        counts = await seed_india_demo(session)
    print("India demo seed complete:", counts)


if __name__ == "__main__":
    asyncio.run(main())
