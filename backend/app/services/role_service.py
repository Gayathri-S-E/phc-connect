import uuid
from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.models.identity import Permission, Role
from app.repositories.audit_repository import AuditRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.role_repo = RoleRepository(session)
        self.audit_repo = AuditRepository(session)

    async def list_roles(self) -> Sequence[Role]:
        return await self.role_repo.list_all(active_only=False)

    async def get_role(self, role_id: uuid.UUID) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ResourceNotFoundException("Role", str(role_id))
        return role

    async def create_role(
        self,
        data: RoleCreate,
        actor_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Role:
        existing = await self.role_repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Role with code '{data.code}' already exists.")

        role = Role(
            name=data.name,
            code=data.code,
            description=data.description,
            is_system=False,
            is_active=True,
        )
        await self.role_repo.create(role)

        if data.permission_ids:
            await self.role_repo.assign_permissions(role.id, data.permission_ids)

        await self.audit_repo.record_event(
            action="ROLE_CREATED",
            resource_type="role",
            resource_id=str(role.id),
            actor_id=actor_id,
            new_state={"code": role.code, "name": role.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.get_role(role.id)

    async def update_role(
        self,
        role_id: uuid.UUID,
        data: RoleUpdate,
        actor_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Role:
        role = await self.get_role(role_id)
        old_state = {"name": role.name, "is_active": role.is_active}

        if data.name is not None:
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.is_active is not None:
            role.is_active = data.is_active

        await self.role_repo.update(role)

        await self.audit_repo.record_event(
            action="ROLE_UPDATED",
            resource_type="role",
            resource_id=str(role.id),
            actor_id=actor_id,
            old_state=old_state,
            new_state={"name": role.name, "is_active": role.is_active},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return role

    async def assign_permissions(
        self,
        role_id: uuid.UUID,
        permission_ids: List[uuid.UUID],
        actor_id: uuid.UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Role:
        role = await self.get_role(role_id)
        await self.role_repo.assign_permissions(role.id, permission_ids)

        await self.audit_repo.record_event(
            action="ROLE_PERMISSIONS_ASSIGNED",
            resource_type="role",
            resource_id=str(role.id),
            actor_id=actor_id,
            new_state={"permission_ids_count": len(permission_ids)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.get_role(role.id)

    async def list_permissions(self) -> Sequence[Permission]:
        return await self.role_repo.list_permissions()
