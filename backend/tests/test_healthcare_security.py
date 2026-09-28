import asyncio
import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.permissions import SystemPermissions
from app.core.security import create_access_token, get_password_hash
from app.models.audit import AuditLog
from app.models.facility import Facility, FacilityType
from app.models.healthcare import (
    AppointmentStatus,
    ConsultationStatus,
    LabOrderStatus,
    Patient,
    PrescriptionStatus,
)
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.models.organization import Organization, OrganizationType


@pytest_asyncio.fixture
async def security_test_env(db_session, seeded_data):
    """
    Sets up multi-facility, multi-scope geographic topology:
    - Facility A: Tamil Nadu, Chengalpattu
    - Facility B: Tamil Nadu, Chengalpattu (Same District as A)
    - Facility C: Tamil Nadu, Kanchipuram (Same State as A, Different District)
    - Facility D: Kerala, Ernakulam (Different State)
    """
    org = seeded_data["org"]
    fac_a = seeded_data["facility"]

    fac_b = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="PHC Kelambakkam",
        code="TEST-PHC-B",
        facility_type=FacilityType.PHC,
        state="Tamil Nadu",
        district="Chengalpattu",
        is_active=True,
    )
    fac_c = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="CHC Walajabad",
        code="TEST-CHC-C",
        facility_type=FacilityType.CHC,
        state="Tamil Nadu",
        district="Kanchipuram",
        is_active=True,
    )
    fac_d = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="PHC Aluva",
        code="TEST-PHC-D",
        facility_type=FacilityType.PHC,
        state="Kerala",
        district="Ernakulam",
        is_active=True,
    )
    db_session.add_all([fac_b, fac_c, fac_d])
    await db_session.flush()

    # Permissions lookup
    from app.repositories.role_repository import RoleRepository
    role_repo = RoleRepository(db_session)
    all_perms = await role_repo.list_permissions()
    perm_by_code = {p.code: p for p in all_perms}

    # Roles
    doctor_role = await role_repo.get_by_code("DOCTOR")
    doc_extra = [
        SystemPermissions.PATIENTS_PROFILE_CREATE,
        SystemPermissions.PATIENTS_PROFILE_UPDATE,
        SystemPermissions.LABS_RESULT_VERIFY,
        SystemPermissions.REFERRALS_CREATE,
        SystemPermissions.REFERRALS_UPDATE,
        SystemPermissions.PRESCRIPTIONS_DISPENSE,
        SystemPermissions.PATIENTS_VITALS_RECORD,
        SystemPermissions.APPOINTMENTS_MANAGE,
    ]
    for c in doc_extra:
        if c in perm_by_code:
            db_session.add(RolePermission(role_id=doctor_role.id, permission_id=perm_by_code[c].id))

    district_officer_role = Role(
        id=uuid.uuid4(),
        name="District Medical Officer",
        code="DMO",
        is_system=True,
        is_active=True,
    )
    state_officer_role = Role(
        id=uuid.uuid4(),
        name="State Health Director",
        code="SHD",
        is_system=True,
        is_active=True,
    )
    patient_role = Role(
        id=uuid.uuid4(),
        name="Citizen Patient",
        code="PATIENT_USER",
        is_system=True,
        is_active=True,
    )
    lab_tech_role = Role(
        id=uuid.uuid4(),
        name="Lab Technician",
        code="LAB_TECH",
        is_system=True,
        is_active=True,
    )
    db_session.add_all([district_officer_role, state_officer_role, patient_role, lab_tech_role])
    await db_session.flush()

    # Map DMO & SHD read permissions
    dmo_perms = [
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.PATIENTS_RECORDS_READ,
        SystemPermissions.APPOINTMENTS_VIEW,
    ]
    for c in dmo_perms:
        db_session.add(RolePermission(role_id=district_officer_role.id, permission_id=perm_by_code[c].id))
        db_session.add(RolePermission(role_id=state_officer_role.id, permission_id=perm_by_code[c].id))

    # Patient role perms
    citizen_perms = [
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.PATIENTS_RECORDS_READ,
    ]
    for c in citizen_perms:
        db_session.add(RolePermission(role_id=patient_role.id, permission_id=perm_by_code[c].id))

    # Lab Tech perms
    db_session.add(RolePermission(role_id=lab_tech_role.id, permission_id=perm_by_code[SystemPermissions.LABS_RESULT_RECORD].id))
    db_session.add(RolePermission(role_id=lab_tech_role.id, permission_id=perm_by_code[SystemPermissions.LABS_ORDER_READ].id))

    await db_session.flush()

    # Users
    doctor_b = User(
        id=uuid.uuid4(),
        email="doctor_b@test.gov.in",
        hashed_password=get_password_hash("DocBPass123!"),
        full_name="Dr. Priya (Facility B)",
        organization_id=org.id,
        facility_id=fac_b.id,
        is_active=True,
        is_verified=True,
    )
    dmo_user = User(
        id=uuid.uuid4(),
        email="dmo@test.gov.in",
        hashed_password=get_password_hash("DmoPass123!"),
        full_name="Dr. Ramanathan (DMO)",
        organization_id=org.id,
        facility_id=fac_a.id,
        is_active=True,
        is_verified=True,
    )
    shd_user = User(
        id=uuid.uuid4(),
        email="shd@test.gov.in",
        hashed_password=get_password_hash("ShdPass123!"),
        full_name="Dr. Vasanthi (State Director)",
        organization_id=org.id,
        facility_id=fac_a.id,
        is_active=True,
        is_verified=True,
    )
    patient_user_a = User(
        id=uuid.uuid4(),
        email="citizen_a@test.gov.in",
        hashed_password=get_password_hash("CitizenPass123!"),
        full_name="Citizen Murugan",
        organization_id=org.id,
        facility_id=fac_a.id,
        is_active=True,
        is_verified=True,
    )
    patient_user_b = User(
        id=uuid.uuid4(),
        email="citizen_b@test.gov.in",
        hashed_password=get_password_hash("CitizenPass123!"),
        full_name="Citizen Anitha",
        organization_id=org.id,
        facility_id=fac_b.id,
        is_active=True,
        is_verified=True,
    )
    lab_tech_user = User(
        id=uuid.uuid4(),
        email="tech@test.gov.in",
        hashed_password=get_password_hash("TechPass123!"),
        full_name="Lab Tech Anand",
        organization_id=org.id,
        facility_id=fac_a.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([doctor_b, dmo_user, shd_user, patient_user_a, patient_user_b, lab_tech_user])
    await db_session.flush()

    # User Roles with Scopes
    db_session.add(UserRole(user_id=doctor_b.id, role_id=doctor_role.id, facility_id=fac_b.id, scope_level=ScopeLevel.FACILITY))
    db_session.add(UserRole(user_id=dmo_user.id, role_id=district_officer_role.id, facility_id=fac_a.id, scope_level=ScopeLevel.DISTRICT))
    db_session.add(UserRole(user_id=shd_user.id, role_id=state_officer_role.id, facility_id=fac_a.id, scope_level=ScopeLevel.STATE))
    db_session.add(UserRole(user_id=patient_user_a.id, role_id=patient_role.id, facility_id=fac_a.id, scope_level=ScopeLevel.SELF))
    db_session.add(UserRole(user_id=patient_user_b.id, role_id=patient_role.id, facility_id=fac_b.id, scope_level=ScopeLevel.SELF))
    db_session.add(UserRole(user_id=lab_tech_user.id, role_id=lab_tech_role.id, facility_id=fac_a.id, scope_level=ScopeLevel.FACILITY))

    # Pre-register Patient at Facility A and Facility B
    pat_a = Patient(
        id=uuid.uuid4(),
        user_id=patient_user_a.id,
        primary_facility_id=fac_a.id,
        patient_identifier="PAT-202609-00001",
        first_name="Murugan",
        last_name="Velu",
        date_of_birth=date(1990, 1, 1),
        gender="MALE",
        phone_number="+919884100001",
        is_active=True,
    )
    pat_b = Patient(
        id=uuid.uuid4(),
        user_id=patient_user_b.id,
        primary_facility_id=fac_b.id,
        patient_identifier="PAT-202609-00002",
        first_name="Anitha",
        last_name="Ramesh",
        date_of_birth=date(1995, 5, 12),
        gender="FEMALE",
        phone_number="+919884100002",
        is_active=True,
    )
    pat_c = Patient(
        id=uuid.uuid4(),
        primary_facility_id=fac_c.id,
        patient_identifier="PAT-202609-00003",
        first_name="Gopal",
        last_name="Krishnan",
        date_of_birth=date(1982, 8, 20),
        gender="MALE",
        phone_number="+919884100003",
        is_active=True,
    )
    pat_d = Patient(
        id=uuid.uuid4(),
        primary_facility_id=fac_d.id,
        patient_identifier="PAT-202609-00004",
        first_name="Mathew",
        last_name="Joseph",
        date_of_birth=date(1978, 3, 15),
        gender="MALE",
        phone_number="+919884100004",
        is_active=True,
    )
    db_session.add_all([pat_a, pat_b, pat_c, pat_d])
    await db_session.commit()

    return {
        "fac_a": fac_a,
        "fac_b": fac_b,
        "fac_c": fac_c,
        "fac_d": fac_d,
        "pat_a": pat_a,
        "pat_b": pat_b,
        "pat_c": pat_c,
        "pat_d": pat_d,
        "doctor_a_token": seeded_data["doctor_token"],
        "doctor_b_token": create_access_token(doctor_b.id, extra_claims={"email": doctor_b.email}),
        "dmo_token": create_access_token(dmo_user.id, extra_claims={"email": dmo_user.email}),
        "shd_token": create_access_token(shd_user.id, extra_claims={"email": shd_user.email}),
        "patient_a_token": create_access_token(patient_user_a.id, extra_claims={"email": patient_user_a.email}),
        "patient_b_token": create_access_token(patient_user_b.id, extra_claims={"email": patient_user_b.email}),
        "lab_tech_token": create_access_token(lab_tech_user.id, extra_claims={"email": lab_tech_user.email}),
    }


# ============================================================================
# 1. SCOPE AUTHORIZATION & CROSS-FACILITY ACCESS CONTROL
# ============================================================================

@pytest.mark.asyncio
async def test_cross_facility_access_denied_for_facility_scope(async_client: AsyncClient, security_test_env):
    """Clinician with FACILITY scope at Facility A cannot access patient belonging to Facility B."""
    doc_a_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    pat_b_id = str(security_test_env["pat_b"].id)

    res = await async_client.get(f"/api/v1/patients/{pat_b_id}", headers=doc_a_headers)
    assert res.status_code == 403
    assert "Cross-facility access denied" in res.json()["detail"]


@pytest.mark.asyncio
async def test_same_facility_access_allowed_for_facility_scope(async_client: AsyncClient, security_test_env):
    """Clinician with FACILITY scope at Facility A can access patient belonging to Facility A."""
    doc_a_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)

    res = await async_client.get(f"/api/v1/patients/{pat_a_id}", headers=doc_a_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == pat_a_id


@pytest.mark.asyncio
async def test_district_scope_hierarchical_access(async_client: AsyncClient, security_test_env):
    """
    District Officer (Chengalpattu) can access facilities in Chengalpattu (Facility A and B),
    but is DENIED access to Facility C (Kanchipuram district).
    """
    dmo_headers = {"Authorization": f"Bearer {security_test_env['dmo_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)
    pat_b_id = str(security_test_env["pat_b"].id)
    pat_c_id = str(security_test_env["pat_c"].id)

    # 1. Access Facility A (Same District) -> 200 OK
    res_a = await async_client.get(f"/api/v1/patients/{pat_a_id}", headers=dmo_headers)
    assert res_a.status_code == 200

    # 2. Access Facility B (Same District) -> 200 OK
    res_b = await async_client.get(f"/api/v1/patients/{pat_b_id}", headers=dmo_headers)
    assert res_b.status_code == 200

    # 3. Access Facility C (Different District) -> 403 Forbidden
    res_c = await async_client.get(f"/api/v1/patients/{pat_c_id}", headers=dmo_headers)
    assert res_c.status_code == 403
    assert "District scope denied" in res_c.json()["detail"]


@pytest.mark.asyncio
async def test_state_scope_hierarchical_access(async_client: AsyncClient, security_test_env):
    """
    State Officer (Tamil Nadu) can access facilities across all districts of Tamil Nadu (A, B, C),
    but is DENIED access to Facility D (Kerala state).
    """
    shd_headers = {"Authorization": f"Bearer {security_test_env['shd_token']}"}
    pat_c_id = str(security_test_env["pat_c"].id)
    pat_d_id = str(security_test_env["pat_d"].id)

    # 1. Facility C in Tamil Nadu -> 200 OK
    res_c = await async_client.get(f"/api/v1/patients/{pat_c_id}", headers=shd_headers)
    assert res_c.status_code == 200

    # 2. Facility D in Kerala -> 403 Forbidden
    res_d = await async_client.get(f"/api/v1/patients/{pat_d_id}", headers=shd_headers)
    assert res_d.status_code == 403
    assert "State scope denied" in res_d.json()["detail"]


# ============================================================================
# 2. SELF SCOPE & IDOR PREVENTIONS
# ============================================================================

@pytest.mark.asyncio
async def test_citizen_self_access_and_idor_prevention(async_client: AsyncClient, security_test_env):
    """Patient can view own profile and records, but is blocked from another patient's data (IDOR)."""
    patient_a_headers = {"Authorization": f"Bearer {security_test_env['patient_a_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)
    pat_b_id = str(security_test_env["pat_b"].id)

    # 1. Citizen A views own profile -> ALLOW
    res_own = await async_client.get(f"/api/v1/patients/{pat_a_id}", headers=patient_a_headers)
    assert res_own.status_code == 200
    assert res_own.json()["data"]["id"] == pat_a_id

    # 2. Citizen A views own clinical history -> ALLOW
    res_own_history = await async_client.get(f"/api/v1/patients/{pat_a_id}/clinical-history", headers=patient_a_headers)
    assert res_own_history.status_code == 200

    # 3. IDOR Attack: Citizen A attempts to view Citizen B profile -> 403 FORBIDDEN
    res_idor_profile = await async_client.get(f"/api/v1/patients/{pat_b_id}", headers=patient_a_headers)
    assert res_idor_profile.status_code == 403
    assert "Access denied" in res_idor_profile.json()["detail"]

    # 4. IDOR Attack: Citizen A attempts to view Citizen B clinical history -> 403 FORBIDDEN
    res_idor_history = await async_client.get(f"/api/v1/patients/{pat_b_id}/clinical-history", headers=patient_a_headers)
    assert res_idor_history.status_code == 403


# ============================================================================
# 3. USER ≠ PATIENT ARCHITECTURE (CASE A & CASE B)
# ============================================================================

@pytest.mark.asyncio
async def test_user_patient_separation_cases(async_client: AsyncClient, security_test_env):
    """
    Case A: Walk-in patient without User account exists seamlessly.
    Case B: Citizen portal patient with linked User account.
    """
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    fac_a_id = str(security_test_env["fac_a"].id)

    # Case A: Walk-in patient (user_id is None)
    res_a = await async_client.post(
        "/api/v1/patients",
        json={
            "first_name": "Walkin",
            "last_name": "Citizen",
            "date_of_birth": "1960-04-10",
            "gender": "MALE",
            "phone_number": "+919840199999",
            "primary_facility_id": fac_a_id,
            "user_id": None,
        },
        headers=doc_headers,
    )
    assert res_a.status_code == 201
    walkin_patient = res_a.json()["data"]
    assert walkin_patient["first_name"] == "Walkin"

    # Case B: Linked citizen portal patient
    dummy_user_id = str(uuid.uuid4())
    res_b = await async_client.post(
        "/api/v1/patients",
        json={
            "first_name": "Portal",
            "last_name": "Citizen",
            "date_of_birth": "1994-07-22",
            "gender": "FEMALE",
            "phone_number": "+919840288888",
            "primary_facility_id": fac_a_id,
            "user_id": dummy_user_id,
        },
        headers=doc_headers,
    )
    assert res_b.status_code == 201
    portal_patient = res_b.json()["data"]
    assert portal_patient["first_name"] == "Portal"


# ============================================================================
# 4. CLINICAL IMMUTABILITY & AMENDMENT LEDGER
# ============================================================================

@pytest.mark.asyncio
async def test_clinical_encounter_immutability_and_amendments(async_client: AsyncClient, security_test_env):
    """Finalized consultations cannot be mutated, but accept structured clinical amendments."""
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)

    # 1. Start consultation with vitals
    start_res = await async_client.post(
        "/api/v1/consultations",
        json={
            "patient_id": pat_a_id,
            "chief_complaint": "Acute persistent migraine",
            "triage_vitals": {
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "pulse_rate": 72,
                "temperature_celsius": 37.0,
                "spo2_percent": 99,
            },
        },
        headers=doc_headers,
    )
    assert start_res.status_code == 201
    consult_id = start_res.json()["data"]["id"]

    # 2. Record second vitals reading into ledger
    vitals_res = await async_client.post(
        f"/api/v1/consultations/{consult_id}/vitals",
        json={
            "systolic_bp": 118,
            "diastolic_bp": 78,
            "pulse_rate": 70,
            "spo2_percent": 99,
        },
        headers=doc_headers,
    )
    assert vitals_res.status_code == 201
    assert vitals_res.json()["data"]["systolic_bp"] == 118

    # 3. Finalize consultation
    final_res = await async_client.post(
        f"/api/v1/consultations/{consult_id}/finalize",
        json={
            "clinical_notes": "Patient advised rest in dark room and hydration.",
            "diagnoses": [
                {
                    "icd10_code": "G43.9",
                    "condition_name": "Migraine, unspecified",
                    "diagnosis_type": "PRIMARY",
                }
            ],
        },
        headers=doc_headers,
    )
    assert final_res.status_code == 200
    assert final_res.json()["data"]["status"] == "FINALIZED"

    # 4. Attempt to finalize again -> 400 Bad Request
    refinalize_res = await async_client.post(
        f"/api/v1/consultations/{consult_id}/finalize",
        json={"clinical_notes": "Attempted rewrite"},
        headers=doc_headers,
    )
    assert refinalize_res.status_code == 400
    assert "Cannot finalize consultation in status 'FINALIZED'" in refinalize_res.json()["detail"]

    # 5. Attach legitimate clinical amendment
    amend_payload = {
        "amendment_reason": "Follow-up neurology consultation addendum",
        "amendment_notes": "Patient reported family history of hemiplegic migraine. Advised MRI if symptoms recur.",
    }
    amend_res = await async_client.post(
        f"/api/v1/consultations/{consult_id}/amendments",
        json=amend_payload,
        headers=doc_headers,
    )
    assert amend_res.status_code == 201
    amendment = amend_res.json()["data"]
    assert amendment["amendment_reason"] == amend_payload["amendment_reason"]

    # 6. Verify consultation contains original notes and amendment
    consult_detail = await async_client.get(f"/api/v1/consultations/{consult_id}", headers=doc_headers)
    assert consult_detail.status_code == 200
    data = consult_detail.json()["data"]
    assert data["clinical_notes"] == "Patient advised rest in dark room and hydration."
    assert len(data["amendments"]) == 1
    assert len(data["vitals_records"]) >= 1


# ============================================================================
# 5. PRESCRIPTION DISPENSING QUANTITY INTEGRITY
# ============================================================================

@pytest.mark.asyncio
async def test_prescription_dispensing_boundary_and_overdispensing_protection(async_client: AsyncClient, security_test_env):
    """Prescription dispensing strictly enforces quantity caps and terminal states."""
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)

    # 1. Start consultation
    c_res = await async_client.post(
        "/api/v1/consultations",
        json={"patient_id": pat_a_id, "chief_complaint": "Bacterial pharyngitis"},
        headers=doc_headers,
    )
    consult_id = c_res.json()["data"]["id"]

    # 2. Issue prescription for 10 tablets
    rx_res = await async_client.post(
        "/api/v1/prescriptions",
        json={
            "consultation_id": consult_id,
            "items": [
                {
                    "medication_name": "Azithromycin 500mg",
                    "dosage": "500mg",
                    "frequency": "OD",
                    "duration_days": 3,
                    "quantity_prescribed": 10,
                }
            ],
        },
        headers=doc_headers,
    )
    assert rx_res.status_code == 201
    rx = rx_res.json()["data"]
    rx_id = rx["id"]
    item_id = rx["items"][0]["id"]

    # 3. Malicious attempt to over-dispense 15 units (prescribed only 10) -> 400 Bad Request
    overdispense_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"dispensed_items": {item_id: 15}},
        headers=doc_headers,
    )
    assert overdispense_res.status_code == 400
    assert "Remaining prescribed quantity is 10" in overdispense_res.json()["detail"]

    # 4. Partial dispense: 6 units -> 200 OK (PARTIALLY_DISPENSED)
    partial_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"dispensed_items": {item_id: 6}},
        headers=doc_headers,
    )
    assert partial_res.status_code == 200
    assert partial_res.json()["data"]["status"] == "PARTIALLY_DISPENSED"

    # 5. Attempt to dispense 5 more (only 4 remain) -> 400 Bad Request
    over_partial_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"dispensed_items": {item_id: 5}},
        headers=doc_headers,
    )
    assert over_partial_res.status_code == 400
    assert "Remaining prescribed quantity is 4" in over_partial_res.json()["detail"]

    # 6. Complete remaining 4 units -> 200 OK (COMPLETED)
    complete_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"dispensed_items": {item_id: 4}},
        headers=doc_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["data"]["status"] == "COMPLETED"

    # 7. Attempt to dispense on COMPLETED prescription -> 400 Bad Request
    terminal_res = await async_client.post(
        f"/api/v1/prescriptions/{rx_id}/dispense",
        json={"dispensed_items": {item_id: 1}},
        headers=doc_headers,
    )
    assert terminal_res.status_code == 400
    assert "Cannot dispense prescription in status 'COMPLETED'" in terminal_res.json()["detail"]


