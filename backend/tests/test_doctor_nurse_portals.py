import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.permissions import SystemPermissions
from app.core.security import create_access_token, get_password_hash
from app.models.facility import Facility, FacilityType
from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    Consultation,
    ConsultationStatus,
    Patient,
)
from sqlalchemy import select
from app.models.identity import Role, RolePermission, ScopeLevel, User, UserRole
from app.repositories.role_repository import RoleRepository


@pytest_asyncio.fixture
async def clinical_portal_fixtures(db_session, seeded_data):
    """Seed Doctor and Nurse roles, users, and test patient."""
    org = seeded_data["org"]
    fac = seeded_data["facility"]
    doctor_user = seeded_data["doctor_user"]

    role_repo = RoleRepository(db_session)
    all_perms = await role_repo.list_permissions()
    perm_by_code = {p.code: p for p in all_perms}

    # 1. Update Doctor Role with full Doctor Portal permissions
    doc_role = await role_repo.get_by_code("DOCTOR")
    res_existing = await db_session.execute(
        select(RolePermission.permission_id).where(RolePermission.role_id == doc_role.id)
    )
    existing_perm_ids = set(res_existing.scalars().all())

    doc_perms = [
        SystemPermissions.STAFF_ATTENDANCE_RECORD,
        SystemPermissions.STAFF_ATTENDANCE_READ,
        SystemPermissions.APPOINTMENTS_VIEW,
        SystemPermissions.APPOINTMENTS_MANAGE,
        SystemPermissions.CONSULTATIONS_CONDUCT,
        SystemPermissions.PRESCRIPTIONS_CREATE,
        SystemPermissions.PRESCRIPTIONS_READ,
        SystemPermissions.LABS_ORDER_CREATE,
        SystemPermissions.LABS_ORDER_READ,
        SystemPermissions.REFERRALS_CREATE,
        SystemPermissions.REFERRALS_READ,
        SystemPermissions.CLINICAL_AI_ADVISORY,
    ]
    for code in doc_perms:
        if code in perm_by_code and perm_by_code[code].id not in existing_perm_ids:
            db_session.add(RolePermission(role_id=doc_role.id, permission_id=perm_by_code[code].id))
            existing_perm_ids.add(perm_by_code[code].id)

    # 2. Create Staff Nurse Role and User
    nurse_role = Role(
        id=uuid.uuid4(),
        name="Staff Nurse",
        code="NURSE",
        is_system=True,
        is_active=True,
    )
    db_session.add(nurse_role)
    await db_session.flush()

    nurse_perms = [
        SystemPermissions.STAFF_ATTENDANCE_RECORD,
        SystemPermissions.STAFF_ATTENDANCE_READ,
        SystemPermissions.APPOINTMENTS_VIEW,
        SystemPermissions.APPOINTMENTS_MANAGE,
        SystemPermissions.PATIENTS_VITALS_RECORD,
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.CLINICAL_AI_ADVISORY,
    ]
    for code in nurse_perms:
        if code in perm_by_code:
            db_session.add(RolePermission(role_id=nurse_role.id, permission_id=perm_by_code[code].id))

    nurse_user = User(
        id=uuid.uuid4(),
        email="nurse@test.gov.in",
        phone_number="+919876543222",
        hashed_password=get_password_hash("NursePass123!"),
        full_name="Sister Anitha",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(nurse_user)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=nurse_user.id,
            role_id=nurse_role.id,
            organization_id=org.id,
            facility_id=fac.id,
            scope_level=ScopeLevel.FACILITY,
        )
    )

    # 3. Create Test Patient
    patient = Patient(
        id=uuid.uuid4(),
        primary_facility_id=fac.id,
        patient_identifier="PAT-KOV-2026-0042",
        first_name="Murugan",
        last_name="Velu",
        date_of_birth=date(1985, 3, 20),
        gender="MALE",
        phone_number="+919876543200",
        address="Kovalam Kuppam",
        blood_group="O+",
        preferred_language="ta",
        chronic_conditions="HYPERTENSION, ASTHMA",
        allergies="Penicillin",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.commit()

    doc_token = create_access_token(doctor_user.id, extra_claims={"email": doctor_user.email})
    nurse_token = create_access_token(nurse_user.id, extra_claims={"email": nurse_user.email})

    return {
        "doctor_user": doctor_user,
        "doctor_token": doc_token,
        "nurse_user": nurse_user,
        "nurse_token": nurse_token,
        "facility": fac,
        "patient": patient,
    }


@pytest.mark.asyncio
async def test_doctor_and_nurse_duty_attendance(async_client: AsyncClient, clinical_portal_fixtures):
    doc_token = clinical_portal_fixtures["doctor_token"]
    nurse_token = clinical_portal_fixtures["nurse_token"]
    fac_id = str(clinical_portal_fixtures["facility"].id)

    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    nurse_headers = {"Authorization": f"Bearer {nurse_token}"}

    # 1. Doctor duty check-in
    res_doc_in = await async_client.post(
        "/api/v1/doctor/attendance/check-in",
        headers=doc_headers,
        json={"facility_id": fac_id, "shift": "MORNING", "notes": "Reporting for OPD Duty Room 2"},
    )
    assert res_doc_in.status_code == 201, res_doc_in.text
    doc_att = res_doc_in.json()["data"]
    assert doc_att["status"] == "PRESENT"
    assert doc_att["shift"] == "MORNING"

    # Verify doctor check-in idempotent
    res_doc_today = await async_client.get("/api/v1/doctor/attendance/today", headers=doc_headers)
    assert res_doc_today.status_code == 200
    assert res_doc_today.json()["data"]["id"] == doc_att["id"]

    # 2. Nurse duty check-in
    res_nurse_in = await async_client.post(
        "/api/v1/nurse/attendance/check-in",
        headers=nurse_headers,
        json={"facility_id": fac_id, "shift": "MORNING", "notes": "Triage desk duty"},
    )
    assert res_nurse_in.status_code == 201, res_nurse_in.text
    nurse_att = res_nurse_in.json()["data"]
    assert nurse_att["status"] == "PRESENT"

    # 3. Doctor duty check-out
    res_doc_out = await async_client.post(
        "/api/v1/doctor/attendance/check-out",
        headers=doc_headers,
        json={"notes": "Completed 42 consultations"},
    )
    assert res_doc_out.status_code == 200
    assert res_doc_out.json()["data"]["check_out_time"] is not None


@pytest.mark.asyncio
async def test_deterministic_opd_queue_priority_sorting(
    async_client: AsyncClient, clinical_portal_fixtures, db_session
):
    doc_token = clinical_portal_fixtures["doctor_token"]
    fac = clinical_portal_fixtures["facility"]
    patient = clinical_portal_fixtures["patient"]
    doc_user = clinical_portal_fixtures["doctor_user"]

    headers = {"Authorization": f"Bearer {doc_token}"}
    today = datetime.now(timezone.utc)

    # Insert three appointments:
    # 1. Routine (token 501)
    appt_routine = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        facility_id=fac.id,
        doctor_id=doc_user.id,
        token_number=501,
        priority="ROUTINE",
        appointment_date=today,
        status=AppointmentStatus.SCHEDULED,
        reason="Mild body pain",
    )
    # 2. Emergency (token 502) - should be jumped to position 1 in queue!
    appt_emergency = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        facility_id=fac.id,
        doctor_id=doc_user.id,
        token_number=502,
        priority="EMERGENCY",
        appointment_date=today,
        status=AppointmentStatus.SCHEDULED,
        reason="Severe acute chest tightness",
    )
    # 3. Priority (token 503) - should be position 2 in queue!
    appt_priority = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        facility_id=fac.id,
        doctor_id=doc_user.id,
        token_number=503,
        priority="PRIORITY",
        appointment_date=today,
        status=AppointmentStatus.SCHEDULED,
        reason="High fever 102F",
    )
    db_session.add_all([appt_routine, appt_emergency, appt_priority])
    await db_session.commit()

    # Query doctor queue
    res_queue = await async_client.get(
        f"/api/v1/doctor/queue?facility_id={fac.id}&target_date={today.strftime('%Y-%m-%d')}",
        headers=headers,
    )
    assert res_queue.status_code == 200, res_queue.text
    queue = res_queue.json()["data"]
    assert len(queue) >= 3

    # Emergency must be top of the queue regardless of higher token number
    assert queue[0]["priority"] == "EMERGENCY"
    assert queue[0]["token_number"] == 502

    # Priority must be before routine
    assert queue[1]["priority"] == "PRIORITY"
    assert queue[1]["token_number"] == 503

    # Routine must be after priority
    assert queue[2]["priority"] == "ROUTINE"
    assert queue[2]["token_number"] == 501


