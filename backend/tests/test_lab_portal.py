"""
Phase 4 — Lab Technician & Pathologist Portal Tests (Role 05)
============================================================
Comprehensive test suite verifying:
  1. test_lab_worklist_filtering_and_demographics
  2. test_sample_collection_accessioning
  3. test_critical_value_alert_auto_detection
  4. test_multi_parameter_panel_result_entry
  5. test_pathologist_verification_separation_of_duties
  6. test_bilingual_diagnostic_guidance_ai
"""

import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import SystemPermissions
from app.core.security import create_access_token
from app.models.healthcare import (
    Consultation,
    LabOrder,
    LabOrderStatus,
    Patient,
)
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole


# ---------------------------------------------------------------------------
# Helper: seed a Lab Technician user and a Pathologist/Doctor verifier
# ---------------------------------------------------------------------------

async def _seed_lab_actors(db_session: AsyncSession, seeded_data: dict):
    """Seed dedicated Lab Technician and Pathologist users with appropriate scopes."""
    org = seeded_data["org"]
    fac = seeded_data["facility"]

    needed_codes = [
        SystemPermissions.LABS_ORDER_READ,
        SystemPermissions.LABS_SAMPLE_COLLECT,
        SystemPermissions.LABS_RESULT_RECORD,
        SystemPermissions.LABS_RESULT_VERIFY,
        SystemPermissions.PATIENTS_RECORDS_READ,
        SystemPermissions.PATIENTS_PROFILE_READ,
    ]
    perm_rows = (
        await db_session.execute(select(Permission).where(Permission.code.in_(needed_codes)))
    ).scalars().all()
    perm_map = {p.code: p for p in perm_rows}

    # 1. Lab Technician Role (Can collect samples, record results, read orders — NO verify)
    tech_role = Role(id=uuid.uuid4(), name="Lab Technician", code="LAB_TECH", is_system=False, is_active=True)
    db_session.add(tech_role)
    await db_session.flush()

    for c in [
        SystemPermissions.LABS_ORDER_READ,
        SystemPermissions.LABS_SAMPLE_COLLECT,
        SystemPermissions.LABS_RESULT_RECORD,
        SystemPermissions.PATIENTS_RECORDS_READ,
        SystemPermissions.PATIENTS_PROFILE_READ,
    ]:
        if c in perm_map:
            db_session.add(RolePermission(role_id=tech_role.id, permission_id=perm_map[c].id))

    tech_user = User(
        id=uuid.uuid4(),
        email="labtech@test.gov.in",
        hashed_password="hashed",
        full_name="Technician Karthik",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(tech_user)
    await db_session.flush()
    db_session.add(
        UserRole(user_id=tech_user.id, role_id=tech_role.id, organization_id=org.id, facility_id=fac.id, scope_level=ScopeLevel.FACILITY)
    )

    # 2. Pathologist / Verifier Role (Has LABS_RESULT_VERIFY)
    patho_role = Role(id=uuid.uuid4(), name="Pathologist", code="PATHOLOGIST", is_system=False, is_active=True)
    db_session.add(patho_role)
    await db_session.flush()

    for c in [
        SystemPermissions.LABS_ORDER_READ,
        SystemPermissions.LABS_RESULT_VERIFY,
        SystemPermissions.PATIENTS_RECORDS_READ,
    ]:
        if c in perm_map:
            db_session.add(RolePermission(role_id=patho_role.id, permission_id=perm_map[c].id))

    patho_user = User(
        id=uuid.uuid4(),
        email="pathologist@test.gov.in",
        hashed_password="hashed",
        full_name="Dr. Anitha (Pathologist)",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(patho_user)
    await db_session.flush()
    db_session.add(
        UserRole(user_id=patho_user.id, role_id=patho_role.id, organization_id=org.id, facility_id=fac.id, scope_level=ScopeLevel.FACILITY)
    )

    await db_session.commit()

    tech_token = create_access_token(tech_user.id, extra_claims={"email": tech_user.email})
    patho_token = create_access_token(patho_user.id, extra_claims={"email": patho_user.email})
    return tech_user, tech_token, patho_user, patho_token


async def _setup_patient_and_order(db_session: AsyncSession, seeded_data: dict, test_category: str = "HEMATOLOGY") -> tuple[Patient, LabOrder]:
    """Helper to set up patient, consultation, and a lab order."""
    facility = seeded_data["facility"]
    doctor = seeded_data["doctor_user"]

    patient = Patient(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_identifier=f"PAT-LAB-{uuid.uuid4().hex[:6].upper()}",
        first_name="Murugan",
        last_name="Velan",
        date_of_birth=date(1994, 5, 20),
        gender="MALE",
        phone_number="+919876543210",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.flush()

    consultation = Consultation(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        chief_complaint="High fever and body ache x 4 days",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(consultation)
    await db_session.flush()

    order = LabOrder(
        id=uuid.uuid4(),
        consultation_id=consultation.id,
        patient_id=patient.id,
        ordered_by_doctor_id=doctor.id,
        facility_id=facility.id,
        test_category=test_category,
        clinical_notes="Rule out dengue or severe bacterial infection",
        status=LabOrderStatus.ORDERED,
        ordered_at=datetime.now(timezone.utc),
    )
    db_session.add(order)
    await db_session.commit()
    return patient, order


# ===========================================================================
# TEST 1: Worklist Filtering & Demographics
# ===========================================================================

@pytest.mark.asyncio
async def test_lab_worklist_filtering_and_demographics(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Lab worklist returns pending orders with patient demographics, doctor name,
    and supports filtering by test category and status.
    """
    facility = seeded_data["facility"]
    _, tech_token, _, _ = await _seed_lab_actors(db_session, seeded_data)

    # Create 2 orders: one HEMATOLOGY, one SEROLOGY
    pat1, order1 = await _setup_patient_and_order(db_session, seeded_data, test_category="HEMATOLOGY")
    pat2, order2 = await _setup_patient_and_order(db_session, seeded_data, test_category="SEROLOGY")

    # 1. Fetch entire worklist
    res = await async_client.get(
        f"/api/v1/lab/worklist?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert res.status_code == 200, res.text
    items = res.json()["data"]
    assert len(items) >= 2

    # Check order1 details
    item1 = next((i for i in items if i["id"] == str(order1.id)), None)
    assert item1 is not None
    assert item1["patient_name"] == "Murugan Velan"
    assert item1["patient_identifier"] == pat1.patient_identifier
    assert item1["test_category"] == "HEMATOLOGY"
    assert item1["status"] == "ORDERED"
    assert item1["gender"] == "MALE"
    assert item1["age"] is not None
    assert item1["doctor_name"].startswith("Dr.")

    # 2. Filter by test_category = "SEROLOGY"
    filter_res = await async_client.get(
        f"/api/v1/lab/worklist?facility_id={facility.id}&test_category=SEROLOGY",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert filter_res.status_code == 200
    filtered_items = filter_res.json()["data"]
    order_ids = [i["id"] for i in filtered_items]
    assert str(order2.id) in order_ids
    assert str(order1.id) not in order_ids


# ===========================================================================
# TEST 2: Sample Collection & Accessioning
# ===========================================================================

@pytest.mark.asyncio
async def test_sample_collection_accessioning(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Lab technician records sample collection with barcode, sample type,
    and transitions order from ORDERED to SAMPLE_COLLECTED.
    """
    _, tech_token, _, _ = await _seed_lab_actors(db_session, seeded_data)
    _, order = await _setup_patient_and_order(db_session, seeded_data, test_category="HEMATOLOGY")

    res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/collect-sample",
        json={
            "sample_type": "Whole Blood (EDTA)",
            "sample_barcode": "SPL-2026-EDTA-001",
            "collection_notes": "Sample drawn via venipuncture in EDTA vacutainer.",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] == "SAMPLE_COLLECTED"
    assert data["sample_type"] == "Whole Blood (EDTA)"
    assert data["sample_barcode"] == "SPL-2026-EDTA-001"
    assert data["sample_collected_at"] is not None


# ===========================================================================
# TEST 3: Critical Value Alert Auto-Detection
# ===========================================================================

@pytest.mark.asyncio
async def test_critical_value_alert_auto_detection(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Critical value detection engine flags panic values:
    - Hemoglobin < 7.0 g/dL -> Panic Severe Anemia
    - Dengue NS1 POSITIVE -> IDSP Notifiable Alert
    - Verifies worklist item has_critical_alert is set to True.
    """
    facility = seeded_data["facility"]
    _, tech_token, _, _ = await _seed_lab_actors(db_session, seeded_data)
    _, order = await _setup_patient_and_order(db_session, seeded_data, test_category="HEMATOLOGY")

    # 1. Record Hemoglobin = 6.2 g/dL (Severe panic value < 7.0)
    hb_res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/results",
        json={
            "test_name": "Hemoglobin",
            "result_value": "6.2",
            "reference_range": "13.0 - 17.0",
            "unit": "g/dL",
            "is_abnormal": True,
            "notes": "Verified by duplicate automated run",
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert hb_res.status_code == 201, hb_res.text
    hb_data = hb_res.json()["data"]
    assert hb_data["is_abnormal"] is True
    assert hb_data["critical_alert"] is not None
    assert "CRITICAL PANIC" in hb_data["critical_alert"]
    assert "Severe Anemia" in hb_data["critical_alert"]

    # 2. Record Dengue NS1 = POSITIVE on another order
    _, dengue_order = await _setup_patient_and_order(db_session, seeded_data, test_category="SEROLOGY")
    dengue_res = await async_client.post(
        f"/api/v1/lab/orders/{dengue_order.id}/results",
        json={
            "test_name": "Dengue NS1 Antigen Rapid Test",
            "result_value": "POSITIVE",
            "is_abnormal": True,
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert dengue_res.status_code == 201
    d_data = dengue_res.json()["data"]
    assert d_data["critical_alert"] is not None
    assert "IDSP" in d_data["critical_alert"]

    # 3. Check worklist has_critical_alert flag
    wl_res = await async_client.get(
        f"/api/v1/lab/worklist?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert wl_res.status_code == 200
    wl_items = wl_res.json()["data"]
    order_in_wl = next(i for i in wl_items if i["id"] == str(order.id))
    assert order_in_wl["has_critical_alert"] is True


# ===========================================================================
# TEST 4: Multi-Parameter Panel Result Entry
# ===========================================================================

@pytest.mark.asyncio
async def test_multi_parameter_panel_result_entry(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Atomically records multiple parameters of a complete hemogram (CBC) panel.
    Order status moves to IN_ANALYSIS.
    """
    _, tech_token, _, _ = await _seed_lab_actors(db_session, seeded_data)
    _, order = await _setup_patient_and_order(db_session, seeded_data, test_category="COMPLETE_HEMOGRAM")

    panel_payload = {
        "results": [
            {
                "test_name": "Hemoglobin",
                "result_value": "13.8",
                "reference_range": "13.0 - 17.0",
                "unit": "g/dL",
                "is_abnormal": False,
            },
            {
                "test_name": "Total Leukocyte Count (WBC)",
                "result_value": "8500",
                "reference_range": "4000 - 11000",
                "unit": "/µL",
                "is_abnormal": False,
            },
            {
                "test_name": "Platelet Count",
                "result_value": "180000",
                "reference_range": "150000 - 450000",
                "unit": "/µL",
                "is_abnormal": False,
            },
            {
                "test_name": "Packed Cell Volume (PCV)",
                "result_value": "41.5",
                "reference_range": "40.0 - 50.0",
                "unit": "%",
                "is_abnormal": False,
            },
        ]
    }

    res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/panel-results",
        json=panel_payload,
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert res.status_code == 201, res.text
    results = res.json()["data"]
    assert len(results) == 4
    test_names = [r["test_name"] for r in results]
    assert "Hemoglobin" in test_names
    assert "Platelet Count" in test_names

    # Verify order status transitioned to IN_ANALYSIS
    wl_res = await async_client.get(
        f"/api/v1/lab/worklist?facility_id={seeded_data['facility'].id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert wl_res.status_code == 200
    order_item = next(i for i in wl_res.json()["data"] if i["id"] == str(order.id))
    assert order_item["status"] == "IN_ANALYSIS"


# ===========================================================================
# TEST 5: Pathologist Verification & Separation of Duties
# ===========================================================================

@pytest.mark.asyncio
async def test_pathologist_verification_separation_of_duties(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Enforces role separation:
    - Technician has LABS_RESULT_RECORD but CANNOT verify (403).
    - Pathologist/Doctor has LABS_RESULT_VERIFY and CAN verify (200).
    - Order is finalized as COMPLETED with verifier timestamp.
    """
    tech_user, tech_token, patho_user, patho_token = await _seed_lab_actors(db_session, seeded_data)
    _, order = await _setup_patient_and_order(db_session, seeded_data, test_category="BIOCHEMISTRY")

    # 1. Tech enters a result
    r_res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/results",
        json={
            "test_name": "Random Blood Glucose",
            "result_value": "118",
            "reference_range": "70 - 140",
            "unit": "mg/dL",
            "is_abnormal": False,
        },
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert r_res.status_code == 201

    # 2. Tech attempts to verify order -> 403 Forbidden
    tech_v_res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/verify",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert tech_v_res.status_code == 403

    # 3. Pathologist verifies order -> 200 OK
    patho_v_res = await async_client.post(
        f"/api/v1/lab/orders/{order.id}/verify",
        headers={"Authorization": f"Bearer {patho_token}"},
    )
    assert patho_v_res.status_code == 200, patho_v_res.text
    v_data = patho_v_res.json()["data"]
    assert v_data["status"] == "COMPLETED"
    assert v_data["completed_at"] is not None

    # Check verified_by_id on results
    res_list = v_data["results"]
    assert len(res_list) == 1
    assert res_list[0]["verified_by_id"] == str(patho_user.id)
    assert res_list[0]["verified_at"] is not None


# ===========================================================================
# TEST 6: Bilingual Diagnostic Guidance AI
# ===========================================================================

@pytest.mark.asyncio
async def test_bilingual_diagnostic_guidance_ai(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Diagnostic AI provides bilingual (English + Tamil) clinical guidance,
    panic thresholds, and reporting mandates (IDSP, Nikshay, NVBDCP).
    """
    _, tech_token, _, _ = await _seed_lab_actors(db_session, seeded_data)

    # 1. Test Hemoglobin severe anemia guidance for pregnant woman
    hb_req = {
        "test_name": "Hemoglobin (Hb)",
        "result_value": "6.8",
        "patient_age": 24,
        "patient_gender": "FEMALE",
        "is_pregnant": True,
        "language": "en",
    }
    hb_res = await async_client.post(
        "/api/v1/lab/diagnostic-guidance",
        json=hb_req,
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert hb_res.status_code == 200, hb_res.text
    hb_data = hb_res.json()["data"]
    assert hb_data["is_critical"] is True
    assert "Severe Anemia in Pregnancy" in hb_data["critical_alert_en"]
    assert len(hb_data["interpretation_ta"]) > 0
    assert len(hb_data["action_guidance_ta"]) > 0
    assert "ANC" in (hb_data["reporting_mandate"] or "")

    # 2. Test Sputum AFB positive for Tuberculosis (Nikshay mandate)
    tb_req = {
        "test_name": "Sputum AFB Smear Microscopy",
        "result_value": "POSITIVE 2+",
        "patient_age": 45,
        "patient_gender": "MALE",
        "is_pregnant": False,
        "language": "en",
    }
    tb_res = await async_client.post(
        "/api/v1/lab/diagnostic-guidance",
        json=tb_req,
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert tb_res.status_code == 200
    tb_data = tb_res.json()["data"]
    assert tb_data["is_critical"] is True
    assert "Nikshay" in (tb_data["reporting_mandate"] or "")
    assert "Tuberculosis" in tb_data["critical_alert_en"]
    assert "NTEP" in " ".join(tb_data["references"])
