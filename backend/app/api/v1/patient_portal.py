import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
)
from app.core.exceptions import BadRequestException, PermissionDeniedException, ResourceNotFoundException
from app.models.healthcare import AppointmentStatus
from app.schemas.common import DataResponse
from app.schemas.healthcare import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    ClinicalHistoryResponse,
    FeedbackComplaintCreate,
    FeedbackComplaintResponse,
    HealthAwarenessSlideResponse,
    PatientNotificationResponse,
    PatientPrescriptionFulfillmentResponse,
    PatientResponse,
    PatientUpdate,
    PatientWellnessChatRequest,
    PatientWellnessChatResponse,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(prefix="/patients", tags=["Patient Portal (Role 01)"])


async def _get_authenticated_patient(
    current_user: AuthenticatedUserContext, service: HealthcareService
):
    patient = await service.get_patient_by_user_id(current_user.id)
    if not patient:
        raise ResourceNotFoundException("Patient profile for authenticated user")
    return patient


# ============================================================================
# 1. PROFILE & PREFERENCES
# ============================================================================

@router.get("/me", response_model=DataResponse[PatientResponse])
async def get_my_patient_profile(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve personal health profile for authenticated citizen/patient."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    return DataResponse(data=PatientResponse.model_validate(patient))


@router.patch("/me", response_model=DataResponse[PatientResponse])
async def update_my_patient_profile(
    payload: PatientUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update personal profile, language preference, emergency contacts, or voluntary health indicators."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    updated = await service.update_patient(
        patient.id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PatientResponse.model_validate(updated))


# ============================================================================
# 2. APPOINTMENTS & SEQUENTIAL TOKEN SCHEDULING
# ============================================================================

@router.get("/me/appointments", response_model=DataResponse[List[AppointmentResponse]])
async def list_my_appointments(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List upcoming and past appointments for authenticated patient."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    appointments, _ = await service.list_appointments(patient_id=patient.id, page_size=100)
    return DataResponse(data=[AppointmentResponse.model_validate(a) for a in appointments])


@router.post(
    "/me/appointments",
    response_model=DataResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def book_my_appointment(
    payload: AppointmentCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Book a new PHC appointment with deterministic sequential token (e.g. 501, 502...)."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)

    # Force patient_id to match authenticated patient to prevent IDOR
    if payload.patient_id != patient.id:
        payload.patient_id = patient.id

    appointment = await service.create_appointment(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=AppointmentResponse.model_validate(appointment))


@router.patch(
    "/me/appointments/{appointment_id}/cancel",
    response_model=DataResponse[AppointmentResponse],
)
async def cancel_my_appointment(
    appointment_id: uuid.UUID,
    cancellation_reason: Optional[str] = Query(default="Cancelled by patient"),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Cancel an appointment owned by the authenticated patient."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    appt = await service.repo.get_appointment_by_id(appointment_id)
    if not appt or appt.patient_id != patient.id:
        raise ResourceNotFoundException("Appointment", str(appointment_id))

    updated = await service.update_appointment_status(
        appointment_id,
        AppointmentStatusUpdate(
            status=AppointmentStatus.CANCELLED,
            cancellation_reason=cancellation_reason,
        ),
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=AppointmentResponse.model_validate(updated))


# ============================================================================
# 3. HEALTH RECORDS & LONGITUDINAL HISTORY
# ============================================================================

@router.get("/me/records", response_model=DataResponse[ClinicalHistoryResponse])
async def get_my_health_records(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve full longitudinal consultation history, lab results, diagnoses, and vitals."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    history = await service.get_patient_clinical_history(patient.id)
    return DataResponse(data=history)


# ============================================================================
# 4. PRESCRIPTIONS & SAFE MEDICINE FULFILLMENT STATUS
# ============================================================================

@router.get(
    "/me/prescriptions",
    response_model=DataResponse[List[PatientPrescriptionFulfillmentResponse]],
)
async def get_my_prescriptions(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve own prescriptions with patient-facing fulfillment status.
    STRICT PRIVACY: Zero warehouse quantities, batch numbers, or internal stock ledgers exposed.
    """
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    prescriptions = await service.get_patient_prescriptions_fulfillment(patient.id)
    return DataResponse(data=prescriptions)


# ============================================================================
# 5. FEEDBACK & COMPLAINTS
# ============================================================================

@router.post(
    "/me/feedback",
    response_model=DataResponse[FeedbackComplaintResponse],
    status_code=status.HTTP_201_CREATED,
)
async def submit_patient_feedback(
    payload: FeedbackComplaintCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Submit a healthcare service feedback or grievance and receive a tracking reference code."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    complaint = await service.submit_feedback_complaint(
        patient_id=patient.id,
        data=payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=FeedbackComplaintResponse.model_validate(complaint))


@router.get(
    "/me/feedback",
    response_model=DataResponse[List[FeedbackComplaintResponse]],
)
async def list_my_feedback(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List grievances and feedback submitted by authenticated patient."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    complaints = await service.list_patient_feedback_complaints(patient.id)
    return DataResponse(data=[FeedbackComplaintResponse.model_validate(c) for c in complaints])


@router.get(
    "/feedback/{tracking_number}",
    response_model=DataResponse[FeedbackComplaintResponse],
)
async def track_feedback_complaint(
    tracking_number: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Track resolution status of a submitted feedback/complaint by its CMP-YYYYMM-XXXXX tracking code."""
    service = HealthcareService(session)
    complaint = await service.get_feedback_complaint_by_tracking(tracking_number)
    return DataResponse(data=FeedbackComplaintResponse.model_validate(complaint))


# ============================================================================
# 6. IN-APP NOTIFICATIONS
# ============================================================================

@router.get(
    "/me/notifications",
    response_model=DataResponse[List[PatientNotificationResponse]],
)
async def list_my_notifications(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve in-app notifications (appointment confirmations, reminders, tips)."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    notifications = await service.list_patient_notifications(patient.id)
    return DataResponse(data=[PatientNotificationResponse.model_validate(n) for n in notifications])


@router.patch(
    "/me/notifications/{notification_id}/read",
    response_model=DataResponse[PatientNotificationResponse],
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark an in-app notification as read."""
    service = HealthcareService(session)
    patient = await _get_authenticated_patient(current_user, service)
    notification = await service.mark_patient_notification_read(notification_id, patient.id)
    return DataResponse(data=PatientNotificationResponse.model_validate(notification))


# ============================================================================
# 7. HEALTH AWARENESS SLIDES (BILINGUAL)
# ============================================================================

@router.get(
    "/awareness-slides",
    response_model=DataResponse[List[HealthAwarenessSlideResponse]],
)
async def list_health_awareness_slides(
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve verified health awareness and motivational cards with English & Tamil content.
    Categories: EXERCISE, NUTRITION, HYDRATION_SLEEP, MENTAL_WELLNESS, HYGIENE, DISEASE_PREVENTION, VACCINATION, WARNING_SIGNS.
    """
    service = HealthcareService(session)
    slides = await service.list_health_awareness_slides(category=category)
    return DataResponse(data=[HealthAwarenessSlideResponse.model_validate(s) for s in slides])


# ============================================================================
# 8. PATIENT AI WELLNESS ASSISTANT (BILINGUAL)
# ============================================================================

@router.post(
    "/wellness-assistant/chat",
    response_model=DataResponse[PatientWellnessChatResponse],
)
async def chat_wellness_assistant(
    payload: PatientWellnessChatRequest,
    current_user: Optional[AuthenticatedUserContext] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Dedicated Patient AI Wellness Assistant (English & Tamil).
    Focuses on healthy lifestyle, nutrition, hydration, sleep, exercise, and PHC guidance.
    Strict medical safety: Emergency red flag detection with immediate 108/hospital advice.
    """
    service = HealthcareService(session)
    patient_id = None
    if current_user:
        patient = await service.repo.get_patient_by_user_id(current_user.id)
        if patient:
            patient_id = patient.id

    lang = payload.language or "en"
    res = await service.chat_with_wellness_assistant(
        message=payload.message,
        language=lang,
        patient_id=patient_id,
    )
    return DataResponse(data=res)