# ============================================================================
# 6. STATE MACHINE TERMINAL-STATE PROTECTION
# ============================================================================

@pytest.mark.asyncio
async def test_appointment_state_machine_terminal_protection(async_client: AsyncClient, security_test_env):
    """Terminal appointment states (COMPLETED, CANCELLED, NO_SHOW) cannot be reopened or mutated."""
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)
    fac_a_id = str(security_test_env["fac_a"].id)

    # 1. Schedule appointment
    appt_res = await async_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": pat_a_id,
            "facility_id": fac_a_id,
            "appointment_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "reason": "Routine hypertension review",
        },
        headers=doc_headers,
    )
    appt_id = appt_res.json()["data"]["id"]

    # 2. Cancel appointment -> Status: CANCELLED
    cancel_res = await async_client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "CANCELLED", "cancellation_reason": "Patient requested cancellation"},
        headers=doc_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"

    # 3. Attempt to transition CANCELLED -> CHECKED_IN -> 400 Bad Request
    illegal_res = await async_client.patch(
        f"/api/v1/appointments/{appt_id}/status",
        json={"status": "CHECKED_IN"},
        headers=doc_headers,
    )
    assert illegal_res.status_code == 400
    assert "Cannot change status of an appointment that is in terminal status 'CANCELLED'" in illegal_res.json()["detail"]


