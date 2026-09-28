"""District Emergency Coordinator (Role 08) endpoints."""
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
from app.api.scope import resolve_jurisdiction
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions as P
from app.models.emergency import EmergencyStatus
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.emergency import (
    AffectedFacilityUpsert,
    EmergencyCreate,
    EmergencyDashboard,
    EmergencyDetailResponse,
    EmergencyEscalationCreate,
    EmergencyPrioritySet,
    EmergencyResolve,
    EmergencyResourceRequestCreate,
    EmergencyResponse,
    EmergencyStatusUpdate,
    EmergencyTaskCreate,
    EmergencyTaskUpdate,
    ResourceStatusRow,
    StaffAvailabilityRow,
)
from app.schemas.supply_requests import SupplyRequestResponse
from app.services.emergency_service import EmergencyService

router = APIRouter(prefix="/emergencies", tags=["District Emergency Coordination"])


def _ctx(req: RequestContext):
    return req.ip_address, req.user_agent


def _read_perm(user: AuthenticatedUserContext) -> str:
    for p in (P.EMERGENCY_INCIDENT_MANAGE, P.EMERGENCY_INCIDENT_READ, P.EMERGENCY_INCIDENT_REPORT):
        if user.has_permission(p):
            return p
    raise PermissionDeniedException(f"Missing required permission: '{P.EMERGENCY_INCIDENT_READ}'")


async def _manage(user, session):
    return await resolve_jurisdiction(user, P.EMERGENCY_INCIDENT_MANAGE, session)


