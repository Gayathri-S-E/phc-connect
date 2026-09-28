import uuid
from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import Permission, Role, RolePermission


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.role_permissions).joinedload(RolePermission.permission))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Role]:
        stmt = (
            select(Role)
            .where(Role.code == code)
            .options(selectinload(Role.role_permissions).joinedload(RolePermission.permission))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, active_only: bool = True) -> Sequence[Role]:
        stmt = select(Role).options(
            selectinload(Role.role_permissions).joinedload(RolePermission.permission)
        )
        if active_only:
            stmt = stmt.where(Role.is_active.is_(True))
        stmt = stmt.order_by(Role.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        return role

    async def update(self, role: Role) -> Role:
        await self.session.flush()
        return role

    async def assign_permissions(self, role_id: uuid.UUID, permission_ids: List[uuid.UUID]) -> None:
        # Clear existing permissions
        delete_stmt = select(RolePermission).where(RolePermission.role_id == role_id)
        res = await self.session.execute(delete_stmt)
        for existing in res.scalars().all():
            await self.session.delete(existing)

        # Add new permissions
        for pid in permission_ids:
            rp = RolePermission(role_id=role_id, permission_id=pid)
            self.session.add(rp)
        await self.session.flush()

    async def list_permissions(self) -> Sequence[Permission]:
        stmt = select(Permission).where(Permission.is_active.is_(True)).order_by(Permission.module, Permission.code)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_permission_by_code(self, code: str) -> Optional[Permission]:
        stmt = select(Permission).where(Permission.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_permission(self, permission: Permission) -> Permission:
        self.session.add(permission)
        await self.session.flush()
        return permission
