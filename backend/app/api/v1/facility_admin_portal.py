"""
Facility Admin / MPHS Portal — Role 06
=======================================
Endpoints for PHC Facility Administrator / Medical PHC Supervisor:

  * Staff Attendance Admin  – facility-level view of all staff attendance by date range
  * Cold Chain Management   – register equipment, log temperatures, detect excursions
  * Outreach Camp Planning  – schedule, update, and track field outreach camps
  * Complaint Management    – triage, respond to, and resolve patient complaints
  * Facility Monthly Report – aggregate OPD, lab, referral, cold chain, grievance KPIs
"""

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
    require_permission,
)
from app.core.authorization import check_scope_access
from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    ColdChainEquipment,
    ColdChainLog,
    ComplaintStatus,
    Consultation,
    FeedbackComplaint,
    LabOrder,
    LabOrderStatus,
    OutreachCamp,
    Patient,
    Prescription,
    PrescriptionStatus,
    Referral,
    StaffAttendance,
    AttendanceStatus,
)
from app.models.identity import User, UserRole
from app.schemas.common import DataResponse
from app.schemas.healthcare import (
    ColdChainEquipmentCreate,
    ColdChainEquipmentResponse,
    ColdChainLogCreate,
    ColdChainLogResponse,
    FacilityReportResponse,
    FeedbackComplaintResponse,
    FeedbackComplaintStatusUpdate,
    OutreachCampCreate,
    OutreachCampResponse,
    OutreachCampUpdate,
    StaffAttendanceSummaryItem,
    StaffAttendanceResponse,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(prefix="/facility-admin", tags=["Facility Admin / MPHS Portal"])


# ===========================================================================
# 1. STAFF ATTENDANCE ADMIN VIEW
# ===========================================================================

@router.get(
    "/staff-attendance",
    response_model=DataResponse[List[StaffAttendanceResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_READ))],
    summary="Facility-Level Staff Attendance View",
    description=(
        "Returns all staff attendance records for a facility within a date range. "
        "Admin/MPHS can monitor absenteeism, late arrivals, and duty camp deployments."
    ),
)
async def get_facility_staff_attendance(
    facility_id: uuid.UUID = Query(...),
    from_date: date = Query(..., description="Start date (inclusive)"),
    to_date: date = Query(..., description="End date (inclusive)"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.STAFF_ATTENDANCE_READ,
        session=session,
    )

    stmt = (
        select(StaffAttendance)
        .where(
            StaffAttendance.facility_id == facility_id,
            StaffAttendance.attendance_date >= from_date,
            StaffAttendance.attendance_date <= to_date,
        )
        .options(selectinload(StaffAttendance.user))
        .order_by(StaffAttendance.attendance_date.desc(), StaffAttendance.check_in_time.asc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()
    return DataResponse(data=[StaffAttendanceResponse.model_validate(r) for r in records])


@router.get(
    "/staff-attendance/summary",
    response_model=DataResponse[List[StaffAttendanceSummaryItem]],
    dependencies=[Depends(require_permission(SystemPermissions.STAFF_ATTENDANCE_READ))],
    summary="Monthly Staff Attendance Summary",
    description="Aggregated per-staff attendance statistics for a facility-month.",
)
async def get_staff_attendance_summary(
    facility_id: uuid.UUID = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.STAFF_ATTENDANCE_READ,
        session=session,
    )

    from_dt = date(year, month, 1)
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    to_dt = date(year, month, last_day)

    stmt = (
        select(StaffAttendance)
        .where(
            StaffAttendance.facility_id == facility_id,
            StaffAttendance.attendance_date >= from_dt,
            StaffAttendance.attendance_date <= to_dt,
        )
        .options(selectinload(StaffAttendance.user).selectinload(User.roles))
    )
    result = await session.execute(stmt)
    records = result.scalars().all()

    # Aggregate by user
    user_stats: dict[uuid.UUID, dict] = {}
    for rec in records:
        uid = rec.user_id
        if uid not in user_stats:
            role_code = "STAFF"
            if rec.user and rec.user.roles:
                user_role = rec.user.roles[0] if rec.user.roles else None
                if user_role:
                    role_stmt = select(UserRole).where(
                        UserRole.user_id == uid,
                        UserRole.facility_id == facility_id,
                    )
                role_code = "STAFF"  # simplified; roles resolved via UserRole in full impl

            user_stats[uid] = {
                "user_id": uid,
                "full_name": rec.user.full_name if rec.user else str(uid),
                "role_code": role_code,
                "present_days": 0,
                "half_days": 0,
                "absent_days": 0,
                "on_leave_days": 0,
                "on_duty_camp_days": 0,
                "total_days": 0,
            }

        stat = user_stats[uid]
        stat["total_days"] += 1
        if rec.status == AttendanceStatus.PRESENT:
            stat["present_days"] += 1
        elif rec.status == AttendanceStatus.HALF_DAY:
            stat["half_days"] += 1
        elif rec.status == AttendanceStatus.ON_LEAVE:
            stat["on_leave_days"] += 1
        elif rec.status == AttendanceStatus.ON_DUTY_CAMP:
            stat["on_duty_camp_days"] += 1

    summary = []
    for uid, s in user_stats.items():
        total = s["total_days"]
        present_equivalent = s["present_days"] + (s["half_days"] * 0.5) + s["on_duty_camp_days"]
        rate = round((present_equivalent / total) * 100, 1) if total > 0 else 0.0
        summary.append(
            StaffAttendanceSummaryItem(
                user_id=s["user_id"],
                full_name=s["full_name"],
                role_code=s["role_code"],
                present_days=s["present_days"],
                half_days=s["half_days"],
                absent_days=s["absent_days"],
                on_leave_days=s["on_leave_days"],
                on_duty_camp_days=s["on_duty_camp_days"],
                attendance_rate_percent=rate,
            )
        )
    return DataResponse(data=summary)


# ===========================================================================
# 2. COLD CHAIN EQUIPMENT MANAGEMENT
# ===========================================================================

@router.post(
    "/cold-chain/equipment",
    response_model=DataResponse[ColdChainEquipmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.COLD_CHAIN_MANAGE))],
    summary="Register Cold Chain Equipment",
    description="Register an ILR, deep freezer, cold box, or vaccine carrier in the facility cold chain registry.",
)
async def register_cold_chain_equipment(
    facility_id: uuid.UUID = Query(...),
    payload: ColdChainEquipmentCreate = ...,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.COLD_CHAIN_MANAGE,
        session=session,
    )

    equipment = ColdChainEquipment(
        id=uuid.uuid4(),
        facility_id=facility_id,
        equipment_type=payload.equipment_type.upper(),
        serial_number=payload.serial_number,
        model_name=payload.model_name,
        min_temp_c=payload.min_temp_c,
        max_temp_c=payload.max_temp_c,
        is_functional=True,
        is_temperature_in_range=True,
    )
    session.add(equipment)
    await session.flush()
    await session.commit()
    return DataResponse(data=ColdChainEquipmentResponse.model_validate(equipment))


@router.get(
    "/cold-chain/equipment",
    response_model=DataResponse[List[ColdChainEquipmentResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.COLD_CHAIN_READ))],
    summary="List Cold Chain Equipment",
)
async def list_cold_chain_equipment(
    facility_id: uuid.UUID = Query(...),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.COLD_CHAIN_READ,
        session=session,
    )
    stmt = (
        select(ColdChainEquipment)
        .where(ColdChainEquipment.facility_id == facility_id)
        .order_by(ColdChainEquipment.equipment_type)
    )
    result = await session.execute(stmt)
    equipments = result.scalars().all()
    return DataResponse(data=[ColdChainEquipmentResponse.model_validate(e) for e in equipments])


