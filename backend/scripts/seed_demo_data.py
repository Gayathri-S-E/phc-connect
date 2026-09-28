"""Seed clearly-labelled DEMO accounts and stock so every role can be exercised end to end.

Refuses to run unless ENVIRONMENT is 'development' or 'demo' (main.md §2.7: synthetic
data only in labelled demo/testing environments). All demo facilities are prefixed
"[DEMO]" and all demo accounts use the @demo.smarthealth.local domain.

Usage:  python scripts/seed_demo_data.py          (runs seed_initial_data first)
        DEMO_PASSWORD=... python scripts/seed_demo_data.py
"""
import asyncio
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.role_catalog import ROLES_CONFIG
from app.core.security import get_password_hash
from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication, Patient
from app.models.identity import Role, ScopeLevel, User, UserRole
from app.models.organization import Organization
from app.models.pharmacy import BatchStatus, InventoryBatch, InventoryItem
from scripts.seed_initial_data import seed_data

DEMO_DOMAIN = "demo.smarthealth.com"

DEMO_FACILITIES = [
    ("DEMO-DWH-CGL", "[DEMO] District Drug Warehouse Chengalpattu", FacilityType.DISTRICT_WAREHOUSE, "Chengalpattu"),
    ("DEMO-SWH-TN", "[DEMO] State Central Medical Warehouse", FacilityType.CENTRAL_WAREHOUSE, "Chennai"),
]

# role code -> facility code the demo user is attached to
ROLE_HOME = {
    "PATIENT": "PHC-KOV-001", "DOCTOR": "PHC-KOV-001", "NURSE": "PHC-KOV-001", "LAB_TECHNICIAN": "PHC-KOV-001",
    "PHC_IN_CHARGE": "PHC-KOV-001", "PHARMACIST": "PHC-KOV-001", "INVENTORY_OFFICER": "DEMO-DWH-CGL",
    "DISTRICT_HEALTH_OFFICER": "DEMO-DWH-CGL", "DISTRICT_SUPPLY_OFFICER": "DEMO-DWH-CGL",
    "DISTRICT_EMERGENCY_COORDINATOR": "DEMO-DWH-CGL", "STATE_HEALTH_ADMIN": "DEMO-SWH-TN",
    "STATE_SUPPLY_MANAGER": "DEMO-SWH-TN", "STATE_PUBLIC_HEALTH_ANALYST": "DEMO-SWH-TN",
    "NATIONAL_HEALTH_AUTHORITY": "DEMO-SWH-TN", "SUPER_ADMIN": "DEMO-SWH-TN", "SYSTEM_ADMIN": "DEMO-SWH-TN",
    "AUDITOR": "DEMO-SWH-TN",
}

DEMO_MEDICINES = [
    ("DEMO-PCM-500", "Paracetamol", "500 mg", "Tablet", "Tablet"),
    ("DEMO-AMX-500", "Amoxicillin", "500 mg", "Capsule", "Capsule"),
    ("DEMO-MET-500", "Metformin", "500 mg", "Tablet", "Tablet"),
    ("DEMO-ORS-21", "Oral Rehydration Salts", "20.5 g", "Sachet", "Sachet"),
    ("DEMO-AML-5", "Amlodipine", "5 mg", "Tablet", "Tablet"),
]

# (facility code, medicine code) -> quantity; PHC Kovalam deliberately short on two items.
DEMO_STOCK = {
    ("PHC-KOV-001", "DEMO-PCM-500"): 40, ("PHC-KOV-001", "DEMO-AMX-500"): 0, ("PHC-KOV-001", "DEMO-MET-500"): 300,
    ("PHC-KOV-001", "DEMO-ORS-21"): 25, ("PHC-KEL-002", "DEMO-AMX-500"): 400, ("PHC-KEL-002", "DEMO-ORS-21"): 250,
    ("DEMO-DWH-CGL", "DEMO-PCM-500"): 2000, ("DEMO-DWH-CGL", "DEMO-AMX-500"): 150, ("DEMO-DWH-CGL", "DEMO-MET-500"): 1500,
    ("DEMO-SWH-TN", "DEMO-PCM-500"): 20000, ("DEMO-SWH-TN", "DEMO-AMX-500"): 12000, ("DEMO-SWH-TN", "DEMO-ORS-21"): 8000,
    ("DEMO-SWH-TN", "DEMO-AML-5"): 5000,
}


