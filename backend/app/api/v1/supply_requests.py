"""Supply requests, allocation, receipts, DHO health-impact notices, state supply dashboard and monitoring.

Roles: Pharmacist (05) raises requests and verifies receipts; DSCO (07) reviews,
allocates within the district and escalates; State Supply Manager (10) reviews
district requests and allocates from state warehouses; DHO (06) reads impact.
"""
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
from app.api.scope import resolve_jurisdiction
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions as P
from app.models.supply_chain import (
    PurchaseRequestUrgency,
    ReceiptVerificationStatus,
    SupplyRequestLevel,
    SupplyRequestStatus,
)
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.supply_requests import (
    HealthImpactCreate,
    HealthImpactResponse,
    MonitoringRunResponse,
    StateSupplyDashboard,
    SupplyAllocationCreate,
    SupplyEscalationCreate,
    SupplyReceiptResponse,
    SupplyRequestClarify,
    SupplyRequestCreate,
    SupplyRequestDecision,
    SupplyRequestDetail,
    SupplyRequestResponse,
)
from app.services.supply_request_service import SupplyRequestService

router = APIRouter(tags=["Supply Requests, Allocation & Receipts"])


def _ctx(req: RequestContext):
    return req.ip_address, req.user_agent


def _page(items, total, page, page_size, schema) -> PaginatedResponse:
    return PaginatedResponse(data=[schema.model_validate(i) for i in items],
                             pagination=PaginationMeta(page=page, page_size=page_size, total=total,
                                                       total_pages=math.ceil(total / page_size) if total else 0))


def _read_perm(user: AuthenticatedUserContext) -> str:
    for p in (P.SUPPLY_ALLOCATION_MANAGE, P.SUPPLY_REQUEST_REVIEW, P.SUPPLY_REQUEST_READ, P.SUPPLY_REQUEST_CREATE):
        if user.has_permission(p):
            return p
    raise PermissionDeniedException(f"Missing required permission: '{P.SUPPLY_REQUEST_READ}'")


async def _detail(service: SupplyRequestService, request_id, j, user) -> SupplyRequestDetail:
    include_stock = user.has_permission(P.SUPPLY_REQUEST_REVIEW) or user.has_permission(P.SUPPLY_ALLOCATION_MANAGE)
    return SupplyRequestDetail.model_validate(await service.detail(request_id, j, include_stock))