@router.post(
    "/cold-chain/equipment/{equipment_id}/log",
    response_model=DataResponse[ColdChainLogResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.COLD_CHAIN_LOG))],
    summary="Record Temperature Log",
    description=(
        "Record twice-daily temperature readings for an ILR or freezer. "
        "Automatically detects temperature excursions (temp outside min–max range) "
        "and updates equipment status."
    ),
)
async def log_cold_chain_temperature(
    equipment_id: uuid.UUID,
    payload: ColdChainLogCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    equip_stmt = select(ColdChainEquipment).where(ColdChainEquipment.id == equipment_id)
    equip = (await session.execute(equip_stmt)).scalar_one_or_none()
    if not equip:
        raise ResourceNotFoundException("Cold Chain Equipment", str(equipment_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=equip.facility_id,
        permission_code=SystemPermissions.COLD_CHAIN_LOG,
        session=session,
    )

    now = datetime.now(timezone.utc)
    is_excursion = (
        payload.temperature_c < equip.min_temp_c or
        payload.temperature_c > equip.max_temp_c
    )

    log_entry = ColdChainLog(
        id=uuid.uuid4(),
        equipment_id=equipment_id,
        recorded_by_id=user_ctx.user.id,
        temperature_c=payload.temperature_c,
        is_excursion=is_excursion,
        excursion_reason=payload.excursion_reason if is_excursion else None,
        notes=payload.notes,
        recorded_at=now,
    )
    session.add(log_entry)

    # Update equipment current state
    equip.current_temp_c = payload.temperature_c
    equip.last_logged_at = now
    equip.is_temperature_in_range = not is_excursion

    await session.flush()
    await session.commit()
    return DataResponse(data=ColdChainLogResponse.model_validate(log_entry))


@router.get(
    "/cold-chain/equipment/{equipment_id}/logs",
    response_model=DataResponse[List[ColdChainLogResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.COLD_CHAIN_READ))],
    summary="Temperature Log History",
)
async def get_cold_chain_logs(
    equipment_id: uuid.UUID,
    limit: int = Query(default=50, le=200),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    equip_stmt = select(ColdChainEquipment).where(ColdChainEquipment.id == equipment_id)
    equip = (await session.execute(equip_stmt)).scalar_one_or_none()
    if not equip:
        raise ResourceNotFoundException("Cold Chain Equipment", str(equipment_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=equip.facility_id,
        permission_code=SystemPermissions.COLD_CHAIN_READ,
        session=session,
    )

    logs_stmt = (
        select(ColdChainLog)
        .where(ColdChainLog.equipment_id == equipment_id)
        .order_by(ColdChainLog.recorded_at.desc())
        .limit(limit)
    )
    logs = (await session.execute(logs_stmt)).scalars().all()
    return DataResponse(data=[ColdChainLogResponse.model_validate(l) for l in logs])


# ===========================================================================
# 3. OUTREACH CAMP MANAGEMENT
# ===========================================================================

@router.post(
    "/outreach-camps",
    response_model=DataResponse[OutreachCampResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.OUTREACH_CAMP_MANAGE))],
    summary="Schedule an Outreach Camp",
    description="Plan a village-level immunization, ANC, or health screening camp.",
)
async def create_outreach_camp(
    facility_id: uuid.UUID = Query(...),
    payload: OutreachCampCreate = ...,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.OUTREACH_CAMP_MANAGE,
        session=session,
    )

    camp = OutreachCamp(
        id=uuid.uuid4(),
        facility_id=facility_id,
        camp_name=payload.camp_name,
        target_village=payload.target_village,
        scheduled_date=payload.scheduled_date,
        supervisor_id=payload.supervisor_id,
        status="SCHEDULED",
        target_beneficiaries=payload.target_beneficiaries,
        actual_beneficiaries_served=0,
        notes=payload.notes,
    )
    session.add(camp)
    await session.flush()
    await session.commit()
    return DataResponse(data=OutreachCampResponse.model_validate(camp))


@router.get(
    "/outreach-camps",
    response_model=DataResponse[List[OutreachCampResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.OUTREACH_CAMP_READ))],
    summary="List Outreach Camps",
)
async def list_outreach_camps(
    facility_id: uuid.UUID = Query(...),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.OUTREACH_CAMP_READ,
        session=session,
    )

    stmt = (
        select(OutreachCamp)
        .where(OutreachCamp.facility_id == facility_id)
    )
    if status_filter:
        stmt = stmt.where(OutreachCamp.status == status_filter.upper())
    stmt = stmt.order_by(OutreachCamp.scheduled_date.desc())
    camps = (await session.execute(stmt)).scalars().all()
    return DataResponse(data=[OutreachCampResponse.model_validate(c) for c in camps])


