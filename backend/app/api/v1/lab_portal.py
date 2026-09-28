"""
Lab Technician & Pathologist Portal — Role 05
==============================================
Endpoints for PHC Laboratory operations:
  * Lab Worklist          – filterable view of requested diagnostic tests
  * Sample Accessioning   – record sample collection, barcode, and sample type
  * Result Entry          – single test result with automatic critical alert detection
  * Panel Results         – batch entry for multi-parameter panels (CBC, LFT, RFT, etc.)
  * Pathologist Verification – formal review and release (enforces separation of duties)
  * Diagnostic AI Guidance – bilingual interpretation and notifiable condition flags
"""

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
from app.models.healthcare import LabOrderStatus
from app.schemas.common import DataResponse
from app.schemas.healthcare import (
    LabDiagnosticGuidanceRequest,
    LabDiagnosticGuidanceResponse,
    LabOrderResponse,
    LabPanelResultCreate,
    LabResultCreate,
    LabResultResponse,
    LabSampleCollectRequest,
    LabWorklistItem,
)
from app.services.healthcare_service import HealthcareService

router = APIRouter(prefix="/lab", tags=["Lab Technician & Pathologist Portal"])


# ============================================================================
# 1. LAB WORKLIST
# ============================================================================

@router.get(
    "/worklist",
    response_model=DataResponse[List[LabWorklistItem]],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_ORDER_READ))],
    summary="Diagnostic Test Worklist",
    description=(
        "Returns the laboratory queue for a facility, filterable by status "
        "(ORDERED, SAMPLE_COLLECTED, IN_ANALYSIS, COMPLETED) or test category. "
        "Includes patient demographics, ordering clinician, sample metadata, and critical value flags."
    ),
)
async def get_lab_worklist(
    facility_id: uuid.UUID = Query(..., description="Facility UUID to scope the worklist"),
    status: Optional[LabOrderStatus] = Query(default=None, description="Optional status filter"),
    test_category: Optional[str] = Query(default=None, description="Optional test category filter"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=SystemPermissions.LABS_ORDER_READ,
        session=session,
    )

    service = HealthcareService(session)
    worklist = await service.get_lab_worklist(
        facility_id=facility_id,
        status=status,
        test_category=test_category,
    )
    return DataResponse(data=worklist)


# ============================================================================
# 2. SAMPLE ACCESSIONING
# ============================================================================

@router.post(
    "/orders/{order_id}/collect-sample",
    response_model=DataResponse[LabOrderResponse],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_SAMPLE_COLLECT))],
    summary="Record Sample Collection & Accessioning",
    description=(
        "Transitions order status from ORDERED to SAMPLE_COLLECTED. "
        "Captures sample type (EDTA Blood, Serum, Sputum, Urine), barcode, and technician notes."
    ),
)
async def collect_sample(
    order_id: uuid.UUID,
    payload: LabSampleCollectRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_SAMPLE_COLLECT,
        session=session,
    )

    updated_order = await service.collect_lab_sample(
        order_id=order_id,
        data=payload,
        technician_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=LabOrderResponse.model_validate(updated_order))


# ============================================================================
# 3. RESULT ENTRY (SINGLE TEST)
# ============================================================================

@router.post(
    "/orders/{order_id}/results",
    response_model=DataResponse[LabResultResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.LABS_RESULT_RECORD))],
    summary="Enter Single Lab Result with Critical Value Engine",
    description=(
        "Records test value, unit, and reference range. Evaluates results against "
        "panic thresholds (Severe Anemia, Thrombocytopenia, Hyper/Hypoglycemia, Dengue, TB, Malaria) "
        "and auto-flags is_abnormal and critical_alert."
    ),
)
async def add_lab_result(
    order_id: uuid.UUID,
    payload: LabResultCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_RESULT_RECORD,
        session=session,
    )

    result = await service.add_lab_result(
        order_id=order_id,
        data=payload,
        technician_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=LabResultResponse.model_validate(result))


# ============================================================================
# 4. PANEL RESULT ENTRY (MULTI-PARAMETER BATCH)
# ============================================================================

@router.post(
    "/orders/{order_id}/panel-results",
    response_model=DataResponse[List[LabResultResponse]],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.LABS_RESULT_RECORD))],
    summary="Enter Multi-Parameter Panel Results",
    description="Atomically records multiple test findings under a single diagnostic order.",
)
async def add_lab_panel_results(
    order_id: uuid.UUID,
    payload: LabPanelResultCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_RESULT_RECORD,
        session=session,
    )

    results = await service.add_lab_panel_results(
        order_id=order_id,
        data=payload,
        technician_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=[LabResultResponse.model_validate(r) for r in results])


# ============================================================================
# 5. PATHOLOGIST / MEDICAL OFFICER VERIFICATION
# ============================================================================

@router.post(
    "/orders/{order_id}/verify",
    response_model=DataResponse[LabOrderResponse],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_RESULT_VERIFY))],
    summary="Verify & Release Lab Order",
    description=(
        "Pathologist or Medical Officer review and formal sign-off. "
        "Enforces strict separation of duties — requires LABS_RESULT_VERIFY permission. "
        "Transitions status to COMPLETED and stamps verification timestamp."
    ),
)
async def verify_lab_order(
    order_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    order = await service.repo.get_lab_order_by_id(order_id)
    if not order:
        raise ResourceNotFoundException("Lab Order", str(order_id))

    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=order.facility_id,
        permission_code=SystemPermissions.LABS_RESULT_VERIFY,
        session=session,
    )

    verified = await service.verify_lab_order(
        order_id=order_id,
        verifier_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=LabOrderResponse.model_validate(verified))


# ============================================================================
# 6. DIAGNOSTIC AI & INTERPRETATION GUIDANCE
# ============================================================================

@router.post(
    "/diagnostic-guidance",
    response_model=DataResponse[LabDiagnosticGuidanceResponse],
    dependencies=[Depends(require_permission(SystemPermissions.LABS_ORDER_READ))],
    summary="Bilingual Diagnostic Guidance AI",
    description=(
        "Returns clinical interpretation (English + Tamil), panic alert status, "
        "action guidelines per Tamil Nadu Standard Treatment Guidelines (STG), "
        "and statutory notification mandates (IDSP Form L, Nikshay TB, NVBDCP Malaria)."
    ),
)
async def get_diagnostic_guidance(
    payload: LabDiagnosticGuidanceRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = HealthcareService(session)
    guidance = service.get_diagnostic_guidance(payload)
    return DataResponse(data=guidance)
