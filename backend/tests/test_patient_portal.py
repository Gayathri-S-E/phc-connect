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
    ComplaintStatus,
    Consultation,
    ConsultationStatus,
    FeedbackComplaint,
    HealthAwarenessSlide,
    Patient,
    PatientNotification,
    Prescription,
    PrescriptionItem,
    PrescriptionItemStatus,
    PrescriptionStatus,
)
from app.models.identity import Role, RolePermission, ScopeLevel, User, UserRole


@pytest_asyncio.fixture
async def patient_portal_fixtures(db_session, seeded_data):
    """Seed patient user, role, doctor user, awareness slides, and notification data."""
    org = seeded_data["org"]
    fac = seeded_data["facility"]
    doctor_user = seeded_data["doctor_user"]

    # 1. Create Patient Role & map permissions
    patient_role = Role(
        id=uuid.uuid4(),
        name="Citizen / Patient",
        code="PATIENT",
        is_system=True,
        is_active=True,
    )
    db_session.add(patient_role)
    await db_session.flush()

    from app.repositories.role_repository import RoleRepository
    role_repo = RoleRepository(db_session)
    all_perms = await role_repo.list_permissions()
    perm_by_code = {p.code: p for p in all_perms}

    patient_perm_codes = [
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.PATIENTS_PROFILE_UPDATE,
        SystemPermissions.PATIENTS_RECORDS_READ,
        SystemPermissions.APPOINTMENTS_VIEW,
        SystemPermissions.APPOINTMENTS_MANAGE,
        SystemPermissions.PRESCRIPTIONS_READ,
        SystemPermissions.PATIENTS_FEEDBACK_SUBMIT,
        SystemPermissions.PATIENTS_FEEDBACK_READ,
        SystemPermissions.PATIENTS_AWARENESS_READ,
        SystemPermissions.PATIENTS_AI_WELLNESS_CHAT,
        SystemPermissions.PATIENTS_NOTIFICATIONS_READ,
    ]
    for code in patient_perm_codes:
        if code in perm_by_code:
            db_session.add(RolePermission(role_id=patient_role.id, permission_id=perm_by_code[code].id))
    await db_session.flush()

    # 2. Patient User
    patient_user = User(
        id=uuid.uuid4(),
        email="patient@test.gov.in",
        phone_number="+919876543210",
        hashed_password=get_password_hash("PatientPass123!"),
        full_name="Kavitha Raman",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(patient_user)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=patient_user.id,
            role_id=patient_role.id,
            organization_id=org.id,
            facility_id=fac.id,
            scope_level=ScopeLevel.SELF,
        )
    )

    # 3. Patient Entity
    patient = Patient(
        id=uuid.uuid4(),
        user_id=patient_user.id,
        primary_facility_id=fac.id,
        patient_identifier="PHC-KOV-2026-9999",
        first_name="Kavitha",
        last_name="Raman",
        date_of_birth=date(1992, 5, 14),
        gender="FEMALE",
        phone_number="+919876543210",
        address="12 South Mada Street, Kovalam",
        blood_group="B+",
        preferred_language="ta",
        chronic_conditions="HYPERTENSION",
        allergies="Penicillin",
        is_active=True,
    )
    db_session.add(patient)

    # 4. Awareness Slides
    slide = HealthAwarenessSlide(
        id=uuid.uuid4(),
        category="PREVENTIVE_HEALTH",
        title_en="Stay Hydrated and Beat the Heat",
        title_ta="நீரேற்றமாக இருங்கள் - கோடை வெப்பத்தை வெல்லுங்கள்",
        tip_en="Drink at least 8 glasses of boiled water daily.",
        tip_ta="தினமும் குறைந்தது 8 டம்ளர் காய்ச்சிய நீரைக் குடியுங்கள்.",
        motivation_en="Prevention is the foundation of good health.",
        motivation_ta="நோயற்ற வாழ்வே குறைவற்ற செல்வம்.",
        action_en="Visit your local PHC for free health checkups.",
        action_ta="இலவச மருத்துவ பரிசோதனைக்கு உங்கள் ஆரம்ப சுகாதார நிலையத்தை அணுகவும்.",
        display_order=1,
        is_active=True,
    )
    db_session.add(slide)

    # 5. Patient Notification
    notif = PatientNotification(
        id=uuid.uuid4(),
        patient_id=patient.id,
        title_en="Appointment Reminder",
        title_ta="மருத்துவ சந்திப்பு நினைவூட்டல்",
        message_en="Your appointment at Kovalam PHC is confirmed.",
        message_ta="கோவளம் ஆரம்ப சுகாதார நிலையத்தில் உங்கள் சந்திப்பு உறுதி செய்யப்பட்டது.",
        notification_type="APPOINTMENT",
        is_read=False,
    )
    db_session.add(notif)

    # 6. Clinical Data (Consultation, Prescription, PrescriptionItem)
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient.id,
        doctor_id=doctor_user.id,
        facility_id=fac.id,
        started_at=datetime.now(timezone.utc) - timedelta(days=2),
        finalized_at=datetime.now(timezone.utc) - timedelta(days=2) + timedelta(minutes=15),
        status=ConsultationStatus.FINALIZED,
        chief_complaint="Occasional mild headaches",
        clinical_notes="Blood pressure slightly elevated 135/85.",
    )
    db_session.add(consultation)

    prescription = Prescription(
        id=uuid.uuid4(),
        consultation_id=consultation.id,
        patient_id=patient.id,
        doctor_id=doctor_user.id,
        facility_id=fac.id,
        status=PrescriptionStatus.ISSUED,
        notes="Take after food",
    )
    db_session.add(prescription)

    med_item = PrescriptionItem(
        id=uuid.uuid4(),
        prescription_id=prescription.id,
        medication_name="Amlodipine 5mg",
        dosage="5mg",
        frequency="ONCE_DAILY",
        duration_days=30,
        instructions="Morning after breakfast",
        quantity_prescribed=30,
        quantity_dispensed=0,
        status=PrescriptionItemStatus.PENDING,
    )
    db_session.add(med_item)

    await db_session.commit()

    patient_token = create_access_token(patient_user.id, extra_claims={"email": patient_user.email})

    return {
        "patient_user": patient_user,
        "patient": patient,
        "patient_token": patient_token,
        "doctor_user": doctor_user,
        "facility": fac,
        "org": org,
        "slide": slide,
        "notification": notif,
    }


