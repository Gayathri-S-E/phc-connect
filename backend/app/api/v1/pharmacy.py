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
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions
from app.models.identity import ScopeLevel
from app.models.pharmacy import BatchStatus, StockMovementType, StockTransferStatus
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.pharmacy import (
    DispensePrescriptionRequest,
    DispensingRecordResponse,
    InventoryBatchResponse,
    InventoryBatchStatusUpdate,
    InventoryItemResponse,
    ShortageIncidentCreate,
    ShortageIncidentResolveRequest,
    ShortageIncidentResponse,
    StockAdjustmentRequest,
    StockMovementResponse,
    StockReceiptRequest,
    StockTransferApproveRequest,
    StockTransferCreate,
    StockTransferDispatchRequest,
    StockTransferReceiveRequest,
    StockTransferResponse,
)
from app.services.pharmacy_service import PharmacyService

router = APIRouter(tags=["Pharmacy & Inventory Operations"])


# ============================================================================
# INVENTORY ITEMS
# ============================================================================

@router.get(
    "/inventory",
    response_model=PaginatedResponse[InventoryItemResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_ITEM_READ))],
)
async def list_inventory(
    facility_id: Optional[uuid.UUID] = Query(None),
    low_stock_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if target_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot access inventory outside your assigned facility")
        target_facility_id = user_ctx.user.facility_id

    service = PharmacyService(session)
    items, total = await service.list_inventory(
        facility_id=target_facility_id,
        low_stock_only=low_stock_only,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/inventory/{item_id:uuid}",
    response_model=DataResponse[InventoryItemResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_ITEM_READ))],
)
async def get_inventory_item(
    item_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    item = await service.get_inventory_item(item_id)
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if item.facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot access inventory item outside your assigned facility")

    return DataResponse(data=item)


# ============================================================================
# BATCHES & STOCK MOVEMENTS (RECEIPT / ADJUSTMENT)
# ============================================================================

@router.post(
    "/inventory/batches/receive",
    response_model=DataResponse[InventoryBatchResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_MOVEMENT_RECORD))],
)
async def receive_stock(
    payload: StockReceiptRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if payload.facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot receive stock for another facility")

    service = PharmacyService(session)
    batch = await service.receive_stock(
        data=payload,
        actor_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=batch)


@router.post(
    "/inventory/batches/adjust",
    response_model=DataResponse[StockMovementResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_STOCK_ADJUST))],
)
async def adjust_stock(
    payload: StockAdjustmentRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    # Check facility scope on the batch's inventory item
    batch = await service.repo.get_batch_by_id(payload.batch_id)
    if not batch:
        from app.core.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("Batch", str(payload.batch_id))

    target_facility_id = (
        batch.inventory_item.facility_id
        if (batch.inventory_item)
        else user_ctx.user.facility_id
    )
    if not target_facility_id:
        target_facility_id = user_ctx.user.facility_id

    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if target_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot adjust stock batch of another facility")

    movement = await service.adjust_stock(
        data=payload,
        actor_id=user_ctx.user.id,
        facility_id=target_facility_id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=movement)


@router.get(
    "/inventory/batches",
    response_model=DataResponse[List[InventoryBatchResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_ITEM_READ))],
)
async def list_batches(
    inventory_item_id: Optional[uuid.UUID] = Query(None),
    facility_id: Optional[uuid.UUID] = Query(None),
    expiring_within_days: Optional[int] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if target_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot list batches for another facility")
        target_facility_id = user_ctx.user.facility_id

    service = PharmacyService(session)
    batches = await service.list_batches(
        inventory_item_id=inventory_item_id,
        facility_id=target_facility_id,
        expiring_within_days=expiring_within_days,
    )
    return DataResponse(data=batches)


@router.get(
    "/inventory/movements",
    response_model=DataResponse[List[StockMovementResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_MOVEMENT_RECORD))],
)
async def list_stock_movements(
    facility_id: Optional[uuid.UUID] = Query(None),
    inventory_item_id: Optional[uuid.UUID] = Query(None),
    movement_type: Optional[StockMovementType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if target_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot access stock movements of another facility")
        target_facility_id = user_ctx.user.facility_id

    service = PharmacyService(session)
    movements = await service.repo.list_movements(
        facility_id=target_facility_id,
        inventory_item_id=inventory_item_id,
        movement_type=movement_type,
        limit=limit,
    )
    return DataResponse(data=[StockMovementResponse.model_validate(m) for m in movements])


# ============================================================================
# DISPENSING (ATOMIC FEFO MULTI-BATCH DISPENSING)
# ============================================================================

@router.post(
    "/prescriptions/{prescription_id:uuid}/dispense-fefo",
    response_model=DataResponse[List[DispensingRecordResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_DISPENSE))],
)
async def dispense_prescription_fefo(
    prescription_id: uuid.UUID,
    payload: DispensePrescriptionRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    presc = await service.health_repo.get_prescription_by_id(prescription_id)
    if not presc:
        from app.core.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("Prescription", str(prescription_id))

    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if presc.facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot dispense prescription for another facility")

    target_facility_id = presc.facility_id or user_ctx.user.facility_id
    if not target_facility_id:
        raise PermissionDeniedException("Facility context is required to dispense prescriptions")

    await service.dispense_prescription_fefo(
        prescription_id=prescription_id,
        payload=payload,
        pharmacist_id=user_ctx.user.id,
        facility_id=target_facility_id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    records = await service.repo.list_dispensing_records(prescription_id=prescription_id)
    return DataResponse(data=[DispensingRecordResponse.model_validate(r) for r in records])


@router.get(
    "/prescriptions/{prescription_id:uuid}/dispensing-records",
    response_model=DataResponse[List[DispensingRecordResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_READ))],
)
async def get_dispensing_records_for_prescription(
    prescription_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    presc = await service.health_repo.get_prescription_by_id(prescription_id)
    if presc and user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if presc.facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot access dispensing records for another facility")

    records = await service.repo.list_dispensing_records(prescription_id=prescription_id)
    return DataResponse(data=[DispensingRecordResponse.model_validate(r) for r in records])


# ============================================================================
# STOCK TRANSFERS (2-PHASE DISPATCH & RECEIPT)
# ============================================================================

@router.post(
    "/transfers",
    response_model=DataResponse[StockTransferResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_REQUEST))],
)
async def create_transfer_request(
    payload: StockTransferCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    # Requester facility check
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if payload.destination_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Can only request stock transfers on behalf of your assigned facility")

    service = PharmacyService(session)
    transfer = await service.create_transfer_request(
        data=payload,
        requester_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=transfer)


@router.get(
    "/transfers",
    response_model=DataResponse[List[StockTransferResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_REQUEST))],
)
async def list_transfers(
    facility_id: Optional[uuid.UUID] = Query(None),
    transfer_status: Optional[StockTransferStatus] = Query(None, alias="status"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        target_facility_id = user_ctx.user.facility_id

    service = PharmacyService(session)
    transfers = await service.list_transfers(facility_id=target_facility_id, status=transfer_status)
    return DataResponse(data=transfers)


@router.get(
    "/transfers/{transfer_id:uuid}",
    response_model=DataResponse[StockTransferResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_REQUEST))],
)
async def get_transfer(
    transfer_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    transfer = await service.repo.get_transfer_by_id(transfer_id)
    if not transfer:
        from app.core.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("StockTransfer", str(transfer_id))

    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if (
            transfer.source_facility_id != user_ctx.user.facility_id
            and transfer.destination_facility_id != user_ctx.user.facility_id
        ):
            raise PermissionDeniedException("Cannot access transfer involving other facilities")

    return DataResponse(data=StockTransferResponse.model_validate(transfer))


@router.patch(
    "/transfers/{transfer_id:uuid}/approve",
    response_model=DataResponse[StockTransferResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_APPROVE))],
)
async def approve_transfer(
    transfer_id: uuid.UUID,
    payload: StockTransferApproveRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    transfer = await service.approve_transfer(
        transfer_id=transfer_id,
        approver_id=user_ctx.user.id,
        data=payload,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=transfer)


@router.patch(
    "/transfers/{transfer_id:uuid}/dispatch",
    response_model=DataResponse[StockTransferResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_DISPATCH))],
)
async def dispatch_transfer(
    transfer_id: uuid.UUID,
    payload: StockTransferDispatchRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    transfer = await service.dispatch_transfer(
        transfer_id=transfer_id,
        dispatcher_id=user_ctx.user.id,
        data=payload,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=transfer)


@router.patch(
    "/transfers/{transfer_id:uuid}/receive",
    response_model=DataResponse[StockTransferResponse],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_TRANSFER_RECEIVE))],
)
async def receive_transfer(
    transfer_id: uuid.UUID,
    payload: StockTransferReceiveRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    transfer = await service.receive_transfer(
        transfer_id=transfer_id,
        receiver_id=user_ctx.user.id,
        data=payload,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=transfer)


# ============================================================================
# SHORTAGE INCIDENTS
# ============================================================================

@router.post(
    "/shortages",
    response_model=DataResponse[ShortageIncidentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.SHORTAGES_INCIDENT_REPORT))],
)
async def report_shortage_incident(
    payload: ShortageIncidentCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if payload.facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot report shortage incident for another facility")

    service = PharmacyService(session)
    incident = await service.report_shortage_incident(
        data=payload,
        reporter_id=user_ctx.user.id,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=incident)


@router.get(
    "/shortages",
    response_model=DataResponse[List[ShortageIncidentResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.SHORTAGES_INCIDENT_REPORT))],
)
async def list_shortage_incidents(
    facility_id: Optional[uuid.UUID] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        target_facility_id = user_ctx.user.facility_id

    service = PharmacyService(session)
    incidents = await service.list_shortage_incidents(facility_id=target_facility_id)
    return DataResponse(data=incidents)


@router.patch(
    "/shortages/{incident_id:uuid}/resolve",
    response_model=DataResponse[ShortageIncidentResponse],
    dependencies=[Depends(require_permission(SystemPermissions.SHORTAGES_INCIDENT_RESOLVE))],
)
async def resolve_shortage_incident(
    incident_id: uuid.UUID,
    payload: ShortageIncidentResolveRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    service = PharmacyService(session)
    incident = await service.resolve_shortage_incident(
        incident_id=incident_id,
        resolver_id=user_ctx.user.id,
        data=payload,
        ip_address=req_ctx.ip_address,
        user_agent=req_ctx.user_agent,
    )
    return DataResponse(data=incident)
