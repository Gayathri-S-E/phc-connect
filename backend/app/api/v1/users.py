import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, RequestContext, get_current_user, get_db_session, get_request_context, require_permission
from app.core.permissions import SystemPermissions
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.user import UserCreate, UserResponse, UserRoleAssignRequest, UserRoleResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_USER_READ))],
)
async def list_users(
    facility_id: Optional[uuid.UUID] = Query(None),
    organization_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """List paginated users filtered by facility or organization."""
    service = UserService(session)
    users, total = await service.list_users(
        facility_id=facility_id,
        organization_id=organization_id,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    user_dtos = []
    for u in users:
        roles_dto = [
            UserRoleResponse(
                id=ur.id,
                role_id=ur.role_id,
                role_name=ur.role.name if ur.role else "Unknown",
                role_code=ur.role.code if ur.role else "UNKNOWN",
                organization_id=ur.organization_id,
                facility_id=ur.facility_id,
                scope_level=ur.scope_level,
                created_at=ur.created_at,
            )
            for ur in u.user_roles
        ]
        user_dtos.append(
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                phone_number=u.phone_number,
                organization_id=u.organization_id,
                facility_id=u.facility_id,
                is_active=u.is_active,
                is_verified=u.is_verified,
                created_at=u.created_at,
                updated_at=u.updated_at,
                roles=roles_dto,
            )
        )

    return PaginatedResponse(
        data=user_dtos,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.post(
    "",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_USER_CREATE))],
)
async def create_user(
    payload: UserCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Provision a new staff account."""
    service = UserService(session)
    user = await service.create_user(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=UserResponse.model_validate(user))


@router.get(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_USER_READ))],
)
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Get user profile and assigned roles by ID."""
    service = UserService(session)
    user = await service.get_by_id(user_id)
    return DataResponse(data=UserResponse.model_validate(user))


@router.patch(
    "/{user_id}",
    response_model=DataResponse[UserResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_USER_UPDATE))],
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update user information or status."""
    service = UserService(session)
    user = await service.update_user(
        user_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=UserResponse.model_validate(user))


@router.post(
    "/{user_id}/roles",
    response_model=DataResponse[UserRoleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_ASSIGN))],
)
async def assign_role(
    user_id: uuid.UUID,
    payload: UserRoleAssignRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Assign a scoped role (FACILITY / DISTRICT / STATE / GLOBAL) to a user."""
    service = UserService(session)
    user_role = await service.assign_role(
        user_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(
        data=UserRoleResponse(
            id=user_role.id,
            role_id=user_role.role_id,
            role_name=user_role.role.name if user_role.role else "",
            role_code=user_role.role.code if user_role.role else "",
            organization_id=user_role.organization_id,
            facility_id=user_role.facility_id,
            scope_level=user_role.scope_level,
            created_at=user_role.created_at,
        )
    )


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_ASSIGN))],
)
async def revoke_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Revoke a role (at every scope it was granted) from a user."""
    service = UserService(session)
    await service.revoke_role(
        user_id,
        role_id,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