# ============================================================================
# 7. LAB SEPARATION OF DUTIES & TERMINAL VERIFICATION
# ============================================================================

@pytest.mark.asyncio
async def test_lab_separation_of_duties_and_terminal_verification(async_client: AsyncClient, security_test_env):
    """
    Enforces separation of duties:
    - Technician can enter results, but cannot verify.
    - Clinician verifies findings.
    - Verified lab order cannot be modified.
    """
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    tech_headers = {"Authorization": f"Bearer {security_test_env['lab_tech_token']}"}
    pat_a_id = str(security_test_env["pat_a"].id)

    # 1. Create encounter and lab order
    c_res = await async_client.post(
        "/api/v1/consultations",
        json={"patient_id": pat_a_id, "chief_complaint": "Suspected dengue fever"},
        headers=doc_headers,
    )
    consult_id = c_res.json()["data"]["id"]

    order_res = await async_client.post(
        "/api/v1/labs/orders",
        json={"consultation_id": consult_id, "test_category": "SEROLOGY"},
        headers=doc_headers,
    )
    order_id = order_res.json()["data"]["id"]

    # 2. Technician adds result -> ALLOW
    result_res = await async_client.post(
        f"/api/v1/labs/orders/{order_id}/results",
        json={"test_name": "Dengue NS1 Antigen", "result_value": "NEGATIVE"},
        headers=tech_headers,
    )
    assert result_res.status_code == 201

    # 3. Technician attempts to verify order -> 403 Forbidden
    tech_verify_res = await async_client.post(f"/api/v1/labs/orders/{order_id}/verify", headers=tech_headers)
    assert tech_verify_res.status_code == 403

    # 4. Doctor verifies order -> 200 OK
    doc_verify_res = await async_client.post(f"/api/v1/labs/orders/{order_id}/verify", headers=doc_headers)
    assert doc_verify_res.status_code == 200
    assert doc_verify_res.json()["data"]["status"] == "COMPLETED"

    # 5. Attempting to add results to already completed order -> 400 Bad Request
    post_verify_res = await async_client.post(
        f"/api/v1/labs/orders/{order_id}/results",
        json={"test_name": "IgM Antibody", "result_value": "NEGATIVE"},
        headers=tech_headers,
    )
    assert post_verify_res.status_code == 400
    assert "Cannot add results to a lab order in status 'COMPLETED'" in post_verify_res.json()["detail"]


