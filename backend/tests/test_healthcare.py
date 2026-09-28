import uuid
from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.identity import Role, RolePermission, ScopeLevel, User, UserRole


@pytest_asyncio.fixture
async def healthcare_fixtures(db_session, seeded_data):
    """Seed additional healthcare staff: Nurse and Pharmacist."""
    org = seeded_data["org"]
    fac = seeded_data["facility"]

    # 1. Fetch or create Nurse and Pharmacist roles
    nurse_role = Role(
        id=uuid.uuid4(),
        name="Staff Nurse",
        code="NURSE",
        is_system=True,
        is_active=True,
    )
    pharmacist_role = Role(
        id=uuid.uuid4(),
        name="Pharmacist",
        code="PHARMACIST",
        is_system=True,
        is_active=True,
    )
    lab_tech_role = Role(
        id=uuid.uuid4(),
        name="Lab Tech",
        code="LAB_TECHNICIAN",
        is_system=True,
        is_active=True,
    )
    db_session.add_all([nurse_role, pharmacist_role, lab_tech_role])
    await db_session.flush()

    # Map permissions
    from app.core.permissions import SystemPermissions
    from app.repositories.role_repository import RoleRepository

    role_repo = RoleRepository(db_session)
    all_perms = await role_repo.list_permissions()
    perm_by_code = {p.code: p for p in all_perms}

    nurse_perm_codes = [
        SystemPermissions.PATIENTS_PROFILE_CREATE,
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.PATIENTS_PROFILE_UPDATE,
        SystemPermissions.PATIENTS_VITALS_RECORD,
        SystemPermissions.APPOINTMENTS_MANAGE,
        SystemPermissions.APPOINTMENTS_VIEW,
    ]
    for c in nurse_perm_codes:
        if c in perm_by_code:
            db_session.add(RolePermission(role_id=nurse_role.id, permission_id=perm_by_code[c].id))

    pharm_perm_codes = [
        SystemPermissions.PRESCRIPTIONS_READ,
        SystemPermissions.PRESCRIPTIONS_DISPENSE,
    ]
    for c in pharm_perm_codes:
        if c in perm_by_code:
            db_session.add(RolePermission(role_id=pharmacist_role.id, permission_id=perm_by_code[c].id))

    lab_perm_codes = [
        SystemPermissions.LABS_ORDER_READ,
        SystemPermissions.LABS_RESULT_RECORD,
    ]
    for c in lab_perm_codes:
        if c in perm_by_code:
            db_session.add(RolePermission(role_id=lab_tech_role.id, permission_id=perm_by_code[c].id))

    # Add referral and lab verify permissions to doctor
    doc_role = await role_repo.get_by_code("DOCTOR")
    doc_extra_perms = [
        SystemPermissions.LABS_RESULT_VERIFY,
        SystemPermissions.REFERRALS_CREATE,
        SystemPermissions.REFERRALS_READ,
        SystemPermissions.REFERRALS_UPDATE,
    ]
    if doc_role:
        for c in doc_extra_perms:
            if c in perm_by_code:
                db_session.add(RolePermission(role_id=doc_role.id, permission_id=perm_by_code[c].id))

    await db_session.flush()

    # Users
    nurse_user = User(
        id=uuid.uuid4(),
        email="nurse@test.gov.in",
        hashed_password=get_password_hash("NursePass123!"),
        full_name="Nurse Mary",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    pharm_user = User(
        id=uuid.uuid4(),
        email="pharm@test.gov.in",
        hashed_password=get_password_hash("PharmPass123!"),
        full_name="Pharmacist Kumar",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    lab_user = User(
        id=uuid.uuid4(),
        email="lab@test.gov.in",
        hashed_password=get_password_hash("LabPass123!"),
        full_name="Technician Ramesh",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([nurse_user, pharm_user, lab_user])
    await db_session.flush()

    db_session.add(UserRole(user_id=nurse_user.id, role_id=nurse_role.id, facility_id=fac.id, scope_level=ScopeLevel.FACILITY))
    db_session.add(UserRole(user_id=pharm_user.id, role_id=pharmacist_role.id, facility_id=fac.id, scope_level=ScopeLevel.FACILITY))
    db_session.add(UserRole(user_id=lab_user.id, role_id=lab_tech_role.id, facility_id=fac.id, scope_level=ScopeLevel.FACILITY))
    await db_session.commit()

    return {
        "nurse_token": create_access_token(nurse_user.id, extra_claims={"email": nurse_user.email}),
        "pharm_token": create_access_token(pharm_user.id, extra_claims={"email": pharm_user.email}),
        "lab_token": create_access_token(lab_user.id, extra_claims={"email": lab_user.email}),
    }


@pytest.mark.asyncio
async def test_patient_registration_and_search(async_client: AsyncClient, seeded_data, healthcare_fixtures):
    nurse_headers = {"Authorization": f"Bearer {healthcare_fixtures['nurse_token']}"}
    fac_id = str(seeded_data["facility"].id)

    # 1. Register Patient
    payload = {
        "first_name": "Ravi",
        "last_name": "Chandran",
        "date_of_birth": "1988-06-15",
        "gender": "MALE",
        "phone_number": "+919884011223",
        "primary_facility_id": fac_id,
        "blood_group": "O+",
        "address": "42 Fishermen Colony, Kovalam",
        "emergency_contact_name": "Meena Chandran",
        "emergency_contact_phone": "+919884099887",
        "emergency_contact_relation": "SPOUSE",
    }
    create_res = await async_client.post("/api/v1/patients", json=payload, headers=nurse_headers)
    assert create_res.status_code == 201
    patient = create_res.json()["data"]
    assert patient["first_name"] == "Ravi"
    assert patient["patient_identifier"].startswith("PAT-")
    patient_id = patient["id"]

    # 2. Search Patient by phone
    search_res = await async_client.get("/api/v1/patients?query=9884011223", headers=nurse_headers)
    assert search_res.status_code == 200
    search_data = search_res.json()["data"]
    assert len(search_data) >= 1
    assert search_data[0]["id"] == patient_id


@pytest.mark.asyncio
async def test_appointment_lifecycle_and_state_machine(async_client: AsyncClient, seeded_data, healthcare_fixtures):
    nurse_headers = {"Authorization": f"Bearer {healthcare_fixtures['nurse_token']}"}
    fac_id = str(seeded_data["facility"].id)

    # 1. Register Patient
    p_res = await async_client.post(
        "/api/v1/patients",
        json={
            "first_name": "Lakshmi",
            "last_name": "Narayanan",
            "date_of_birth": "1992-03-21",
            "gender": "FEMALE",
            "phone_number": "+919841022334",
            "primary_facility_id": fac_id,
        },
        headers=nurse_headers,
    )
    patient_id = p_res.json()["data"]["id"]

    # 2. Schedule Appointment
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    appt_payload = {
        "patient_id": patient_id,
        "facility_id": fac_id,
        "doctor_id": str(seeded_data["doctor_user"].id),
        "appointment_date": future_date,
        "reason": "Persistent dry cough and mild fever",
    }
    appt_res = await async_client.post("/api/v1/appointments", json=appt_payload, headers=nurse_headers)
    assert appt_res.status_code == 201
    appt = appt_res.json()["data"]
    assert appt["status"] == "SCHEDULED"
    appt_id = appt["id"]

    # 3. Patient arrives: Check in
    checkin_res = await async_client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "CHECKED_IN"},
        headers=nurse_headers,
    )
    assert checkin_res.status_code == 200
    assert checkin_res.json()["data"]["status"] == "CHECKED_IN"


@pytest.mark.asyncio
async def test_complete_clinical_encounter_workflow(async_client: AsyncClient, seeded_data, healthcare_fixtures):
    nurse_headers = {"Authorization": f"Bearer {healthcare_fixtures['nurse_token']}"}
    doc_headers = {"Authorization": f"Bearer {seeded_data['doctor_token']}"}
    pharm_headers = {"Authorization": f"Bearer {healthcare_fixtures['pharm_token']}"}
    lab_headers = {"Authorization": f"Bearer {healthcare_fixtures['lab_token']}"}
    fac_id = str(seeded_data["facility"].id)

    # 1. Patient & Appointment
    p_res = await async_client.post(
        "/api/v1/patients",
        json={
            "first_name": "Karthik",
            "last_name": "Subramanian",
            "date_of_birth": "1975-11-10",
            "gender": "MALE",
            "phone_number": "+919840991122",
            "primary_facility_id": fac_id,
        },
        headers=nurse_headers,
    )
    patient_id = p_res.json()["data"]["id"]

    appt_res = await async_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "facility_id": fac_id,
            "appointment_date": datetime.now(timezone.utc).isoformat(),
            "reason": "Severe acute bronchitis evaluation",
        },
        headers=nurse_headers,
    )
    appt_id = appt_res.json()["data"]["id"]

    # 2. Doctor Commences Consultation with Vitals
    consult_payload = {
        "patient_id": patient_id,
        "appointment_id": appt_id,
        "chief_complaint": "Productive cough with yellow sputum for 5 days, shortness of breath",
        "triage_vitals": {
            "systolic_bp": 130,
            "diastolic_bp": 85,
            "pulse_rate": 88,
            "temperature_celsius": 38.2,
            "respiratory_rate": 20,
            "spo2_percent": 96,
            "weight_kg": 72.5,
            "height_cm": 172.0,
        },
        "clinical_notes": "Bilateral rhonchi present on auscultation. No cyanosis.",
        "examination_findings": "Pharyngeal erythema observed.",
    }
    consult_res = await async_client.post("/api/v1/consultations", json=consult_payload, headers=doc_headers)
    assert consult_res.status_code == 201
    consultation = consult_res.json()["data"]
    assert consultation["status"] == "IN_PROGRESS"
    consult_id = consultation["id"]

    # 3. Doctor orders Diagnostic Lab Test
    lab_order_payload = {
        "consultation_id": consult_id,
        "test_category": "HEMATOLOGY",
        "clinical_notes": "Complete blood count to rule out acute bacterial infection",
    }
    lab_order_res = await async_client.post("/api/v1/labs/orders", json=lab_order_payload, headers=doc_headers)
    assert lab_order_res.status_code == 201
    lab_order_id = lab_order_res.json()["data"]["id"]

    # 4. Lab Technician Records Lab Results
    lab_result_payload = {
        "test_name": "White Blood Cell Count (WBC)",
        "result_value": "12500",
        "reference_range": "4000-11000",
        "unit": "cells/mcL",
        "is_abnormal": True,
        "notes": "Elevated leukocytosis consistent with acute infection.",
    }
    lab_res = await async_client.post(
        f"/api/v1/labs/orders/{lab_order_id}/results",
        json=lab_result_payload,
        headers=lab_headers,
    )
    assert lab_res.status_code == 201
    assert lab_res.json()["data"]["is_abnormal"] is True

    # 5. Doctor Verifies Lab Order
    verify_res = await async_client.post(f"/api/v1/labs/orders/{lab_order_id}/verify", headers=doc_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "COMPLETED"

    # 6. Doctor Issues Prescription
    rx_payload = {
        "consultation_id": consult_id,
        "notes": "Take medications with food. Return if fever persists beyond 48 hours.",
        "items": [
            {
                "medication_name": "Amoxicillin 500mg Capsule",
                "medication_code": "MED-AMOX-500",
                "dosage": "500mg",
                "frequency": "TID (Every 8 hours)",
                "duration_days": 7,
                "quantity_prescribed": 21,
                "instructions": "Complete full course of antibiotics.",
            },
            {
                "medication_name": "Paracetamol 650mg Tablet",
                "medication_code": "MED-PARA-650",
                "dosage": "650mg",
                "frequency": "PRN (As needed for fever)",
                "duration_days": 5,
                "quantity_prescribed": 10,
                "instructions": "Max 4 tablets in 24 hours.",
            },
        ],
    }
    rx_res = await async_client.post("/api/v1/prescriptions", json=rx_payload, headers=doc_headers)
    assert rx_res.status_code == 201
    prescription = rx_res.json()["data"]
    assert prescription["status"] == "ISSUED"
    assert len(prescription["items"]) == 2
    rx_id = prescription["id"]
    item_amox_id = prescription["items"][0]["id"]
    item_para_id = prescription["items"][1]["id"]

    # 7. Doctor Finalizes Consultation with Diagnoses
    finalize_payload = {
        "clinical_notes": "Patient advised rest, hydration, and prescribed antibiotic course.",
        "diagnoses": [
            {
                "icd10_code": "J20.9",
                "condition_name": "Acute bronchitis, unspecified",
                "diagnosis_type": "PRIMARY",
                "notes": "Clinical and hematological confirmation",
            }
        ],
    }
    final_res = await async_client.post(
        f"/api/v1/consultations/{consult_id}/finalize",
        json=finalize_payload,
        headers=doc_headers,
    )
    assert final_res.status_code == 200
    assert final_res.json()["data"]["status"] == "FINALIZED"
    assert len(final_res.json()["data"]["diagnoses"]) == 1

    # 8. Pharmacist Dispenses Prescription Items
    dispense_payload = {
        "dispensed_items": {
            item_amox_id: 21,
            item_para_id: 10,
        }
    }
    dispense_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json=dispense_payload,
        headers=pharm_headers,
    )
    assert dispense_res.status_code == 200
    assert dispense_res.json()["data"]["status"] == "COMPLETED"

    # 9. Verify Patient's Longitudinal Clinical History
    history_res = await async_client.get(f"/api/v1/patients/{patient_id}/clinical-history", headers=doc_headers)
    assert history_res.status_code == 200
    history = history_res.json()["data"]
    assert history["patient"]["first_name"] == "Karthik"
    assert len(history["consultations"]) == 1
    assert history["consultations"][0]["diagnoses"][0]["icd10_code"] == "J20.9"


@pytest.mark.asyncio
async def test_healthcare_permission_enforcement(async_client: AsyncClient, seeded_data, healthcare_fixtures):
    nurse_headers = {"Authorization": f"Bearer {healthcare_fixtures['nurse_token']}"}
    fac_id = str(seeded_data["facility"].id)

    # 1. Nurse trying to conduct consultation -> 403 Forbidden
    consult_payload = {
        "patient_id": str(uuid.uuid4()),
        "chief_complaint": "Unauthorized nurse consultation test",
    }
    res = await async_client.post("/api/v1/consultations", json=consult_payload, headers=nurse_headers)
    assert res.status_code == 403
    assert res.json()["code"] == "PERMISSION_DENIED"

    # 2. Nurse trying to issue prescription -> 403 Forbidden
    rx_payload = {
        "consultation_id": str(uuid.uuid4()),
        "items": [{"medication_name": "Test Med", "dosage": "1", "frequency": "1", "duration_days": 1, "quantity_prescribed": 1}],
    }
    rx_res = await async_client.post("/api/v1/prescriptions", json=rx_payload, headers=nurse_headers)
    assert rx_res.status_code == 403
    assert rx_res.json()["code"] == "PERMISSION_DENIED"