@router.get("/dashboard", response_model=DataResponse[EmergencyDashboard])
async def emergency_dashboard(user: AuthenticatedUserContext = Depends(get_current_user),
                              session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    data = await EmergencyService(session).dashboard(j, user.id)
    data["recent"] = [EmergencyResponse.model_validate(e) for e in data["recent"]]
    return DataResponse(data=EmergencyDashboard(**data))


@router.post("", response_model=DataResponse[EmergencyDetailResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_REPORT))])
async def report_emergency(payload: EmergencyCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                           req: RequestContext = Depends(get_request_context),
                           session: AsyncSession = Depends(get_db_session)):
    """Raise an emergency alert. Priority starts UNASSIGNED until an authorized person sets it."""
    j = await resolve_jurisdiction(user, P.EMERGENCY_INCIDENT_REPORT, session)
    inc = await EmergencyService(session).report(payload, j, user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.get("", response_model=PaginatedResponse[EmergencyResponse])
async def list_emergencies(emergency_status: Optional[EmergencyStatus] = Query(None, alias="status"),
                           active_only: bool = False, page: int = Query(1, ge=1),
                           page_size: int = Query(20, ge=1, le=100),
                           user: AuthenticatedUserContext = Depends(get_current_user),
                           session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    items, total = await EmergencyService(session).list(j, user.id, emergency_status, active_only, page, page_size)
    return PaginatedResponse(data=[EmergencyResponse.model_validate(i) for i in items],
                             pagination=PaginationMeta(page=page, page_size=page_size, total=total,
                                                       total_pages=math.ceil(total / page_size) if total else 0))


@router.get("/{incident_id}", response_model=DataResponse[EmergencyDetailResponse])
async def get_emergency(incident_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    return DataResponse(data=EmergencyDetailResponse.model_validate(await EmergencyService(session).get(incident_id, j, user.id)))


@router.post("/{incident_id}/status", response_model=DataResponse[EmergencyDetailResponse],
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def update_emergency_status(incident_id: uuid.UUID, payload: EmergencyStatusUpdate,
                                  user: AuthenticatedUserContext = Depends(get_current_user),
                                  req: RequestContext = Depends(get_request_context),
                                  session: AsyncSession = Depends(get_db_session)):
    inc = await EmergencyService(session).update_status(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/priority", response_model=DataResponse[EmergencyDetailResponse],
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def set_emergency_priority(incident_id: uuid.UUID, payload: EmergencyPrioritySet,
                                 user: AuthenticatedUserContext = Depends(get_current_user),
                                 req: RequestContext = Depends(get_request_context),
                                 session: AsyncSession = Depends(get_db_session)):
    """Human assignment of priority with a recorded reason (AI never sets this)."""
    inc = await EmergencyService(session).set_priority(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/resolve", response_model=DataResponse[EmergencyDetailResponse],
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_RESOLVE))])
async def resolve_emergency(incident_id: uuid.UUID, payload: EmergencyResolve,
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            req: RequestContext = Depends(get_request_context),
                            session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.EMERGENCY_INCIDENT_RESOLVE, session)
    inc = await EmergencyService(session).resolve(incident_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/affected-facilities", response_model=DataResponse[EmergencyDetailResponse],
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def set_affected_facility(incident_id: uuid.UUID, payload: AffectedFacilityUpsert,
                                user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    inc = await EmergencyService(session).upsert_affected(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/tasks", response_model=DataResponse[EmergencyDetailResponse],
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def create_emergency_task(incident_id: uuid.UUID, payload: EmergencyTaskCreate,
                                user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    inc = await EmergencyService(session).create_task(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.patch("/tasks/{task_id}", response_model=DataResponse[EmergencyDetailResponse])
async def update_emergency_task(task_id: uuid.UUID, payload: EmergencyTaskUpdate,
                                user: AuthenticatedUserContext = Depends(get_current_user),
                                req: RequestContext = Depends(get_request_context),
                                session: AsyncSession = Depends(get_db_session)):
    """Coordinator, or the staff member the task is assigned to, updates task progress."""
    can_manage = user.has_permission(P.EMERGENCY_INCIDENT_MANAGE)
    j = await resolve_jurisdiction(user, P.EMERGENCY_INCIDENT_MANAGE, session) if can_manage else None
    inc = await EmergencyService(session).update_task(task_id, payload, j, user.id, can_manage, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/escalations", response_model=DataResponse[EmergencyDetailResponse],
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def escalate_emergency(incident_id: uuid.UUID, payload: EmergencyEscalationCreate,
                             user: AuthenticatedUserContext = Depends(get_current_user),
                             req: RequestContext = Depends(get_request_context),
                             session: AsyncSession = Depends(get_db_session)):
    inc = await EmergencyService(session).escalate(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=EmergencyDetailResponse.model_validate(inc))


@router.post("/{incident_id}/resource-requests", response_model=DataResponse[SupplyRequestResponse],
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.EMERGENCY_INCIDENT_MANAGE))])
async def request_emergency_resources(incident_id: uuid.UUID, payload: EmergencyResourceRequestCreate,
                                      user: AuthenticatedUserContext = Depends(get_current_user),
                                      req: RequestContext = Depends(get_request_context),
                                      session: AsyncSession = Depends(get_db_session)):
    """Forward an emergency supply requirement to the District Supply Chain Officer's queue."""
    sr = await EmergencyService(session).request_resources(incident_id, payload, await _manage(user, session), user.id, _ctx(req))
    return DataResponse(data=SupplyRequestResponse.model_validate(sr))


@router.get("/{incident_id}/staff-availability", response_model=DataResponse[List[StaffAvailabilityRow]])
async def emergency_staff_availability(incident_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                                       session: AsyncSession = Depends(get_db_session)):
    """Read-only, today's attendance at affected facilities (no attendance editing)."""
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    return DataResponse(data=[StaffAvailabilityRow(**r) for r in await EmergencyService(session).staff_availability(incident_id, j, user.id)])


@router.get("/{incident_id}/resource-status", response_model=DataResponse[List[ResourceStatusRow]])
async def emergency_resource_status(incident_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                                    session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _read_perm(user), session)
    return DataResponse(data=[ResourceStatusRow(**r) for r in await EmergencyService(session).resource_status(incident_id, j, user.id)])
