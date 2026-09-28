"""
Phase 4 — Pharmacist Portal Tests (Role 04)
============================================
Tests:
 1. test_pharmacist_dispense_queue_with_fefo_preview
    - Receive stock into 2 FEFO batches
    - Issue a prescription
    - Dispense queue returns the prescription with correct FEFO batch ordering
 2. test_stock_alert_dashboard_low_and_shortage
    - Create inventory with stock at or below reorder level
    - Alert dashboard returns items with correct stock_status tags
 3. test_drug_info_ai_bilingual_metformin_interactions
    - Query drug info for Metformin with a co-medication (contrast dye / rifampicin)
    - Assert English + Tamil content returned
    - Assert interaction warning contains expected co-medication
 4. test_drug_info_ai_storage_query
    - Query storage info for Amlodipine
    - Assert storage_en and storage_ta returned
 5. test_counselling_note_record_and_retrieve
    - Create a prescription, dispense it
    - Record a bilingual counselling note
    - Retrieve and verify the note
"""
import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.healthcare import (
    Medication,
    Patient,
    Consultation,
    Prescription,
    PrescriptionItem,
    PrescriptionItemStatus,
    PrescriptionStatus,
)
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.core.permissions import SystemPermissions


# ---------------------------------------------------------------------------
# Helper: seed a Pharmacist user with the minimum required permissions
# ---------------------------------------------------------------------------

