import uuid
from typing import Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ResourceNotFoundException
from app.core.security import get_password_hash
from app.models.identity import ScopeLevel, User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRoleAssignRequest, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.audit_repo = AuditRepository(session)

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        return user

    async def create_user(
        self,
        data: UserCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists.")

        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            phone_number=data.phone_number,
            organization_id=data.organization_id,
            facility_id=data.facility_id,
            is_active=True,
            is_verified=True,
        )
        await self.user_repo.create(user)

        # Assign initial roles if provided
        if data.initial_role_ids:
            for role_id in data.initial_role_ids:
                role = await self.role_repo.get_by_id(role_id)
                if role:
                    await self.user_repo.assign_role(
                        user_id=user.id,
                        role_id=role.id,
                        organization_id=user.organization_id,
                        facility_id=user.facility_id,
                        scope_level=ScopeLevel.FACILITY,
                    )

        await self.audit_repo.record_event(
            action="USER_CREATED",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=actor_id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            new_state={"email": user.email, "full_name": user.full_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self.get_by_id(user.id)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UserUpdate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        user = await self.get_by_id(user_id)
        old_state = {"full_name": user.full_name, "is_active": user.is_active}

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone_number is not None:
            user.phone_number = data.phone_number
        if data.organization_id is not None:
            user.organization_id = data.organization_id
        if data.facility_id is not None:
            user.facility_id = data.facility_id
        if data.is_active is not None:
            user.is_active = data.is_active

        await self.user_repo.update(user)

        await self.audit_repo.record_event(
            action="USER_UPDATED",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=actor_id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            old_state=old_state,
            new_state={"full_name": user.full_name, "is_active": user.is_active},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def assign_role(
        self,
        user_id: uuid.UUID,
        data: UserRoleAssignRequest,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserRole:
        user = await self.get_by_id(user_id)
        if actor_id == user.id:
            raise BadRequestException("You cannot assign roles to yourself (privilege self-escalation is blocked).")
        role = await self.role_repo.get_by_id(data.role_id)
        if not role:
            raise ResourceNotFoundException("Role", str(data.role_id))

        user_role = await self.user_repo.assign_role(
            user_id=user.id,
            role_id=role.id,
            organization_id=data.organization_id or user.organization_id,
            facility_id=data.facility_id or user.facility_id,
            scope_level=data.scope_level,
        )

        await self.audit_repo.record_event(
            action="USER_ROLE_ASSIGNED",
            resource_type="user_role",
            resource_id=str(user_role.id),
            actor_id=actor_id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            new_state={"role_code": role.code, "scope_level": data.scope_level.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user_role

    async def revoke_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        user = await self.get_by_id(user_id)
        if actor_id == user.id:
            raise BadRequestException("You cannot revoke your own role assignments.")
        if not await self.user_repo.remove_role(user.id, role_id):
            raise ResourceNotFoundException("UserRole", f"{user_id}/{role_id}")

        await self.audit_repo.record_event(
            action="USER_ROLE_REVOKED",
            resource_type="user_role",
            resource_id=f"{user_id}/{role_id}",
            actor_id=actor_id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            old_state={"role_id": str(role_id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def list_users(
        self,
        facility_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[Sequence[User], int]:
        offset = (page - 1) * page_size
        return await self.user_repo.list_paginated(
            facility_id=facility_id,
            organization_id=organization_id,
            offset=offset,
            limit=page_size,
        )