@pytest.mark.asyncio
async def test_nurse_triage_vitals_and_early_warning_scoring(
    async_client: AsyncClient, clinical_portal_fixtures, db_session
):
    nurse_token = clinical_portal_fixtures["nurse_token"]
    fac = clinical_portal_fixtures["facility"]
    patient = clinical_portal_fixtures["patient"]
    doc_user = clinical_portal_fixtures["doctor_user"]

    headers = {"Authorization": f"Bearer {nurse_token}"}
    today = datetime.now(timezone.utc)

    # 1. Create a routine appointment
    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        facility_id=fac.id,
        doctor_id=doc_user.id,
        token_number=510,
        priority="ROUTINE",
        appointment_date=today,
        status=AppointmentStatus.SCHEDULED,
        reason="Difficulty breathing",
    )
    db_session.add(appt)
    await db_session.commit()

    # 2. Nurse records triage vitals with critical SpO2 = 87% (Early Warning Score red flag)
    vitals_payload = {
        "systolic_bp": 170,
        "diastolic_bp": 105,
        "pulse_rate": 118,
        "temperature_celsius": 38.2,
        "respiratory_rate": 26,
        "spo2_percent": 87,  # Critical < 90%
        "weight_kg": 68.0,
        "height_cm": 165.0,
    }
    res_triage = await async_client.post(
        f"/api/v1/nurse/triage/vitals?appointment_id={appt.id}",
        headers=headers,
        json=vitals_payload,
    )
    assert res_triage.status_code == 201, res_triage.text
    vitals = res_triage.json()["data"]
    # Verify BMI calculated: 68 / (1.65^2) = ~25.0
    assert vitals["bmi"] == 25.0
    # Automated triage priority elevated to EMERGENCY
    assert vitals["triage_level"] == "EMERGENCY"
    assert "Critical Hypoxia" in vitals["triage_notes"]

    # 3. Verify appointment priority elevated to EMERGENCY and status changed to CHECKED_IN
    await db_session.refresh(appt)
    assert appt.priority == "EMERGENCY"
    assert appt.status == AppointmentStatus.CHECKED_IN