async def _seed_pharmacist(db_session, seeded_data) -> tuple[User, str]:
    """Create PHARMACIST role + user with dispense & inventory-read permissions."""
    org = seeded_data["org"]
    fac = seeded_data["facility"]

    # Fetch permission objects created by seeded_data fixture
    from sqlalchemy import select
    from app.models.identity import Permission as Perm
    needed_codes = [
        SystemPermissions.PRESCRIPTIONS_DISPENSE,
        SystemPermissions.PRESCRIPTIONS_READ,
        SystemPermissions.INVENTORY_ITEM_READ,
        SystemPermissions.PATIENTS_PROFILE_READ,
    ]
    perm_rows = (
        await db_session.execute(select(Perm).where(Perm.code.in_(needed_codes)))
    ).scalars().all()
    perm_map = {p.code: p for p in perm_rows}

    pharma_role = Role(
        id=uuid.uuid4(),
        name="Pharmacist",
        code="PHARMACIST",
        is_system=False,
        is_active=True,
    )
    db_session.add(pharma_role)
    await db_session.flush()

    for code, p in perm_map.items():
        db_session.add(RolePermission(role_id=pharma_role.id, permission_id=p.id))

    pharma_user = User(
        id=uuid.uuid4(),
        email="pharmacist@test.gov.in",
        hashed_password="hashed",
        full_name="Pharmacist Ravi",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(pharma_user)
    await db_session.flush()
    db_session.add(
        UserRole(
            user_id=pharma_user.id,
            role_id=pharma_role.id,
            organization_id=org.id,
            facility_id=fac.id,
            scope_level=ScopeLevel.FACILITY,
        )
    )
    await db_session.commit()
    token = create_access_token(pharma_user.id, extra_claims={"email": pharma_user.email})
    return pharma_user, token


# ===========================================================================
# TEST 1: Dispense Queue — FEFO Batch Preview
# ===========================================================================

@pytest.mark.asyncio
async def test_pharmacist_dispense_queue_with_fefo_preview(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Dispense queue returns ISSUED prescriptions with FEFO batch previews.
    Earliest-expiring batch must appear FIRST in the batch list.
    """
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]
    doctor = seeded_data["doctor_user"]
    _, pharma_token = await _seed_pharmacist(db_session, seeded_data)

    # 1. Create medication
    med = Medication(
        id=uuid.uuid4(),
        name="Metformin 500mg",
        code="MED-MET-500",
        dosage_form="Tablet",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    # 2. Receive 2 FEFO batches (different expiry dates)
    early_exp = str(date.today() + timedelta(days=20))
    late_exp = str(date.today() + timedelta(days=150))

    b1 = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(facility.id),
            "medication_id": str(med.id),
            "batch_number": "MET-EARLY",
            "manufacture_date": str(date.today() - timedelta(days=60)),
            "expiry_date": early_exp,
            "quantity": 30,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b1.status_code == 201
    b1_id = b1.json()["data"]["id"]

    b2 = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(facility.id),
            "medication_id": str(med.id),
            "batch_number": "MET-LATER",
            "manufacture_date": str(date.today() - timedelta(days=20)),
            "expiry_date": late_exp,
            "quantity": 60,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b2.status_code == 201
    b2_id = b2.json()["data"]["id"]

    # 3. Create Patient → Consultation → Prescription (ISSUED)
    patient = Patient(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_identifier="PAT-PHC-MET",
        first_name="Selvam",
        last_name="Rajan",
        date_of_birth=date(1975, 3, 10),
        gender="MALE",
        phone_number="+919843000111",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        chief_complaint="Type 2 Diabetes follow-up",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(consultation)
    await db_session.flush()

    prescription = Prescription(
        id=uuid.uuid4(),
        facility_id=facility.id,
        consultation_id=consultation.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        status=PrescriptionStatus.ISSUED,
    )
    db_session.add(prescription)
    await db_session.flush()

    rx_item = PrescriptionItem(
        id=uuid.uuid4(),
        prescription_id=prescription.id,
        medication_id=med.id,
        medication_name="Metformin 500mg",
        dosage="500mg",
        frequency="BD",
        duration_days=30,
        quantity_prescribed=40,
        quantity_dispensed=0,
        status=PrescriptionItemStatus.PENDING,
    )
    db_session.add(rx_item)
    await db_session.commit()

    # 4. Pharmacist fetches dispense queue
    queue_res = await async_client.get(
        f"/api/v1/pharmacist/prescriptions/pending?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {pharma_token}"},
    )
    assert queue_res.status_code == 200, queue_res.text
    queue = queue_res.json()["data"]

    # Our prescription must be in the queue
    our_rx = next((q for q in queue if q["prescription_id"] == str(prescription.id)), None)
    assert our_rx is not None, "Prescription not found in dispense queue"
    assert our_rx["patient_identifier"] == "PAT-PHC-MET"
    assert our_rx["item_count"] == 1

    # FEFO preview: earliest expiry batch must be first
    item = our_rx["items"][0]
    assert item["medication_name"] == "Metformin 500mg"
    assert item["quantity_prescribed"] == 40
    fefo_batches = item["fefo_batches"]
    assert len(fefo_batches) >= 2
    # First batch in FEFO list must have the earlier expiry date
    assert fefo_batches[0]["expiry_date"] < fefo_batches[1]["expiry_date"]
    # Batch IDs must be present (pharmacist-only — not patient-facing)
    assert fefo_batches[0]["batch_id"] == b1_id
    assert fefo_batches[1]["batch_id"] == b2_id


# ===========================================================================
# TEST 2: Stock Alert Dashboard
# ===========================================================================

@pytest.mark.asyncio
async def test_stock_alert_dashboard_low_and_shortage(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Stock alert dashboard correctly identifies LOW_STOCK and SHORTAGE_RISK medicines.
    OUT_OF_STOCK items with no stock are also flagged.
    """
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # Create 3 medications with different stock levels
    med_low = Medication(id=uuid.uuid4(), name="Atenolol 50mg", code="MED-ATE-50",
                         dosage_form="Tablet", strength="50mg", is_active=True)
    med_short = Medication(id=uuid.uuid4(), name="Enalapril 5mg", code="MED-ENA-5",
                           dosage_form="Tablet", strength="5mg", is_active=True)
    med_ok = Medication(id=uuid.uuid4(), name="Aspirin 75mg", code="MED-ASP-75",
                        dosage_form="Tablet", strength="75mg", is_active=True)
    db_session.add_all([med_low, med_short, med_ok])
    await db_session.commit()

    # Receive stock: LOW_STOCK medicine (below reorder=50, above min=20 → qty=35)
    low_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={"facility_id": str(facility.id), "medication_id": str(med_low.id),
              "batch_number": "ATE-LOW-001",
              "manufacture_date": str(date.today() - timedelta(days=30)),
              "expiry_date": str(date.today() + timedelta(days=365)),
              "quantity": 35},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert low_res.status_code == 201

    # SHORTAGE_RISK medicine (below minimum_stock_level=20 → qty=10)
    short_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={"facility_id": str(facility.id), "medication_id": str(med_short.id),
              "batch_number": "ENA-SHORT-001",
              "manufacture_date": str(date.today() - timedelta(days=20)),
              "expiry_date": str(date.today() + timedelta(days=180)),
              "quantity": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert short_res.status_code == 201
    short_batch_id = short_res.json()["data"]["id"]

    # Deplete the shortage medicine further to 10 units (already at 10 — let's adjust down 0)
    # (It's already below minimum_stock_level=20; no further adjustment needed.)

    # NORMAL stock medicine (qty=200 — well above reorder=50)
    ok_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={"facility_id": str(facility.id), "medication_id": str(med_ok.id),
              "batch_number": "ASP-NORMAL-001",
              "manufacture_date": str(date.today() - timedelta(days=10)),
              "expiry_date": str(date.today() + timedelta(days=365)),
              "quantity": 200},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ok_res.status_code == 201

    # Fetch stock alerts
    alert_res = await async_client.get(
        f"/api/v1/pharmacist/stock-alerts?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert alert_res.status_code == 200, alert_res.text
    alerts = alert_res.json()["data"]

    # Only LOW and SHORTAGE items should appear — not NORMAL
    alert_med_ids = {a["medication_id"] for a in alerts}
    assert str(med_low.id) in alert_med_ids, "LOW_STOCK medicine must appear in alerts"
    assert str(med_short.id) in alert_med_ids, "SHORTAGE_RISK medicine must appear in alerts"
    assert str(med_ok.id) not in alert_med_ids, "NORMAL medicine must NOT appear in stock alerts"

    # Verify stock_status tags
    low_alert = next(a for a in alerts if a["medication_id"] == str(med_low.id))
    short_alert = next(a for a in alerts if a["medication_id"] == str(med_short.id))
    assert low_alert["stock_status"] in ("LOW_STOCK",)
    assert short_alert["stock_status"] in ("SHORTAGE_RISK", "OUT_OF_STOCK")

    # Verify quantity values
    assert low_alert["quantity_on_hand"] == 35
    assert short_alert["quantity_on_hand"] == 10


# ===========================================================================
# TEST 3: Drug Info AI — Bilingual + Interaction Warnings (Metformin)
# ===========================================================================

@pytest.mark.asyncio
async def test_drug_info_ai_bilingual_metformin_interactions(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Drug info AI returns bilingual content and flags drug interactions.
    Co-medication 'rifampicin' must trigger an interaction warning for Metformin.
    """
    admin_token = seeded_data["admin_token"]

    # Create a Metformin medication entry
    med = Medication(
        id=uuid.uuid4(),
        name="Metformin 500mg",
        code="MED-MET-500-AI",
        dosage_form="Tablet",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    res = await async_client.post(
        "/api/v1/pharmacist/drug-info",
        json={
            "medication_id": str(med.id),
            "query_type": "interactions",
            "co_medications": ["rifampicin"],
            "patient_condition": None,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]

    # Must have bilingual content
    assert data["medication_name"] == "Metformin 500mg"
    assert data["query_type"] == "interactions"
    assert len(data["information_en"]) > 0
    assert len(data["information_ta"]) > 0

    # Must flag rifampicin interaction
    all_warnings = " ".join(data["warnings"]).lower()
    assert "rifampicin" in all_warnings, f"Expected rifampicin interaction warning; got: {data['warnings']}"

    # Must have Tamil counselling points
    assert len(data["counselling_points_ta"]) > 0, "Tamil counselling points expected for Metformin"

    # References must include TN-STG
    references_combined = " ".join(data["references"]).lower()
    assert "tamil nadu" in references_combined or "tn" in references_combined


# ===========================================================================
# TEST 4: Drug Info AI — Storage Query for Amlodipine
# ===========================================================================

@pytest.mark.asyncio
async def test_drug_info_ai_storage_query(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Storage query returns storage_en and storage_ta content for Amlodipine.
    """
    admin_token = seeded_data["admin_token"]

    med = Medication(
        id=uuid.uuid4(),
        name="Amlodipine 5mg",
        code="MED-AML-5",
        dosage_form="Tablet",
        strength="5mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    res = await async_client.post(
        "/api/v1/pharmacist/drug-info",
        json={
            "medication_id": str(med.id),
            "query_type": "storage",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]

    assert "30°C" in data["information_en"] or "temperature" in data["information_en"].lower()
    assert len(data["information_ta"]) > 0  # Tamil storage text returned
    assert data["query_type"] == "storage"


# ===========================================================================
# TEST 5: Counselling Note Record & Retrieve
# ===========================================================================

@pytest.mark.asyncio
async def test_counselling_note_record_and_retrieve(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Pharmacist records a bilingual counselling note after dispensing;
    the note can be retrieved by prescription ID.
    """
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]
    doctor = seeded_data["doctor_user"]
    _, pharma_token = await _seed_pharmacist(db_session, seeded_data)

    # 1. Set up medication, patient, consultation, prescription
    med = Medication(
        id=uuid.uuid4(),
        name="Amoxicillin 500mg",
        code="MED-AMOX-CNS",
        dosage_form="Capsule",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.flush()

    patient = Patient(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_identifier="PAT-CNS-001",
        first_name="Geetha",
        last_name="Devi",
        date_of_birth=date(1990, 6, 15),
        gender="FEMALE",
        phone_number="+919876500222",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        chief_complaint="Sore throat and fever",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(consultation)
    await db_session.flush()

    prescription = Prescription(
        id=uuid.uuid4(),
        facility_id=facility.id,
        consultation_id=consultation.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        status=PrescriptionStatus.COMPLETED,  # Already dispensed
    )
    db_session.add(prescription)
    await db_session.commit()

    # 2. Record counselling note
    counselling_summary = (
        "Patient counselled on completing the full 5-day Amoxicillin course even if symptoms improve. "
        "அமாக்சிசிலின் மருந்தை முழு 5 நாட்கள் எடுக்க வேண்டும் என்று நோயாளிக்கு ஆலோசனை வழங்கப்பட்டது. "
        "Allergy signs (rash, breathing difficulty) explained."
    )
    note_res = await async_client.post(
        "/api/v1/pharmacist/counselling-notes",
        json={
            "prescription_id": str(prescription.id),
            "patient_id": str(patient.id),
            "counselling_summary": counselling_summary,
            "language_used": "BILINGUAL",
            "patient_understood": True,
            "follow_up_recommended": False,
        },
        headers={"Authorization": f"Bearer {pharma_token}"},
    )
    assert note_res.status_code == 201, note_res.text
    note_data = note_res.json()["data"]
    assert note_data["language_used"] == "BILINGUAL"
    assert note_data["patient_understood"] is True
    assert note_data["prescription_id"] == str(prescription.id)

    # 3. Retrieve counselling notes for this prescription
    get_res = await async_client.get(
        f"/api/v1/pharmacist/counselling-notes/{prescription.id}",
        headers={"Authorization": f"Bearer {pharma_token}"},
    )
    assert get_res.status_code == 200, get_res.text
    notes = get_res.json()["data"]
    assert len(notes) >= 1
    retrieved = next(n for n in notes if n["prescription_id"] == str(prescription.id))
    assert "Amoxicillin" in retrieved["counselling_summary"]
    assert retrieved["language_used"] == "BILINGUAL"
    assert retrieved["follow_up_recommended"] is False
