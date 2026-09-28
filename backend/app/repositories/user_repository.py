import uuid
from typing import List, Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import Role, RolePermission, ScopeLevel, User, UserRole, UserSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).joinedload(UserRole.role).selectinload(Role.role_permissions).joinedload(RolePermission.permission)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(func.lower(User.email) == func.lower(email))
            .options(
                selectinload(User.user_roles).joinedload(UserRole.role).selectinload(Role.role_permissions).joinedload(RolePermission.permission)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user

    async def list_paginated(
        self,
        facility_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[User], int]:
        stmt = select(User).options(
            selectinload(User.user_roles).joinedload(UserRole.role)
        )
        count_stmt = select(func.count(User.id))

        if facility_id:
            stmt = stmt.where(User.facility_id == facility_id)
            count_stmt = count_stmt.where(User.facility_id == facility_id)
        elif organization_id:
            stmt = stmt.where(User.organization_id == organization_id)
            count_stmt = count_stmt.where(User.organization_id == organization_id)

        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)

        records_res = await self.session.execute(stmt)
        count_res = await self.session.execute(count_stmt)

        return records_res.scalars().all(), count_res.scalar() or 0

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None,
        scope_level: ScopeLevel = ScopeLevel.FACILITY,
    ) -> UserRole:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
            facility_id=facility_id,
            scope_level=scope_level,
        )
        self.session.add(user_role)
        await self.session.flush()
        return user_role

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        res = await self.session.execute(stmt)
        user_role = res.scalar_one_or_none()
        if user_role:
            await self.session.delete(user_role)
            await self.session.flush()
            return True
        return False

    async def create_session(self, session_obj: UserSession) -> UserSession:
        self.session.add(session_obj)
        await self.session.flush()
        return session_obj

    async def get_session_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.is_revoked.is_(False),
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke_session(self, session_obj: UserSession) -> None:
        session_obj.is_revoked = True
        await self.session.flush()
