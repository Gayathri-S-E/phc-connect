import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
    require_permission,
)
from app.core.exceptions import BadRequestException, PermissionDeniedException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.schemas.common import DataResponse
from app.schemas.healthcare import (
    ConsultationCreate,
    ConsultationFinalizeRequest,
    ConsultationResponse,
    DoctorClinicalAdvisoryRequest,
    DoctorClinicalAdvisoryResponse,
    DoctorOPDQueueItem,
    LabOrderCreate,
    LabOrderResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    ReferralCreate,
    ReferralResponse,
    StaffAttendanceCheckIn,
    StaffAttendanceCheckOut,
    StaffAttendanceResponse,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(prefix="/doctor", tags=["Doctor Portal (Role 02 - Medical Officer)"])


# ============================================================================
# 1. STAFF DUTY ATTENDANCE
# ============================================================================

@router.post(
    "/attendance/check-in",
    response_model=DataResponse[StaffAttendanceResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_RECORD))],
)
async def doctor_check_in(
    payload: StaffAttendanceCheckIn,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Record Doctor duty shift check-in."""
    facility_id = payload.facility_id or current_user.user.facility_id
    if not facility_id:
        raise BadRequestException("Facility ID must be provided or linked to user profile.")

    service = HealthcareService(session)
    record = await service.record_staff_check_in(
        user_id=current_user.id,
        facility_id=facility_id,
        shift=payload.shift or "GENERAL",
        notes=payload.notes,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=StaffAttendanceResponse.model_validate(record))


@router.post(
    "/attendance/check-out",
    response_model=DataResponse[StaffAttendanceResponse],
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_RECORD))],
)
async def doctor_check_out(
    payload: StaffAttendanceCheckOut,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Record Doctor duty shift check-out."""
    service = HealthcareService(session)
    record = await service.record_staff_check_out(
        user_id=current_user.id,
        notes=payload.notes,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=StaffAttendanceResponse.model_validate(record))


@router.get(
    "/attendance/today",
    response_model=DataResponse[Optional[StaffAttendanceResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_READ))],
)
async def get_doctor_attendance_today(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve current day duty attendance status."""
    service = HealthcareService(session)
    record = await service.get_staff_attendance_today(current_user.id)
    if not record:
        return DataResponse(data=None)
    return DataResponse(data=StaffAttendanceResponse.model_validate(record))


# ============================================================================
# 2. PRIORITY OPD QUEUE (EMERGENCY -> PRIORITY -> ROUTINE & DETERMINISTIC TOKENS)
# ============================================================================

@router.get(
    "/queue",
    response_model=DataResponse[List[DoctorOPDQueueItem]],
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_VIEW))],
)
async def get_doctor_opd_queue(
    target_date: Optional[date] = Query(None, description="Queue date (defaults to today)"),
    facility_id: Optional[uuid.UUID] = Query(None, description="PHC facility filter"),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get deterministic sequential OPD patient queue sorted strictly by:
    1. EMERGENCY priority
    2. PRIORITY triage acuity
    3. ROUTINE sequential token number (e.g. 501, 502, 503...)
    Includes patient age, demographics, and nurse triage vitals.
    """
    effective_facility_id = facility_id or current_user.user.facility_id
    if not effective_facility_id:
        raise BadRequestException("Facility ID must be provided or linked to user.")

    service = HealthcareService(session)
    queue = await service.get_doctor_opd_queue(
        facility_id=effective_facility_id,
        doctor_id=current_user.id,
        target_date=target_date,
    )
    return DataResponse(data=queue)


# ============================================================================
# 3. CLINICAL ENCOUNTER WORKFLOW
# ============================================================================

@router.post(
    "/consultations",
    response_model=DataResponse[ConsultationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
async def start_doctor_consultation(
    payload: ConsultationCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    service = HealthcareService(session)
    facility_id = current_user.user.facility_id
    if not facility_id and payload.appointment_id:
        appt = await service.repo.get_appointment_by_id(payload.appointment_id)
        if appt:
            facility_id = appt.facility_id
    if not facility_id:
        raise BadRequestException("Facility ID could not be determined.")

    consultation = await service.start_consultation(
        data=payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ConsultationResponse.model_validate(consultation))


@router.post(
    "/consultations/{consultation_id}/finalize",
    response_model=DataResponse[ConsultationResponse],
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
async def finalize_doctor_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationFinalizeRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Finalize clinical encounter with examination notes, ICD-10 diagnoses, and outcome."""
    service = HealthcareService(session)
    consultation = await service.finalize_consultation(
        consultation_id=consultation_id,
        data=payload,
        doctor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ConsultationResponse.model_validate(consultation))


# ============================================================================
# 4. DIRECT PRESCRIPTION TO PHARMACY
# ============================================================================

@router.post(
    "/prescriptions",
    response_model=DataResponse[PrescriptionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_CREATE))],
)
async def create_doctor_prescription(
    payload: PrescriptionCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Issue structured electronic prescription.
    Automatically enters the PHC Pharmacist Dispenser queue for FEFO fulfillment.
    """
    facility_id = current_user.user.facility_id
    if not facility_id:
        consultation = await HealthcareService(session).repo.get_consultation_by_id(payload.consultation_id)
        if consultation:
            facility_id = consultation.facility_id
        else:
            raise BadRequestException("Facility ID could not be resolved from consultation.")

    service = HealthcareService(session)
    rx = await service.create_prescription(
        data=payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PrescriptionResponse.model_validate(rx))


# ============================================================================
# 5. LAB DIAGNOSTICS & REFERRALS
# ============================================================================

@router.post(
    "/labs",
    response_model=DataResponse[LabOrderResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.LABS_ORDER_CREATE))],
)
async def order_doctor_lab_test(
    payload: LabOrderCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Order laboratory diagnostic test (CBC, Blood Sugar, Dengue NS1, Urine Routine, etc.)."""
    facility_id = current_user.user.facility_id
    if not facility_id:
        consultation = await HealthcareService(session).repo.get_consultation_by_id(payload.consultation_id)
        if consultation:
            facility_id = consultation.facility_id
        else:
            raise BadRequestException("Facility ID could not be resolved.")

    service = HealthcareService(session)
    order = await service.create_lab_order(
        data=payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=LabOrderResponse.model_validate(order))


@router.post(
    "/referrals",
    response_model=DataResponse[ReferralResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.REFERRALS_CREATE))],
)
async def create_doctor_referral(
    payload: ReferralCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Create referral to higher secondary/tertiary hospital (ROUTINE, URGENT, EMERGENCY)."""
    facility_id = current_user.user.facility_id
    if not facility_id:
        consultation = await HealthcareService(session).repo.get_consultation_by_id(payload.consultation_id)
        if consultation:
            facility_id = consultation.facility_id
        else:
            raise BadRequestException("Facility ID could not be resolved.")

    service = HealthcareService(session)
    ref = await service.create_referral(
        data=payload,
        doctor_id=current_user.id,
        from_facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ReferralResponse.model_validate(ref))


# ============================================================================
# 6. DOCTOR CLINICAL AI ASSISTANT (STG & CONTRAINDICATION SCREENING)
# ============================================================================

@router.post(
    "/ai-assistant/advisory",
    response_model=DataResponse[DoctorClinicalAdvisoryResponse],
    dependencies=[Depends(require_permission(SystemPermissions.CLINICAL_AI_ADVISORY))],
)
async def get_clinical_ai_advisory(
    payload: DoctorClinicalAdvisoryRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Dedicated Doctor AI Clinical Assistant.
    Provides Tamil Nadu Standard Treatment Guidelines (STG) treatment protocols,
    contraindication checks against patient allergies & chronic conditions,
    and adverse drug interaction screening.
    """
    service = HealthcareService(session)
    advisory = await service.get_doctor_clinical_advisory(payload)
    return DataResponse(data=advisory)