@pytest.mark.asyncio
async def test_get_and_update_patient_profile(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get profile
    res = await async_client.get("/api/v1/patients/me", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["first_name"] == "Kavitha"
    assert data["patient_identifier"] == "PHC-KOV-2026-9999"
    assert data["preferred_language"] == "ta"
    assert "HYPERTENSION" in (data["chronic_conditions"] or "")

    # 2. Update profile
    update_payload = {
        "phone_number": "+919876543299",
        "address": "45 Temple Road, Kovalam",
        "preferred_language": "en",
        "chronic_conditions": "HYPERTENSION, DIABETES_MELLITUS_TYPE_2",
        "allergies": "Penicillin, Sulfa",
    }
    res_up = await async_client.patch("/api/v1/patients/me", headers=headers, json=update_payload)
    assert res_up.status_code == 200, res_up.text
    updated = res_up.json()["data"]
    assert updated["preferred_language"] == "en"
    assert "DIABETES_MELLITUS_TYPE_2" in updated["chronic_conditions"]
    assert "Sulfa" in updated["allergies"]


@pytest.mark.asyncio
async def test_sequential_appointment_booking_and_cancellation(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    patient = patient_portal_fixtures["patient"]
    facility = patient_portal_fixtures["facility"]
    doctor_user = patient_portal_fixtures["doctor_user"]
    headers = {"Authorization": f"Bearer {token}"}

    target_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # 1. Book first appointment (should get token 501)
    booking_1 = {
        "patient_id": str(patient.id),
        "facility_id": str(facility.id),
        "doctor_id": str(doctor_user.id),
        "appointment_date": target_date,
        "time_slot": "09:00-09:30",
        "reason": "Routine checkup",
        "priority": "ROUTINE",
    }
    res_1 = await async_client.post("/api/v1/patients/me/appointments", headers=headers, json=booking_1)
    assert res_1.status_code == 201, res_1.text
    appt1 = res_1.json()["data"]
    assert appt1["token_number"] == 501
    assert appt1["status"] == "SCHEDULED"

    # 2. Book second appointment on same day (should get token 502)
    booking_2 = {
        "patient_id": str(patient.id),
        "facility_id": str(facility.id),
        "doctor_id": str(doctor_user.id),
        "appointment_date": target_date,
        "time_slot": "09:30-10:00",
        "reason": "Follow up consult",
        "priority": "ROUTINE",
    }
    res_2 = await async_client.post("/api/v1/patients/me/appointments", headers=headers, json=booking_2)
    assert res_2.status_code == 201, res_2.text
    appt2 = res_2.json()["data"]
    assert appt2["token_number"] == 502

    # 3. List patient appointments
    res_list = await async_client.get("/api/v1/patients/me/appointments", headers=headers)
    assert res_list.status_code == 200
    appts = res_list.json()["data"]
    assert len(appts) >= 2

    # 4. Cancel appointment 1
    cancel_res = await async_client.patch(
        f"/api/v1/patients/me/appointments/{appt1['id']}/cancel?cancellation_reason=Unable%20to%20attend",
        headers=headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_patient_medical_records_and_safe_prescriptions(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Medical records list (clinical history)
    res_records = await async_client.get("/api/v1/patients/me/records", headers=headers)
    assert res_records.status_code == 200, res_records.text
    history = res_records.json()["data"]
    assert "patient" in history
    assert "consultations" in history
    assert len(history["consultations"]) >= 1

    # 2. Prescriptions with safe fulfillment
    res_rx = await async_client.get("/api/v1/patients/me/prescriptions", headers=headers)
    assert res_rx.status_code == 200, res_rx.text
    rx_list = res_rx.json()["data"]
    assert len(rx_list) >= 1
    rx = rx_list[0]
    assert "overall_status" in rx
    assert len(rx["items"]) >= 1
    med = rx["items"][0]
    assert med["medication_name"] == "Amlodipine 5mg"
    assert med["fulfillment_status"] in ["PROCESSING", "READY_FOR_COLLECTION", "PARTIALLY_AVAILABLE", "TEMPORARILY_UNAVAILABLE", "COLLECTED"]
    # Ensure no internal inventory batch/stock leakage in response
    assert "batch_number" not in med
    assert "stock_level" not in med


@pytest.mark.asyncio
async def test_patient_feedback_and_grievance_tracking(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    facility = patient_portal_fixtures["facility"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Submit feedback
    payload = {
        "facility_id": str(facility.id),
        "category": "FACILITY",
        "subject": "Drinking water facility",
        "description": "Drinking water filter was clean and working properly.",
    }
    res = await async_client.post("/api/v1/patients/me/feedback", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    feedback = res.json()["data"]
    assert feedback["tracking_number"].startswith("CMP-")
    assert feedback["status"] == "SUBMITTED"

    # 2. List submitted feedback
    res_list = await async_client.get("/api/v1/patients/me/feedback", headers=headers)
    assert res_list.status_code == 200
    items = res_list.json()["data"]
    assert len(items) >= 1
    assert items[0]["tracking_number"] == feedback["tracking_number"]


@pytest.mark.asyncio
async def test_patient_notifications_and_awareness(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Notifications
    res_notif = await async_client.get("/api/v1/patients/me/notifications", headers=headers)
    assert res_notif.status_code == 200, res_notif.text
    notifs = res_notif.json()["data"]
    assert len(notifs) >= 1
    notif_id = notifs[0]["id"]
    assert notifs[0]["title_ta"] == "மருத்துவ சந்திப்பு நினைவூட்டல்"
    assert notifs[0]["is_read"] is False

    # Mark as read
    res_read = await async_client.patch(f"/api/v1/patients/me/notifications/{notif_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["data"]["is_read"] is True

    # 2. Awareness Slides
    res_slides = await async_client.get("/api/v1/patients/awareness-slides", headers=headers)
    assert res_slides.status_code == 200, res_slides.text
    slides = res_slides.json()["data"]
    assert len(slides) >= 1
    assert slides[0]["category"] == "PREVENTIVE_HEALTH"
    assert slides[0]["title_ta"] == "நீரேற்றமாக இருங்கள் - கோடை வெப்பத்தை வெல்லுங்கள்"


@pytest.mark.asyncio
async def test_patient_wellness_ai_assistant(async_client: AsyncClient, patient_portal_fixtures):
    token = patient_portal_fixtures["patient_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Routine wellness query in English
    chat_payload = {
        "message": "What should I eat to keep my blood pressure healthy?",
        "language": "en",
    }
    res = await async_client.post("/api/v1/patients/wellness-assistant/chat", headers=headers, json=chat_payload)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["is_emergency_warning"] is False
    assert len(data["reply"]) > 10

    # 2. Emergency red flag triage query
    emergency_payload = {
        "message": "I have severe sudden chest pain and shortness of breath",
        "language": "en",
    }
    res_em = await async_client.post("/api/v1/patients/wellness-assistant/chat", headers=headers, json=emergency_payload)
    assert res_em.status_code == 200, res_em.text
    data_em = res_em.json()["data"]
    assert data_em["is_emergency_warning"] is True
    assert "108" in data_em["reply"] or "emergency" in data_em["reply"].lower() or "phc" in data_em["reply"].lower()

    # 3. Tamil emergency query
    emergency_ta = {
        "message": "கடுமையான நெஞ்சு வலி மற்றும் மூச்சுத் திணறல்",
        "language": "ta",
    }
    res_ta = await async_client.post("/api/v1/patients/wellness-assistant/chat", headers=headers, json=emergency_ta)
    assert res_ta.status_code == 200, res_ta.text
    data_ta = res_ta.json()["data"]
    assert data_ta["is_emergency_warning"] is True
    assert "108" in data_ta["reply"] or "அவசர" in data_ta["reply"]
