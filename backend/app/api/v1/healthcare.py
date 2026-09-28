import math
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
    require_permission,
)
from app.core.authorization import check_scope_access
from app.core.exceptions import PermissionDeniedException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.api.scope import resolve_facility_filter
from app.models.healthcare import AppointmentStatus, LabOrderStatus, PrescriptionStatus
from app.models.identity import ScopeLevel
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.healthcare import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
    ClinicalAmendmentCreate,
    ClinicalAmendmentResponse,
    ClinicalHistoryResponse,
    ConsultationCreate,
    ConsultationFinalizeRequest,
    ConsultationResponse,
    LabOrderCreate,
    LabOrderResponse,
    LabResultCreate,
    LabResultResponse,
    MedicationCreate,
    MedicationResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
    PrescriptionCreate,
    PrescriptionDispenseRequest,
    PrescriptionResponse,
    ReferralCreate,
    ReferralResponse,
    ReferralStatusUpdate,
    VitalsCreate,
    VitalsResponse,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(tags=["Healthcare Core Operations"])


# ============================================================================
# PATIENTS
# ============================================================================

@router.post(
    "/patients",
    response_model=DataResponse[PatientResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_PROFILE_CREATE))],
)
async def register_patient(
    payload: PatientCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Register a new patient at a healthcare facility."""
    await check_scope_access(
        current_user=current_user,
        target_facility_id=payload.primary_facility_id,
        permission_code=SystemPermissions.PATIENTS_PROFILE_CREATE,
        session=session,
    )
    service = HealthcareService(session)
    patient = await service.register_patient(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PatientResponse.model_validate(patient))


@router.get(
    "/patients",
    response_model=PaginatedResponse[PatientResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_PROFILE_READ))],
)
async def search_patients(
    facility_id: Optional[uuid.UUID] = Query(None),
    query: Optional[str] = Query(None, description="Search by identifier, phone, or name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Search and filter registered patients with scope-aware filtering."""
    scope = current_user.get_highest_scope(SystemPermissions.PATIENTS_PROFILE_READ)
    if scope == ScopeLevel.FACILITY:
        if facility_id and facility_id != current_user.facility_id:
            raise PermissionDeniedException("Cross-facility access denied: Your search is restricted to your assigned health facility.")
        facility_id = current_user.facility_id
    elif facility_id:
        await check_scope_access(
            current_user=current_user,
            target_facility_id=facility_id,
            permission_code=SystemPermissions.PATIENTS_PROFILE_READ,
            session=session,
        )

    service = HealthcareService(session)
    patients, total = await service.search_patients(
        facility_id=facility_id,
        query=query,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        data=[PatientResponse.model_validate(p) for p in patients],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/patients/{patient_id:uuid}",
    response_model=DataResponse[PatientResponse],
)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get patient demographic record by ID (enforcing SELF or facility/district/state scope)."""
    service = HealthcareService(session)
    patient = await service.get_patient(patient_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=patient.primary_facility_id,
        permission_code=SystemPermissions.PATIENTS_PROFILE_READ,
        session=session,
        target_patient_user_id=patient.user_id,
    )

    return DataResponse(data=PatientResponse.model_validate(patient))


@router.patch(
    "/patients/{patient_id:uuid}",
    response_model=DataResponse[PatientResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_PROFILE_UPDATE))],
)
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update patient demographic and emergency contact information."""
    service = HealthcareService(session)
    patient = await service.get_patient(patient_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=patient.primary_facility_id,
        permission_code=SystemPermissions.PATIENTS_PROFILE_UPDATE,
        session=session,
        target_patient_user_id=patient.user_id,
    )

    updated = await service.update_patient(
        patient_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PatientResponse.model_validate(updated))


@router.get(
    "/patients/{patient_id:uuid}/clinical-history",
    response_model=DataResponse[ClinicalHistoryResponse],
)
async def get_patient_clinical_history(
    patient_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve complete longitudinal clinical history (authorized clinician or patient SELF)."""
    service = HealthcareService(session)
    patient = await service.get_patient(patient_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=patient.primary_facility_id,
        permission_code=SystemPermissions.PATIENTS_RECORDS_READ,
        session=session,
        target_patient_user_id=patient.user_id,
    )

    history = await service.get_patient_clinical_history(patient_id)
    return DataResponse(data=history)


# ============================================================================
# APPOINTMENTS
# ============================================================================

@router.post(
    "/appointments",
    response_model=DataResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_MANAGE))],
)
async def create_appointment(
    payload: AppointmentCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Schedule a clinical appointment at a facility."""
    await check_scope_access(
        current_user=current_user,
        target_facility_id=payload.facility_id,
        permission_code=SystemPermissions.APPOINTMENTS_MANAGE,
        session=session,
    )
    service = HealthcareService(session)
    appointment = await service.create_appointment(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=AppointmentResponse.model_validate(appointment))


@router.get(
    "/appointments",
    response_model=PaginatedResponse[AppointmentResponse],
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_VIEW))],
)
async def list_appointments(
    facility_id: Optional[uuid.UUID] = Query(None),
    patient_id: Optional[uuid.UUID] = Query(None),
    doctor_id: Optional[uuid.UUID] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List appointments filtered by facility, patient, doctor, or status."""
    scope = current_user.get_highest_scope(SystemPermissions.APPOINTMENTS_VIEW)
    if scope == ScopeLevel.FACILITY:
        if facility_id and facility_id != current_user.facility_id:
            raise PermissionDeniedException("Cross-facility access denied: You can only view appointments at your assigned facility.")
        facility_id = current_user.facility_id
    elif facility_id:
        await check_scope_access(
            current_user=current_user,
            target_facility_id=facility_id,
            permission_code=SystemPermissions.APPOINTMENTS_VIEW,
            session=session,
        )

    service = HealthcareService(session)
    appointments, total = await service.list_appointments(
        facility_id=facility_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        data=[AppointmentResponse.model_validate(a) for a in appointments],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.patch(
    "/appointments/{appointment_id}/status",
    response_model=DataResponse[AppointmentResponse],
    dependencies=[Depends(require_permission(SystemPermissions.APPOINTMENTS_MANAGE))],
)
async def update_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Transition appointment status (e.g. CHECKED_IN, CANCELLED)."""
    service = HealthcareService(session)
    appointment = await service.repo.get_appointment_by_id(appointment_id)
    if not appointment:
        raise ResourceNotFoundException("Appointment", str(appointment_id))

    await check_scope_access(
        current_user=current_user,
        target_facility_id=appointment.facility_id,
        permission_code=SystemPermissions.APPOINTMENTS_MANAGE,
        session=session,
    )

    updated = await service.update_appointment_status(
        appointment_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=AppointmentResponse.model_validate(updated))


# ============================================================================
# CONSULTATIONS (CLINICAL ENCOUNTERS)
# ============================================================================

@router.post(
    "/consultations",
    response_model=DataResponse[ConsultationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
async def start_consultation(
    payload: ConsultationCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Commence a clinical encounter, recording chief complaint and triage vitals."""
    facility_id = current_user.facility_id
    if not facility_id:
        raise PermissionDeniedException("Doctor must be assigned to an active health facility to conduct consultations.")

    service = HealthcareService(session)
    patient = await service.get_patient(payload.patient_id)

    # Scope check doctor facility and patient facility
    await check_scope_access(
        current_user=current_user,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.CONSULTATIONS_CONDUCT,
        session=session,
    )
    await check_scope_access(
        current_user=current_user,
        target_facility_id=patient.primary_facility_id,
        permission_code=SystemPermissions.CONSULTATIONS_CONDUCT,
        session=session,
    )

    consultation = await service.start_consultation(
        payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ConsultationResponse.model_validate(consultation))


@router.get(
    "/consultations/{consultation_id}",
    response_model=DataResponse[ConsultationResponse],
)
async def get_consultation(
    consultation_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get complete consultation details including diagnoses, prescriptions, and lab orders."""
    service = HealthcareService(session)
    consultation = await service.get_consultation(consultation_id)
    patient = await service.get_patient(consultation.patient_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.PATIENTS_RECORDS_READ,
        session=session,
        target_patient_user_id=patient.user_id,
    )

    return DataResponse(data=ConsultationResponse.model_validate(consultation))


@router.post(
    "/consultations/{consultation_id}/finalize",
    response_model=DataResponse[ConsultationResponse],
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
async def finalize_consultation(
    consultation_id: uuid.UUID,
    payload: ConsultationFinalizeRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Finalize clinical encounter, locking notes and attaching formal diagnoses."""
    service = HealthcareService(session)
    consultation = await service.get_consultation(consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.CONSULTATIONS_CONDUCT,
        session=session,
    )

    finalized = await service.finalize_consultation(
        consultation_id,
        payload,
        doctor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ConsultationResponse.model_validate(finalized))


@router.post(
    "/consultations/{consultation_id}/amendments",
    response_model=DataResponse[ClinicalAmendmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
async def add_clinical_amendment(
    consultation_id: uuid.UUID,
    payload: ClinicalAmendmentCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Attach a formal clinical amendment/addendum to a finalized encounter."""
    service = HealthcareService(session)
    consultation = await service.get_consultation(consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.CONSULTATIONS_CONDUCT,
        session=session,
    )

    amendment = await service.add_amendment(
        consultation_id=consultation_id,
        data=payload,
        doctor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ClinicalAmendmentResponse.model_validate(amendment))


@router.post(
    "/consultations/{consultation_id}/vitals",
    response_model=DataResponse[VitalsResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PATIENTS_VITALS_RECORD))],
)
async def record_consultation_vitals(
    consultation_id: uuid.UUID,
    payload: VitalsCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Record an official physiological observation into the vitals ledger for an encounter."""
    service = HealthcareService(session)
    consultation = await service.get_consultation(consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.PATIENTS_VITALS_RECORD,
        session=session,
    )

    vitals = await service.record_vitals(
        consultation_id=consultation_id,
        data=payload,
        recorder_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=VitalsResponse.model_validate(vitals))


# ============================================================================
# PRESCRIPTIONS & PHARMACY DISPENSING
# ============================================================================

@router.post(
    "/prescriptions",
    response_model=DataResponse[PrescriptionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_CREATE))],
)
async def create_prescription(
    payload: PrescriptionCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Issue a prescription with line items linked to a consultation."""
    facility_id = current_user.facility_id
    if not facility_id:
        raise PermissionDeniedException("Prescribing doctor must be associated with a facility.")

    service = HealthcareService(session)
    consultation = await service.get_consultation(payload.consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.PRESCRIPTIONS_CREATE,
        session=session,
    )

    prescription = await service.create_prescription(
        payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PrescriptionResponse.model_validate(prescription))


@router.get(
    "/prescriptions",
    response_model=PaginatedResponse[PrescriptionResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_READ))],
)
async def list_prescriptions(
    facility_id: Optional[uuid.UUID] = Query(None),
    patient_id: Optional[uuid.UUID] = Query(None),
    doctor_id: Optional[uuid.UUID] = Query(None),
    rx_status: Optional[PrescriptionStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Search prescriptions by patient, doctor, facility, or status."""
    target = await resolve_facility_filter(current_user, facility_id, SystemPermissions.PRESCRIPTIONS_READ, session)
    service = HealthcareService(session)
    items, total = await service.repo.list_prescriptions_paginated(
        facility_id=target,
        patient_id=patient_id,
        status=rx_status,
        doctor_id=doctor_id,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return PaginatedResponse(
        data=[PrescriptionResponse.model_validate(p) for p in items],
        pagination=PaginationMeta(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=DataResponse[PrescriptionResponse],
)
async def get_prescription(
    prescription_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get prescription details and dispensing progress."""
    service = HealthcareService(session)
    prescription = await service.get_prescription(prescription_id)
    patient = await service.get_patient(prescription.patient_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=prescription.facility_id,
        permission_code=SystemPermissions.PRESCRIPTIONS_READ,
        session=session,
        target_patient_user_id=patient.user_id,
    )

    return DataResponse(data=PrescriptionResponse.model_validate(prescription))


@router.post(
    "/prescriptions/{prescription_id}/dispense",
    response_model=DataResponse[PrescriptionResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_DISPENSE))],
)
async def dispense_prescription(
    prescription_id: uuid.UUID,
    payload: PrescriptionDispenseRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Mark prescription items as dispensed by pharmacy."""
    service = HealthcareService(session)
    prescription = await service.get_prescription(prescription_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=prescription.facility_id,
        permission_code=SystemPermissions.PRESCRIPTIONS_DISPENSE,
        session=session,
    )

    dispensed = await service.dispense_prescription(
        prescription_id,
        payload,
        pharmacist_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=PrescriptionResponse.model_validate(dispensed))


# ============================================================================
# LABORATORY ORDERS & RESULTS
# ============================================================================

@router.post(
    "/labs/orders",
    response_model=DataResponse[LabOrderResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.LABS_ORDER_CREATE))],
)
async def create_lab_order(
    payload: LabOrderCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Order diagnostic laboratory panel for an encounter."""
    facility_id = current_user.facility_id
    if not facility_id:
        raise PermissionDeniedException("Doctor ordering tests must be assigned to a facility.")

    service = HealthcareService(session)
    consultation = await service.get_consultation(payload.consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.LABS_ORDER_CREATE,
        session=session,
    )

    order = await service.create_lab_order(
        payload,
        doctor_id=current_user.id,
        facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=LabOrderResponse.model_validate(order))


@router.get(
    "/labs/orders",
    response_model=PaginatedResponse[LabOrderResponse],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_ORDER_READ))],
)
async def list_lab_orders(
    facility_id: Optional[uuid.UUID] = Query(None),
    patient_id: Optional[uuid.UUID] = Query(None),
    order_status: Optional[LabOrderStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List lab orders, e.g. those pending sample collection or testing."""
    target = await resolve_facility_filter(current_user, facility_id, SystemPermissions.LABS_ORDER_READ, session)
    service = HealthcareService(session)
    items, total = await service.repo.list_lab_orders_paginated(
        facility_id=target,
        patient_id=patient_id,
        status=order_status,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return PaginatedResponse(
        data=[LabOrderResponse.model_validate(o) for o in items],
        pagination=PaginationMeta(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


@router.post(
    "/labs/orders/{order_id}/results",
    response_model=DataResponse[LabResultResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.LABS_RESULT_RECORD))],
)
async def add_lab_result(
    order_id: uuid.UUID,
    payload: LabResultCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Enter diagnostic laboratory test result."""
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=current_user,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_RESULT_RECORD,
        session=session,
    )

    result = await service.add_lab_result(
        order_id,
        payload,
        technician_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=LabResultResponse.model_validate(result))


@router.post(
    "/labs/orders/{order_id}/verify",
    response_model=DataResponse[LabOrderResponse],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_RESULT_VERIFY))],
)
async def verify_lab_order(
    order_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Formally verify and release lab test findings."""
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=current_user,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_RESULT_VERIFY,
        session=session,
    )

    verified = await service.verify_lab_order(
        order_id,
        verifier_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=LabOrderResponse.model_validate(verified))


# ============================================================================
# REFERRALS
# ============================================================================

@router.post(
    "/referrals",
    response_model=DataResponse[ReferralResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.REFERRALS_CREATE))],
)
async def create_referral(
    payload: ReferralCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Initiate an inter-facility clinical referral for specialized treatment."""
    facility_id = current_user.facility_id
    if not facility_id:
        raise PermissionDeniedException("Referring physician must be associated with a facility.")

    service = HealthcareService(session)
    consultation = await service.get_consultation(payload.consultation_id)

    await check_scope_access(
        current_user=current_user,
        target_facility_id=consultation.facility_id,
        permission_code=SystemPermissions.REFERRALS_CREATE,
        session=session,
    )

    referral = await service.create_referral(
        payload,
        doctor_id=current_user.id,
        from_facility_id=facility_id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ReferralResponse.model_validate(referral))


@router.patch(
    "/referrals/{referral_id}/status",
    response_model=DataResponse[ReferralResponse],
    dependencies=[Depends(require_permission(SystemPermissions.REFERRALS_UPDATE))],
)
async def update_referral_status(
    referral_id: uuid.UUID,
    payload: ReferralStatusUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update referral state (e.g. ACCEPTED, COMPLETED, REJECTED)."""
    service = HealthcareService(session)
    referral = await service.repo.get_referral_by_id(referral_id)
    if not referral:
        raise ResourceNotFoundException("Referral", str(referral_id))

    await check_scope_access(
        current_user=current_user,
        target_facility_id=referral.from_facility_id,
        permission_code=SystemPermissions.REFERRALS_UPDATE,
        session=session,
    )

    updated = await service.update_referral_status(
        referral_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=ReferralResponse.model_validate(updated))


# ============================================================================
# MASTER REFERENCE DATA (PHASE 2.1 BOUNDARY)
# ============================================================================

@router.post(
    "/medications",
    response_model=DataResponse[MedicationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_ITEM_CREATE))],
)
async def create_medication(
    payload: MedicationCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Register a standardized pharmaceutical item in the master catalog."""
    service = HealthcareService(session)
    med = await service.create_medication(
        data=payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=MedicationResponse.model_validate(med))


@router.get(
    "/medications",
    response_model=DataResponse[List[MedicationResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_READ))],
)
async def list_medications(
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_db_session),
):
    """List active medications from the master catalog for prescribing."""
    service = HealthcareService(session)
    meds = await service.list_medications(active_only=active_only)
    return DataResponse(data=[MedicationResponse.model_validate(m) for m in meds])


router.add_api_route(
    "/consultations/{consultation_id}/finalize",
    finalize_consultation,
    methods=["PATCH"],
    response_model=DataResponse[ConsultationResponse],
    dependencies=[Depends(require_permission(SystemPermissions.CONSULTATIONS_CONDUCT))],
)
