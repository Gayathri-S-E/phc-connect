import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, RequestContext, get_current_user, get_db_session, get_request_context, require_permission
from app.core.permissions import SystemPermissions
from app.schemas.common import DataResponse
from app.schemas.role import PermissionResponse, RoleCreate, RolePermissionAssignRequest, RoleResponse, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(tags=["Roles & Permissions"])


@router.get(
    "/roles",
    response_model=DataResponse[List[RoleResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_MANAGE))],
)
async def list_roles(session: AsyncSession = Depends(get_db_session)):
    """List all system roles and their assigned permissions."""
    service = RoleService(session)
    roles = await service.list_roles()
    role_dtos = []
    for r in roles:
        perms = [
            PermissionResponse.model_validate(rp.permission)
            for rp in r.role_permissions
            if rp.permission
        ]
        role_dtos.append(
            RoleResponse(
                id=r.id,
                name=r.name,
                code=r.code,
                description=r.description,
                is_system=r.is_system,
                is_active=r.is_active,
                created_at=r.created_at,
                updated_at=r.updated_at,
                permissions=perms,
            )
        )
    return DataResponse(data=role_dtos)


@router.post(
    "/roles",
    response_model=DataResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_MANAGE))],
)
async def create_role(
    payload: RoleCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Create a new dynamic role."""
    service = RoleService(session)
    role = await service.create_role(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    perms = [
        PermissionResponse.model_validate(rp.permission)
        for rp in role.role_permissions
        if rp.permission
    ]
    return DataResponse(
        data=RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=perms,
        )
    )


@router.patch(
    "/roles/{role_id}",
    response_model=DataResponse[RoleResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_MANAGE))],
)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update role name, description, or active status."""
    service = RoleService(session)
    await service.update_role(
        role_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    role = await service.get_role(role_id)
    perms = [
        PermissionResponse.model_validate(rp.permission)
        for rp in role.role_permissions
        if rp.permission
    ]
    return DataResponse(
        data=RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=perms,
        )
    )


@router.post(
    "/roles/{role_id}/permissions",
    response_model=DataResponse[RoleResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_MANAGE))],
)
async def assign_role_permissions(
    role_id: uuid.UUID,
    payload: RolePermissionAssignRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Assign granular permission IDs to a role."""
    service = RoleService(session)
    role = await service.assign_permissions(
        role_id,
        payload.permission_ids,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    perms = [
        PermissionResponse.model_validate(rp.permission)
        for rp in role.role_permissions
        if rp.permission
    ]
    return DataResponse(
        data=RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=perms,
        )
    )


@router.get(
    "/permissions",
    response_model=DataResponse[List[PermissionResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_ROLE_MANAGE))],
)
async def list_permissions(session: AsyncSession = Depends(get_db_session)):
    """List all available granular system permission codes from the database."""
    service = RoleService(session)
    perms = await service.list_permissions()
    return DataResponse(data=[PermissionResponse.model_validate(p) for p in perms])
