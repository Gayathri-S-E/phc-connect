import math
import uuid
from typing import Optional

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
from app.api.scope import ensure_any_facility_access, ensure_facility_access, facility_ids_in_scope
from app.core.exceptions import PermissionDeniedException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.models.supply_chain import PurchaseOrderStatus, PurchaseRequestStatus, ShipmentStatus
from app.repositories.pharmacy_repository import PharmacyRepository
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.pharmacy import ShortageIncidentResponse
from app.schemas.supply_chain import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseRequestCreate,
    PurchaseRequestDecision,
    PurchaseRequestResponse,
    ShipmentCreate,
    ShipmentEventCreate,
    ShipmentResponse,
    ShortageEscalateRequest,
    SupplierCreate,
    SupplierResponse,
)
from app.services.supply_chain_service import SupplyChainService

router = APIRouter(tags=["Procurement, Suppliers & Logistics"])

P = SystemPermissions


def _page(items, total: int, page: int, page_size: int, schema) -> PaginatedResponse:
    return PaginatedResponse(
        data=[schema.model_validate(i) for i in items],
        pagination=PaginationMeta(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


def _ctx(req: RequestContext):
    return req.ip_address, req.user_agent


# ============================================================================
# SUPPLIERS
# ============================================================================

@router.get(
    "/suppliers",
    response_model=PaginatedResponse[SupplierResponse],
    dependencies=[Depends(require_permission(P.SUPPLIERS_MANAGE))],
)
async def list_suppliers(
    search: Optional[str] = Query(None, max_length=100),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """List registered pharmaceutical suppliers with reliability ratings."""
    items, total = await SupplyChainService(session).list_suppliers(search, active_only, page, page_size)
    return _page(items, total, page, page_size, SupplierResponse)


@router.post(
    "/suppliers",
    response_model=DataResponse[SupplierResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(P.SUPPLIERS_MANAGE))],
)
async def create_supplier(
    payload: SupplierCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Onboard a new approved medicine or logistics vendor."""
    supplier = await SupplyChainService(session).create_supplier(payload, user_ctx.id, _ctx(req))
    return DataResponse(data=SupplierResponse.model_validate(supplier))


# ============================================================================
# PURCHASE REQUESTS
# ============================================================================

@router.post(
    "/procurement/requests",
    response_model=DataResponse[PurchaseRequestResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(P.PROCUREMENT_REQUEST_CREATE))],
)
async def create_purchase_request(
    payload: PurchaseRequestCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Raise a purchase requisition for a clinic or warehouse."""
    await ensure_facility_access(user_ctx, payload.facility_id, P.PROCUREMENT_REQUEST_CREATE, session)
    pr = await SupplyChainService(session).create_purchase_request(payload, user_ctx.id, _ctx(req))
    return DataResponse(data=PurchaseRequestResponse.model_validate(pr))


@router.get("/procurement/requests", response_model=PaginatedResponse[PurchaseRequestResponse])
async def list_purchase_requests(
    request_status: Optional[PurchaseRequestStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List purchase requests visible to requesters and approvers within their scope."""
    perm = next(
        (p for p in (P.PROCUREMENT_REQUEST_APPROVE, P.PROCUREMENT_REQUEST_CREATE) if user_ctx.has_permission(p)),
        None,
    )
    if perm is None:
        raise PermissionDeniedException(
            f"Missing required permission: '{P.PROCUREMENT_REQUEST_CREATE}' or '{P.PROCUREMENT_REQUEST_APPROVE}'"
        )
    facility_ids = await facility_ids_in_scope(user_ctx, perm, session)
    items, total = await SupplyChainService(session).list_purchase_requests(
        facility_ids, request_status, page, page_size
    )
    return _page(items, total, page, page_size, PurchaseRequestResponse)


async def _decide_request(request_id, approve, payload, user_ctx, req, session):
    service = SupplyChainService(session)
    pr = await service.get_purchase_request(request_id)
    await ensure_facility_access(user_ctx, pr.facility_id, P.PROCUREMENT_REQUEST_APPROVE, session)
    pr = await service.decide_purchase_request(pr, approve, payload.notes, user_ctx.id, _ctx(req))
    return DataResponse(data=PurchaseRequestResponse.model_validate(pr))


@router.post(
    "/procurement/requests/{request_id}/approve",
    response_model=DataResponse[PurchaseRequestResponse],
    dependencies=[Depends(require_permission(P.PROCUREMENT_REQUEST_APPROVE))],
)
async def approve_purchase_request(
    request_id: uuid.UUID,
    payload: PurchaseRequestDecision,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """District approval of a purchase request (requester cannot self-approve)."""
    return await _decide_request(request_id, True, payload, user_ctx, req, session)


@router.post(
    "/procurement/requests/{request_id}/reject",
    response_model=DataResponse[PurchaseRequestResponse],
    dependencies=[Depends(require_permission(P.PROCUREMENT_REQUEST_APPROVE))],
)
async def reject_purchase_request(
    request_id: uuid.UUID,
    payload: PurchaseRequestDecision,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Reject a submitted purchase request."""
    return await _decide_request(request_id, False, payload, user_ctx, req, session)


# ============================================================================
# PURCHASE ORDERS
# ============================================================================

@router.post(
    "/procurement/orders",
    response_model=DataResponse[PurchaseOrderResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(P.PROCUREMENT_ORDER_CREATE))],
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Draft a purchase order to a supplier (optionally converting an approved request)."""
    await ensure_facility_access(user_ctx, payload.destination_facility_id, P.PROCUREMENT_ORDER_CREATE, session)
    po = await SupplyChainService(session).create_purchase_order(payload, user_ctx.id, _ctx(req))
    return DataResponse(data=PurchaseOrderResponse.model_validate(po))


@router.get(
    "/procurement/orders",
    response_model=PaginatedResponse[PurchaseOrderResponse],
    dependencies=[Depends(require_permission(P.PROCUREMENT_ORDER_READ))],
)
async def list_purchase_orders(
    supplier_id: Optional[uuid.UUID] = Query(None),
    order_status: Optional[PurchaseOrderStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Track purchase orders and delivery timelines."""
    facility_ids = await facility_ids_in_scope(user_ctx, P.PROCUREMENT_ORDER_READ, session)
    items, total = await SupplyChainService(session).list_purchase_orders(
        facility_ids, supplier_id, order_status, page, page_size
    )
    return _page(items, total, page, page_size, PurchaseOrderResponse)


@router.post(
    "/procurement/orders/{order_id}/approve",
    response_model=DataResponse[PurchaseOrderResponse],
    dependencies=[Depends(require_permission(P.PROCUREMENT_ORDER_APPROVE))],
)
async def approve_purchase_order(
    order_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Executive sign-off that issues the PO (segregation of duties enforced)."""
    service = SupplyChainService(session)
    po = await service.get_purchase_order(order_id)
    await ensure_facility_access(user_ctx, po.destination_facility_id, P.PROCUREMENT_ORDER_APPROVE, session)
    po = await service.approve_purchase_order(po, user_ctx.id, _ctx(req))
    return DataResponse(data=PurchaseOrderResponse.model_validate(po))


# ============================================================================
# SHIPMENTS
# ============================================================================

@router.post(
    "/shipments",
    response_model=DataResponse[ShipmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(P.SHIPMENTS_CREATE))],
)
async def create_shipment(
    payload: ShipmentCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Generate a shipment consignment for a stock transfer or purchase order."""
    service = SupplyChainService(session)
    origin_id, destination_id = await service.resolve_shipment_route(payload)
    await ensure_any_facility_access(user_ctx, [origin_id, destination_id], P.SHIPMENTS_CREATE, session)
    shipment = await service.create_shipment(payload, user_ctx.id, _ctx(req))
    return DataResponse(data=ShipmentResponse.model_validate(shipment))


@router.get(
    "/shipments",
    response_model=PaginatedResponse[ShipmentResponse],
    dependencies=[Depends(require_permission(P.SHIPMENTS_READ))],
)
async def list_shipments(
    shipment_status: Optional[ShipmentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Track in-transit consignments with carrier details and event history."""
    facility_ids = await facility_ids_in_scope(user_ctx, P.SHIPMENTS_READ, session)
    items, total = await SupplyChainService(session).list_shipments(facility_ids, shipment_status, page, page_size)
    return _page(items, total, page, page_size, ShipmentResponse)


@router.get(
    "/shipments/{shipment_id}",
    response_model=DataResponse[ShipmentResponse],
    dependencies=[Depends(require_permission(P.SHIPMENTS_READ))],
)
async def get_shipment(
    shipment_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    shipment = await SupplyChainService(session).get_shipment(shipment_id)
    await ensure_any_facility_access(
        user_ctx, [shipment.origin_facility_id, shipment.destination_facility_id], P.SHIPMENTS_READ, session
    )
    return DataResponse(data=ShipmentResponse.model_validate(shipment))


@router.post(
    "/shipments/{shipment_id}/events",
    response_model=DataResponse[ShipmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(P.SHIPMENTS_UPDATE))],
)
async def log_shipment_event(
    shipment_id: uuid.UUID,
    payload: ShipmentEventCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Log a milestone checkpoint, delay, delivery, or cold-chain temperature reading."""
    service = SupplyChainService(session)
    shipment = await service.get_shipment(shipment_id)
    await ensure_any_facility_access(
        user_ctx, [shipment.origin_facility_id, shipment.destination_facility_id], P.SHIPMENTS_UPDATE, session
    )
    shipment = await service.log_shipment_event(shipment, payload, user_ctx.id, _ctx(req))
    return DataResponse(data=ShipmentResponse.model_validate(shipment))


# ============================================================================
# SHORTAGE ESCALATION
# ============================================================================

@router.post(
    "/shortages/{incident_id}/escalate",
    response_model=DataResponse[ShortageIncidentResponse],
    dependencies=[Depends(require_permission(P.SHORTAGES_INCIDENT_ESCALATE))],
)
async def escalate_shortage(
    incident_id: uuid.UUID,
    payload: ShortageEscalateRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Escalate a shortage to the district or state buffer reserve; raises a CRITICAL_SHORTAGE alert."""
    incident = await PharmacyRepository(session).get_shortage_incident_by_id(incident_id)
    if not incident:
        raise ResourceNotFoundException("Shortage incident", str(incident_id))
    await ensure_facility_access(user_ctx, incident.facility_id, P.SHORTAGES_INCIDENT_ESCALATE, session)
    incident = await SupplyChainService(session).escalate_shortage(incident, payload, user_ctx.id, _ctx(req))
    return DataResponse(data=ShortageIncidentResponse.model_validate(incident))