@router.patch(
    "/outreach-camps/{camp_id}",
    response_model=DataResponse[OutreachCampResponse],
    dependencies=[Depends(require_permission(SystemPermissions.OUTREACH_CAMP_MANAGE))],
    summary="Update Outreach Camp Status and Beneficiary Count",
)
async def update_outreach_camp(
    camp_id: uuid.UUID,
    payload: OutreachCampUpdate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(OutreachCamp).where(OutreachCamp.id == camp_id)
    camp = (await session.execute(stmt)).scalar_one_or_none()
    if not camp:
        raise ResourceNotFoundException("Outreach Camp", str(camp_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=camp.facility_id,
        permission_code=SystemPermissions.OUTREACH_CAMP_MANAGE,
        session=session,
    )

    valid_statuses = {"SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "POSTPONED"}
    if payload.status:
        if payload.status.upper() not in valid_statuses:
            raise BadRequestException(f"Invalid status. Must be one of: {valid_statuses}")
        camp.status = payload.status.upper()

    if payload.actual_beneficiaries_served is not None:
        camp.actual_beneficiaries_served = payload.actual_beneficiaries_served
    if payload.notes is not None:
        camp.notes = payload.notes

    await session.flush()
    await session.commit()
    return DataResponse(data=OutreachCampResponse.model_validate(camp))


# ===========================================================================
# 4. COMPLAINT / GRIEVANCE MANAGEMENT
# ===========================================================================

@router.get(
    "/complaints",
    response_model=DataResponse[List[FeedbackComplaintResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_FEEDBACK_MANAGE))],
    summary="Facility Complaint Queue",
    description="Returns all patient feedback and complaints for the facility, filterable by status.",
)
async def list_facility_complaints(
    facility_id: uuid.UUID = Query(...),
    complaint_status: Optional[str] = Query(default=None, alias="status"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.PATIENTS_FEEDBACK_MANAGE,
        session=session,
    )

    stmt = (
        select(FeedbackComplaint)
        .where(FeedbackComplaint.facility_id == facility_id)
    )
    if complaint_status:
        stmt = stmt.where(FeedbackComplaint.status == complaint_status.upper())
    stmt = stmt.order_by(FeedbackComplaint.created_at.desc())
    complaints = (await session.execute(stmt)).scalars().all()
    return DataResponse(data=[FeedbackComplaintResponse.model_validate(c) for c in complaints])


@router.patch(
    "/complaints/{complaint_id}",
    response_model=DataResponse[FeedbackComplaintResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_FEEDBACK_MANAGE))],
    summary="Resolve or Escalate Complaint",
)
async def update_complaint_status(
    complaint_id: uuid.UUID,
    payload: FeedbackComplaintStatusUpdate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    complaint = await service.repo.get_feedback_complaint_by_id(complaint_id)
    if not complaint:
        raise ResourceNotFoundException("Complaint", str(complaint_id))

    # Scope check via facility
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=complaint.facility_id,
        permission_code=SystemPermissions.PATIENTS_FEEDBACK_MANAGE,
        session=session,
    )

    updated = await service.update_feedback_complaint_status(
        complaint_id=complaint_id,
        data=payload,
        resolver_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=FeedbackComplaintResponse.model_validate(updated))


# ===========================================================================
# 5. FACILITY MONTHLY PERFORMANCE REPORT
# ===========================================================================

@router.get(
    "/reports/monthly",
    response_model=DataResponse[FacilityReportResponse],
    dependencies=[Depends(require_permission(SystemPermissions.FACILITY_REPORT_VIEW))],
    summary="Facility Monthly Performance Report",
    description=(
        "Aggregated HMIS-style monthly report covering OPD load, consultations, "
        "lab tests, referrals, prescriptions, staff attendance, cold chain excursions, "
        "outreach camp coverage, and grievance resolution."
    ),
)
async def get_monthly_facility_report(
    facility_id: uuid.UUID = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.FACILITY_REPORT_VIEW,
        session=session,
    )

    import calendar
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    first_dt = datetime(year, month, 1, tzinfo=timezone.utc)
    last_dt = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, tzinfo=timezone.utc)

    # OPD Patients (unique patients with appointments)
    opd_stmt = select(func.count(func.distinct(Appointment.patient_id))).where(
        Appointment.facility_id == facility_id,
        Appointment.appointment_date >= first_dt,
        Appointment.appointment_date <= last_dt,
        Appointment.status != AppointmentStatus.CANCELLED,
    )
    total_opd = (await session.execute(opd_stmt)).scalar_one() or 0

    # Consultations
    consult_stmt = select(func.count(Consultation.id)).where(
        Consultation.facility_id == facility_id,
        Consultation.started_at >= first_dt,
        Consultation.started_at <= last_dt,
    )
    total_consults = (await session.execute(consult_stmt)).scalar_one() or 0

    # Prescriptions
    rx_stmt = select(func.count(Prescription.id)).where(
        Prescription.facility_id == facility_id,
        Prescription.created_at >= first_dt,
        Prescription.created_at <= last_dt,
        Prescription.status != PrescriptionStatus.CANCELLED,
    )
    total_rx = (await session.execute(rx_stmt)).scalar_one() or 0

    # Lab Orders
    lab_stmt = select(func.count(LabOrder.id)).where(
        LabOrder.facility_id == facility_id,
        LabOrder.ordered_at >= first_dt,
        LabOrder.ordered_at <= last_dt,
    )
    total_labs = (await session.execute(lab_stmt)).scalar_one() or 0

    # Completed Labs
    lab_done_stmt = select(func.count(LabOrder.id)).where(
        LabOrder.facility_id == facility_id,
        LabOrder.ordered_at >= first_dt,
        LabOrder.ordered_at <= last_dt,
        LabOrder.status == LabOrderStatus.COMPLETED,
    )
    total_labs_done = (await session.execute(lab_done_stmt)).scalar_one() or 0

    # Referrals
    ref_stmt = select(func.count(Referral.id)).where(
        Referral.from_facility_id == facility_id,
        Referral.created_at >= first_dt,
        Referral.created_at <= last_dt,
    )
    total_refs = (await session.execute(ref_stmt)).scalar_one() or 0

    # Staff count
    staff_stmt = select(func.count(func.distinct(StaffAttendance.user_id))).where(
        StaffAttendance.facility_id == facility_id,
        StaffAttendance.attendance_date >= first_day,
        StaffAttendance.attendance_date <= last_day,
    )
    total_staff = (await session.execute(staff_stmt)).scalar_one() or 0

    # Attendance rate
    att_records_stmt = select(StaffAttendance).where(
        StaffAttendance.facility_id == facility_id,
        StaffAttendance.attendance_date >= first_day,
        StaffAttendance.attendance_date <= last_day,
    )
    att_records = (await session.execute(att_records_stmt)).scalars().all()
    present_count = sum(
        1 for r in att_records if r.status in (AttendanceStatus.PRESENT, AttendanceStatus.ON_DUTY_CAMP)
    ) + sum(0.5 for r in att_records if r.status == AttendanceStatus.HALF_DAY)
    att_rate = round((present_count / len(att_records)) * 100, 1) if att_records else 0.0

    # Cold chain excursions
    cc_equip_stmt = select(ColdChainEquipment.id).where(ColdChainEquipment.facility_id == facility_id)
    equip_ids = (await session.execute(cc_equip_stmt)).scalars().all()
    excursion_count = 0
    if equip_ids:
        exc_stmt = select(func.count(ColdChainLog.id)).where(
            ColdChainLog.equipment_id.in_(equip_ids),
            ColdChainLog.is_excursion == True,
            ColdChainLog.recorded_at >= first_dt,
            ColdChainLog.recorded_at <= last_dt,
        )
        excursion_count = (await session.execute(exc_stmt)).scalar_one() or 0

    # Outreach camps
    camp_stmt = select(OutreachCamp).where(
        OutreachCamp.facility_id == facility_id,
        OutreachCamp.scheduled_date >= first_day,
        OutreachCamp.scheduled_date <= last_day,
    )
    camps = (await session.execute(camp_stmt)).scalars().all()
    camps_scheduled = len(camps)
    camps_done = sum(1 for c in camps if c.status == "COMPLETED")
    beneficiaries = sum(c.actual_beneficiaries_served for c in camps)

    # Grievances
    griev_stmt = select(FeedbackComplaint).where(
        FeedbackComplaint.facility_id == facility_id,
        FeedbackComplaint.created_at >= first_dt,
        FeedbackComplaint.created_at <= last_dt,
    )
    grievances = (await session.execute(griev_stmt)).scalars().all()
    griev_total = len(grievances)
    griev_resolved = sum(1 for g in grievances if g.status == ComplaintStatus.RESOLVED)
    griev_rate = round((griev_resolved / griev_total) * 100, 1) if griev_total > 0 else 0.0

    # Facility name
    from app.models.facility import Facility
    fac_stmt = select(Facility).where(Facility.id == facility_id)
    fac = (await session.execute(fac_stmt)).scalar_one_or_none()
    fac_name = fac.name if fac else str(facility_id)

    return DataResponse(
        data=FacilityReportResponse(
            facility_id=facility_id,
            facility_name=fac_name,
            report_month=month,
            report_year=year,
            total_opd_patients=total_opd,
            total_consultations=total_consults,
            total_prescriptions_issued=total_rx,
            total_lab_tests_ordered=total_labs,
            total_lab_tests_completed=total_labs_done,
            total_referrals=total_refs,
            total_staff=total_staff,
            staff_attendance_rate_percent=att_rate,
            cold_chain_excursions=excursion_count,
            outreach_camps_scheduled=camps_scheduled,
            outreach_camps_completed=camps_done,
            beneficiaries_served=beneficiaries,
            grievances_received=griev_total,
            grievances_resolved=griev_resolved,
            grievance_resolution_rate_percent=griev_rate,
        )
    )