# ============================================================================
# 8. AUDIT LOG IMMUTABILITY ENFORCEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_audit_log_strict_immutability(db_session):
    """AuditLog rows reject all in-place UPDATE and DELETE mutations via SQLAlchemy event hooks."""
    log = AuditLog(
        id=uuid.uuid4(),
        action="SECURITY_AUDIT_TEST",
        resource_type="system",
        resource_id="123",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(log)
    await db_session.flush()

    # 1. Attempt UPDATE on AuditLog -> Must raise RuntimeError
    log.action = "TAMPERED_ACTION"
    with pytest.raises(RuntimeError, match="Audit logs are strictly immutable and cannot be modified"):
        await db_session.flush()

    await db_session.rollback()

    # 2. Re-create and attempt DELETE on AuditLog -> Must raise RuntimeError
    log2 = AuditLog(
        id=uuid.uuid4(),
        action="SECURITY_AUDIT_TEST_2",
        resource_type="system",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(log2)
    await db_session.flush()

    await db_session.delete(log2)
    with pytest.raises(RuntimeError, match="Audit logs are strictly immutable and cannot be deleted"):
        await db_session.flush()

    await db_session.rollback()


# ============================================================================
# 9. MASS ASSIGNMENT & MALICIOUS INPUT VALIDATION
# ============================================================================

@pytest.mark.asyncio
async def test_mass_assignment_and_payload_protection(async_client: AsyncClient, security_test_env):
    """Pydantic extra='forbid' strictly rejects unknown or privilege-escalation fields."""
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    fac_a_id = str(security_test_env["fac_a"].id)

    # Malicious payload with injected privilege escalation attributes
    malicious_payload = {
        "first_name": "Injected",
        "last_name": "Attacker",
        "date_of_birth": "1990-01-01",
        "gender": "MALE",
        "phone_number": "+919999900000",
        "primary_facility_id": fac_a_id,
        "is_superuser": True,
        "role": "SUPER_ADMIN",
        "role_id": str(uuid.uuid4()),
        "scope": "GLOBAL",
    }
    res = await async_client.post("/api/v1/patients", json=malicious_payload, headers=doc_headers)
    assert res.status_code == 422
    errors = res.json().get("invalid_params", res.json().get("detail", []))
    assert any("Extra inputs are not permitted" in str(e) or "extra_forbidden" in str(e) for e in errors)


# ============================================================================
# 10. CONCURRENCY: 100 CONCURRENT PATIENT REGISTRATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_100_patient_registrations(async_client: AsyncClient, security_test_env):
    """
    100 simultaneous concurrent patient registrations:
    - Zero duplicate patient identifiers
    - Zero transaction corruption
    - All registrations successfully return unique PAT-YYYYMM-XXXXXX
    """
    doc_headers = {"Authorization": f"Bearer {security_test_env['doctor_a_token']}"}
    fac_a_id = str(security_test_env["fac_a"].id)

    async def register_single(idx: int):
        payload = {
            "first_name": f"Concurrent{idx}",
            "last_name": "Tester",
            "date_of_birth": "1985-05-15",
            "gender": "OTHER",
            "phone_number": f"+919884{idx:06d}",
            "primary_facility_id": fac_a_id,
        }
        res = await async_client.post("/api/v1/patients", json=payload, headers=doc_headers)
        return res

    tasks = [register_single(i) for i in range(100)]
    responses = await asyncio.gather(*tasks)

    for r in responses:
        assert r.status_code == 201, f"Failed registration: {r.text}"

    identifiers = [r.json()["data"]["patient_identifier"] for r in responses]
    assert len(identifiers) == 100
    assert len(set(identifiers)) == 100, "Duplicate patient identifier detected under concurrency!"
