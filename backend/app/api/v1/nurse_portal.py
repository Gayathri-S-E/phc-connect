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
from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.models.healthcare import AppointmentStatus
from app.schemas.common import DataResponse
from app.schemas.healthcare import (
    AppointmentResponse,
    AppointmentStatusUpdate,
    DoctorOPDQueueItem,
    NurseImmunizationGuidanceRequest,
    NurseImmunizationGuidanceResponse,
    StaffAttendanceCheckIn,
    StaffAttendanceCheckOut,
    StaffAttendanceResponse,
    VitalsCreate,
    VitalsResponse,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(prefix="/nurse", tags=["Nurse Portal (Role 03 - Staff Nurse)"])


# ============================================================================
# 1. STAFF DUTY ATTENDANCE
# ============================================================================

@router.post(
    "/attendance/check-in",
    response_model=DataResponse[StaffAttendanceResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_RECORD))],
)
async def nurse_check_in(
    payload: StaffAttendanceCheckIn,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Record Nurse duty shift check-in."""
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
async def nurse_check_out(
    payload: StaffAttendanceCheckOut,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Record Nurse duty shift check-out."""
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
async def get_nurse_attendance_today(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve Nurse current day duty attendance status."""
    service = HealthcareService(session)
    record = await service.get_staff_attendance_today(current_user.id)
    if not record:
        return DataResponse(data=None)
    return DataResponse(data=StaffAttendanceResponse.model_validate(record))


# ============================================================================
# 2. TRIAGE QUEUE & CHECK-IN
# ============================================================================

@router.get(
    "/triage/queue",
    response_model=DataResponse[List[DoctorOPDQueueItem]],
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_VIEW))],
)
async def get_nurse_triage_queue(
    target_date: Optional[date] = Query(None, description="Queue date (defaults to today)"),
    facility_id: Optional[uuid.UUID] = Query(None, description="PHC facility filter"),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get list of appointments for triage vital signs and room check-in.
    Ordered by triage priority and sequential token number.
    """
    effective_facility_id = facility_id or current_user.user.facility_id
    if not effective_facility_id:
        raise BadRequestException("Facility ID must be provided or linked to user.")

    service = HealthcareService(session)
    queue = await service.get_doctor_opd_queue(
        facility_id=effective_facility_id,
        doctor_id=None,
        target_date=target_date,
    )
    return DataResponse(data=queue)


@router.post(
    "/triage/vitals",
    response_model=DataResponse[VitalsResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_VITALS_RECORD))],
)
async def record_triage_vitals(
    appointment_id: uuid.UUID = Query(..., description="ID of appointment being triaged"),
    payload: VitalsCreate = ...,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Record patient triage vital signs (BP, Pulse, Temp, Resp, SpO2, BMI).
    Automated Early Warning Scoring automatically flags EMERGENCY or PRIORITY
    and moves patient status to CHECKED_IN.
    """
    service = HealthcareService(session)
    saved_vitals, _ = await service.record_nurse_triage_vitals(
        appointment_id=appointment_id,
        vitals_data=payload,
        nurse_id=current_user.id,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=VitalsResponse.model_validate(saved_vitals))


@router.patch(
    "/appointments/{appointment_id}/check-in",
    response_model=DataResponse[AppointmentResponse],
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_MANAGE))],
)
async def check_in_patient_token(
    appointment_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Mark an assigned patient token as physically CHECKED_IN at the PHC OPD desk."""
    service = HealthcareService(session)
    appt = await service.update_appointment_status(
        appointment_id=appointment_id,
        data=AppointmentStatusUpdate(status=AppointmentStatus.CHECKED_IN),
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=AppointmentResponse.model_validate(appt))


# ============================================================================
# 3. NURSE AI ASSISTANT (IMMUNIZATION & ANC PROTOCOLS)
# ============================================================================

@router.post(
    "/ai-assistant/immunization-guidance",
    response_model=DataResponse[NurseImmunizationGuidanceResponse],
    dependencies=[Depends(require_permission(SystemPermissions.CLINICAL_AI_ADVISORY))],
)
async def get_nurse_immunization_guidance(
    payload: NurseImmunizationGuidanceRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Dedicated Nurse AI Assistant.
    Provides Tamil Nadu Universal Immunization Program (UIP) schedule checks,
    Maternal Antenatal Care (ANC) milestones, High-Risk Pregnancy red flags,
    and vaccine cold chain temperature preservation instructions.
    """
    service = HealthcareService(session)
    guidance = await service.get_nurse_immunization_guidance(payload)
    return DataResponse(data=guidance)