async def seed_demo() -> None:
    if settings.ENVIRONMENT not in ("development", "demo"):
        raise SystemExit(f"Refusing to seed demo data in ENVIRONMENT={settings.ENVIRONMENT!r}.")
    await seed_data()
    password = os.getenv("DEMO_PASSWORD", "Demo@Health2026")
    async with AsyncSessionLocal() as session:
        org = (await session.execute(select(Organization).where(Organization.code == "TN-DPH-01"))).scalar_one()
        facilities = {}
        for code, name, ftype, district in DEMO_FACILITIES:
            f = (await session.execute(select(Facility).where(Facility.code == code))).scalar_one_or_none()
            if not f:
                f = Facility(organization_id=org.id, code=code, name=name, facility_type=ftype, state="Tamil Nadu",
                             district=district, address="Demo address", is_active=True)
                session.add(f)
                await session.flush()
        for f in (await session.execute(select(Facility))).scalars().all():
            facilities[f.code] = f

        meds = {}
        for code, generic, strength, form, unit in DEMO_MEDICINES:
            m = (await session.execute(select(Medication).where(Medication.code == code))).scalar_one_or_none()
            if not m:
                m = Medication(code=code, generic_name=generic, brand_name=f"[DEMO] {generic}", strength=strength,
                               dosage_form=form, route="Oral", unit=unit, is_essential=True, is_active=True)
                session.add(m)
                await session.flush()
            meds[code] = m

        for (fcode, mcode), qty in DEMO_STOCK.items():
            f, m = facilities.get(fcode), meds[mcode]
            if not f:
                continue
            item = (await session.execute(select(InventoryItem).where(
                InventoryItem.facility_id == f.id, InventoryItem.medication_id == m.id))).scalar_one_or_none()
            if item:
                continue
            item = InventoryItem(facility_id=f.id, medication_id=m.id, quantity_on_hand=qty, quantity_reserved=0,
                                 reorder_level=100 if "WH" not in fcode else 1000, critical_level=20)
            session.add(item)
            await session.flush()
            if qty:
                session.add(InventoryBatch(inventory_item_id=item.id, batch_number=f"DEMO-{mcode[-6:]}-{fcode[-3:]}",
                                           manufacture_date=date.today() - timedelta(days=120),
                                           expiry_date=date.today() + timedelta(days=45 if mcode == "DEMO-ORS-21" else 400),
                                           initial_quantity=qty, current_quantity=qty, status=BatchStatus.AVAILABLE,
                                           supplier_name="[DEMO] Supplier"))

        roles = {r.code: r for r in (await session.execute(select(Role))).scalars().all()}
        created = []
        for conf in ROLES_CONFIG:
            code = conf["code"]
            email = f"{code.lower().replace('_', '.')}@{DEMO_DOMAIN}"
            if (await session.execute(select(User).where(User.email == email))).scalar_one_or_none():
                continue
            home = facilities[ROLE_HOME[code]]
            user = User(email=email, hashed_password=get_password_hash(password), full_name=f"[DEMO] {conf['name']}",
                        organization_id=org.id, facility_id=home.id, is_active=True, is_verified=True)
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=roles[code].id, organization_id=org.id, facility_id=home.id,
                                 scope_level=ScopeLevel(conf["default_scope"])))
            if code == "PATIENT":
                session.add(Patient(user_id=user.id, primary_facility_id=home.id, patient_identifier="DEMO-PAT-0001",
                                    first_name="Demo", last_name="Patient", date_of_birth=date(1985, 6, 15),
                                    gender="FEMALE", phone_number="+910000000001"))
            created.append(email)
        await session.commit()
    print("Demo seed complete. Password for all demo accounts:", "(from DEMO_PASSWORD)" if os.getenv("DEMO_PASSWORD") else password)
    for email in created:
        print("  created", email)


if __name__ == "__main__":
    asyncio.run(seed_demo())