@router.post("/supply-requests", response_model=DataResponse[SupplyRequestDetail], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.SUPPLY_REQUEST_CREATE))])
async def create_supply_request(payload: SupplyRequestCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    """PHC (or district warehouse) raises a medicine requirement; duplicates of an open request are rejected."""
    j = await resolve_jurisdiction(user, P.SUPPLY_REQUEST_CREATE, session)
    service = SupplyRequestService(session)
    sr = await service.create(payload, j, user.id, _ctx(req))
    return DataResponse(data=await _detail(service, sr.id, j, user))


@router.get("/supply-requests", response_model=PaginatedResponse[SupplyRequestResponse])
async def list_supply_requests(
    level: Optional[SupplyRequestLevel] = None,
    request_status: Optional[SupplyRequestStatus] = Query(None, alias="status"),
    priority: Optional[PurchaseRequestUrgency] = None,
    open_only: bool = False,
    emergency_only: bool = False,
    facility_id: Optional[uuid.UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Requests in scope, emergency first (configured priority rule), then newest."""
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    items, total = await SupplyRequestService(session).list(j, level, request_status, priority, open_only,
                                                            emergency_only, facility_id, page, page_size)
    return _page(items, total, page, page_size, SupplyRequestResponse)


@router.get("/supply-requests/{request_id}", response_model=DataResponse[SupplyRequestDetail])
async def get_supply_request(request_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                             session: AsyncSession = Depends(get_db_session)):
    """Detail with history, requester stock/consumption and (for reviewers) allocatable stock options."""
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    return DataResponse(data=await _detail(SupplyRequestService(session), request_id, j, user))


def _review_perm(user: AuthenticatedUserContext) -> str:
    for p in (P.SUPPLY_ALLOCATION_MANAGE, P.SUPPLY_REQUEST_REVIEW):
        if user.has_permission(p):
            return p
    raise PermissionDeniedException(f"Missing required permission: '{P.SUPPLY_REQUEST_REVIEW}'")


@router.post("/supply-requests/{request_id}/decision", response_model=DataResponse[SupplyRequestDetail])
async def decide_supply_request(request_id: uuid.UUID, payload: SupplyRequestDecision,
                                user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    """Start review, approve, partially approve (reason), reject (reason), request clarification, or close."""
    j = await resolve_jurisdiction(user, _review_perm(user), session)
    service = SupplyRequestService(session)
    await service.decide(request_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=await _detail(service, request_id, j, user))


@router.post("/supply-requests/{request_id}/clarification", response_model=DataResponse[SupplyRequestDetail],
             dependencies=[Depends(require_permission(P.SUPPLY_REQUEST_CREATE))])
async def clarify_supply_request(request_id: uuid.UUID, payload: SupplyRequestClarify,
                                 user: AuthenticatedUserContext = Depends(get_current_user),
                                 req: RequestContext = Depends(get_request_context),
                                 session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.SUPPLY_REQUEST_CREATE, session)
    service = SupplyRequestService(session)
    await service.clarify(request_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=await _detail(service, request_id, j, user))


@router.post("/supply-requests/{request_id}/allocate", response_model=DataResponse[SupplyRequestDetail])
async def allocate_supply_request(request_id: uuid.UUID, payload: SupplyAllocationCreate,
                                  user: AuthenticatedUserContext = Depends(get_current_user),
                                  req: RequestContext = Depends(get_request_context),
                                  session: AsyncSession = Depends(get_db_session)):
    """Human-authorized allocation: creates an APPROVED transfer from verified, uncommitted, unexpired stock."""
    j = await resolve_jurisdiction(user, _review_perm(user), session)
    service = SupplyRequestService(session)
    await service.allocate(request_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=await _detail(service, request_id, j, user))


@router.post("/supply-requests/{request_id}/escalate", response_model=DataResponse[SupplyRequestResponse],
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.SUPPLY_REQUEST_REVIEW))])
async def escalate_supply_request(request_id: uuid.UUID, payload: SupplyEscalationCreate,
                                  user: AuthenticatedUserContext = Depends(get_current_user),
                                  req: RequestContext = Depends(get_request_context),
                                  session: AsyncSession = Depends(get_db_session)):
    """DSCO escalates to the State Supply Chain / Warehouse Manager when district stock is insufficient."""
    j = await resolve_jurisdiction(user, P.SUPPLY_REQUEST_REVIEW, session)
    child = await SupplyRequestService(session).escalate(request_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=SupplyRequestResponse.model_validate(child))


@router.get("/supply-receipts", response_model=PaginatedResponse[SupplyReceiptResponse])
async def list_supply_receipts(
    verification_status: Optional[ReceiptVerificationStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Verified receipts and discrepancies (dispatched vs actually received)."""
    perm = next((p for p in (P.SUPPLY_ALLOCATION_MANAGE, P.SUPPLY_REQUEST_REVIEW, P.SUPPLY_RECEIPT_VERIFY)
                 if user.has_permission(p)), None)
    if perm is None:
        raise PermissionDeniedException(f"Missing required permission: '{P.SUPPLY_RECEIPT_VERIFY}'")
    j = await resolve_jurisdiction(user, perm, session)
    items, total = await SupplyRequestService(session).list_receipts(j, verification_status, page, page_size)
    return _page(items, total, page, page_size, SupplyReceiptResponse)


# ============================================================================ DSCO → DHO health impact
@router.post("/supply-impacts", response_model=DataResponse[HealthImpactResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.SUPPLY_IMPACT_SHARE))])
async def share_health_impact(payload: HealthImpactCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                              req: RequestContext = Depends(get_request_context),
                              session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.SUPPLY_IMPACT_SHARE, session)
    return DataResponse(data=HealthImpactResponse.model_validate(
        await SupplyRequestService(session).share_impact(payload, j, user.id, _ctx(req))))


@router.get("/supply-impacts", response_model=PaginatedResponse[HealthImpactResponse])
async def list_health_impacts(unacknowledged_only: bool = False, page: int = Query(1, ge=1),
                              page_size: int = Query(20, ge=1, le=100),
                              user: AuthenticatedUserContext = Depends(get_current_user),
                              session: AsyncSession = Depends(get_db_session)):
    perm = next((p for p in (P.SUPPLY_IMPACT_READ, P.SUPPLY_IMPACT_SHARE) if user.has_permission(p)), None)
    if perm is None:
        raise PermissionDeniedException(f"Missing required permission: '{P.SUPPLY_IMPACT_READ}'")
    j = await resolve_jurisdiction(user, perm, session)
    items, total = await SupplyRequestService(session).list_impacts(j, unacknowledged_only, page, page_size)
    return _page(items, total, page, page_size, HealthImpactResponse)


@router.post("/supply-impacts/{impact_id}/acknowledge", response_model=DataResponse[HealthImpactResponse],
             dependencies=[Depends(require_permission(P.SUPPLY_IMPACT_READ))])
async def acknowledge_health_impact(impact_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                                    req: RequestContext = Depends(get_request_context),
                                    session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.SUPPLY_IMPACT_READ, session)
    return DataResponse(data=HealthImpactResponse.model_validate(
        await SupplyRequestService(session).acknowledge_impact(impact_id, j, user.id, _ctx(req))))


# ============================================================================ State supply (Role 10) & monitoring
@router.get("/supply/state-dashboard", response_model=DataResponse[StateSupplyDashboard],
            dependencies=[Depends(require_permission(P.SUPPLY_ALLOCATION_MANAGE))])
async def state_supply_dashboard(user: AuthenticatedUserContext = Depends(get_current_user),
                                 session: AsyncSession = Depends(get_db_session)):
    """Warehouse stock, district requests, allocations, transit, discrepancies and expiry across the jurisdiction."""
    j = await resolve_jurisdiction(user, P.SUPPLY_ALLOCATION_MANAGE, session)
    return DataResponse(data=StateSupplyDashboard(**await SupplyRequestService(session).state_dashboard(j)))


@router.post("/supply/monitoring/run", response_model=DataResponse[MonitoringRunResponse])
async def run_supply_monitoring(user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    """Run the rule-based supply monitor now (also runs on schedule when background jobs are enabled)."""
    j = await resolve_jurisdiction(user, _review_perm(user), session)
    service = SupplyRequestService(session)
    result = await service.run_monitoring(j)
    await service._audit("SUPPLY_MONITORING_RUN", "supply_monitor", j.label, user.id, _ctx(req),
                         new_state={"alerts_created": result["alerts_created"]})
    return DataResponse(data=MonitoringRunResponse(**result))