@pytest.mark.asyncio
async def test_doctor_clinical_encounter_prescription_and_lab_workflow(
    async_client: AsyncClient, clinical_portal_fixtures, db_session
):
    doc_token = clinical_portal_fixtures["doctor_token"]
    fac = clinical_portal_fixtures["facility"]
    patient = clinical_portal_fixtures["patient"]
    doc_user = clinical_portal_fixtures["doctor_user"]

    headers = {"Authorization": f"Bearer {doc_token}"}
    today = datetime.now(timezone.utc)

    # 1. Appointment checked in
    appt = Appointment(
        id=uuid.uuid4(),
        patient_id=patient.id,
        facility_id=fac.id,
        doctor_id=doc_user.id,
        token_number=515,
        priority="ROUTINE",
        appointment_date=today,
        status=AppointmentStatus.CHECKED_IN,
        reason="Follow up blood pressure check",
    )
    db_session.add(appt)
    await db_session.commit()

    # 2. Start Consultation
    res_start = await async_client.post(
        "/api/v1/doctor/consultations",
        headers=headers,
        json={
            "appointment_id": str(appt.id),
            "chief_complaint": "Persistent headache for 3 days, taking Amlodipine irregularly",
        },
    )
    assert res_start.status_code == 201, res_start.text
    consultation = res_start.json()["data"]
    consultation_id = consultation["id"]
    assert consultation["status"] == "IN_PROGRESS"

    # 3. Finalize Consultation with ICD-10 I10
    finalize_payload = {
        "clinical_notes": "Patient advised on strict low-salt diet and medication compliance.",
        "examination_findings": "Chest clear, S1/S2 heard, BP 144/92 mmHg.",
        "diagnoses": [
            {
                "icd10_code": "I10",
                "condition_name": "Essential (primary) hypertension",
                "diagnosis_type": "PRIMARY",
                "notes": "Stage 1 uncontrolled hypertension",
            }
        ],
    }
    res_fin = await async_client.post(
        f"/api/v1/doctor/consultations/{consultation_id}/finalize",
        headers=headers,
        json=finalize_payload,
    )
    assert res_fin.status_code == 200, res_fin.text
    fin_data = res_fin.json()["data"]
    assert fin_data["status"] == "FINALIZED"
    assert len(fin_data["diagnoses"]) >= 1

    # 4. Issue Prescription (Automatically dispatches to Pharmacist)
    rx_payload = {
        "consultation_id": consultation_id,
        "notes": "Take Telmisartan after breakfast daily",
        "items": [
            {
                "medication_name": "Telmisartan 40mg",
                "dosage": "40mg",
                "frequency": "ONCE_DAILY",
                "duration_days": 30,
                "quantity_prescribed": 30,
                "instructions": "Morning after food",
            },
            {
                "medication_name": "Amlodipine 5mg",
                "dosage": "5mg",
                "frequency": "ONCE_DAILY",
                "duration_days": 30,
                "quantity_prescribed": 30,
                "instructions": "Night after food",
            },
        ],
    }
    res_rx = await async_client.post("/api/v1/doctor/prescriptions", headers=headers, json=rx_payload)
    assert res_rx.status_code == 201, res_rx.text
    rx_data = res_rx.json()["data"]
    assert rx_data["status"] == "ISSUED"
    assert len(rx_data["items"]) == 2

    # 5. Order Diagnostic Lab Test
    lab_payload = {
        "consultation_id": consultation_id,
        "test_category": "Serum Electrolytes & Renal Function",
        "clinical_notes": "Monitor K+ and serum creatinine before increasing Telmisartan dosage",
    }
    res_lab = await async_client.post("/api/v1/doctor/labs", headers=headers, json=lab_payload)
    assert res_lab.status_code == 201, res_lab.text
    lab_data = res_lab.json()["data"]
    assert lab_data["status"] == "ORDERED"

    # 6. Create Specialist Referral
    ref_payload = {
        "consultation_id": consultation_id,
        "to_facility_name": "Chengalpattu Government Medical College Hospital",
        "referral_reason": "Cardiology echo evaluation for secondary hypertension causes",
        "urgency": "ROUTINE",
        "clinical_summary": "Hypertension on dual therapy. Rule out renal artery stenosis.",
    }
    res_ref = await async_client.post("/api/v1/doctor/referrals", headers=headers, json=ref_payload)
    assert res_ref.status_code == 201, res_ref.text
    assert res_ref.json()["data"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_doctor_clinical_ai_assistant_advisory(async_client: AsyncClient, clinical_portal_fixtures):
    doc_token = clinical_portal_fixtures["doctor_token"]
    headers = {"Authorization": f"Bearer {doc_token}"}

    # 1. Tamil Nadu STG advisory for Hypertension
    req_htn = {
        "icd10_code": "I10",
        "condition_name": "Primary Hypertension",
        "proposed_medications": ["Amlodipine 5mg"],
        "language": "en",
    }
    res_htn = await async_client.post("/api/v1/doctor/ai-assistant/advisory", headers=headers, json=req_htn)
    assert res_htn.status_code == 200, res_htn.text
    data_htn = res_htn.json()["data"]
    assert "Amlodipine" in data_htn["stg_protocol"]
    assert len(data_htn["monitoring_parameters"]) >= 1

    # 2. Penicillin Allergy Contraindication Screening
    req_contra = {
        "icd10_code": "J20",
        "condition_name": "Acute Bronchitis",
        "proposed_medications": ["Amoxicillin 500mg"],
        "patient_allergies": "Penicillin",
        "language": "en",
    }
    res_contra = await async_client.post("/api/v1/doctor/ai-assistant/advisory", headers=headers, json=req_contra)
    assert res_contra.status_code == 200, res_contra.text
    data_contra = res_contra.json()["data"]
    assert len(data_contra["contraindication_warnings"]) >= 1
    assert "anaphylaxis" in data_contra["contraindication_warnings"][0].lower() or "penicillin" in data_contra["contraindication_warnings"][0].lower()

    # 3. Dengue + NSAID Bleeding Risk Screening
    req_dengue = {
        "icd10_code": "A90",
        "condition_name": "Dengue Fever",
        "proposed_medications": ["Diclofenac 50mg"],
        "language": "en",
    }
    res_dengue = await async_client.post("/api/v1/doctor/ai-assistant/advisory", headers=headers, json=req_dengue)
    assert res_dengue.status_code == 200
    data_dengue = res_dengue.json()["data"]
    assert len(data_dengue["contraindication_warnings"]) >= 1
    assert "hemorrhage" in data_dengue["contraindication_warnings"][0].lower() or "dengue" in data_dengue["contraindication_warnings"][0].lower()


@pytest.mark.asyncio
async def test_nurse_immunization_and_anc_ai_guidance(async_client: AsyncClient, clinical_portal_fixtures):
    nurse_token = clinical_portal_fixtures["nurse_token"]
    headers = {"Authorization": f"Bearer {nurse_token}"}

    # 1. 6-week infant immunization check
    req_infant = {
        "patient_age_months": 1,
        "is_pregnant": False,
        "language": "en",
    }
    res_infant = await async_client.post(
        "/api/v1/nurse/ai-assistant/immunization-guidance", headers=headers, json=req_infant
    )
    assert res_infant.status_code == 200, res_infant.text
    data_infant = res_infant.json()["data"]
    assert "Universal Immunization Program" in data_infant["category"]
    assert any("Pentavalent-1" in v for v in data_infant["due_vaccines"])
    assert "+2°C and +8°C" in data_infant["cold_chain_reminder"]

    # 2. 2nd trimester Antenatal Care (ANC) guidance
    req_anc = {
        "is_pregnant": True,
        "gestational_weeks": 20,
        "language": "en",
    }
    res_anc = await async_client.post(
        "/api/v1/nurse/ai-assistant/immunization-guidance", headers=headers, json=req_anc
    )
    assert res_anc.status_code == 200, res_anc.text
    data_anc = res_anc.json()["data"]
    assert "Antenatal Care" in data_anc["category"]
    assert "Anomaly Scan" in (data_anc["anc_milestone_guidance"] or "")
    assert len(data_anc["triage_red_flags"]) >= 1
