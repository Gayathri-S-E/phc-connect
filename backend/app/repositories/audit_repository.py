import uuid
from typing import Any, Dict, Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_event(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None,
        old_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            organization_id=organization_id,
            facility_id=facility_id,
            old_state=old_state,
            new_state=new_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_logs(
        self,
        facility_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[AuditLog], int]:
        stmt = select(AuditLog)
        count_stmt = select(func.count(AuditLog.id))

        if facility_id:
            stmt = stmt.where(AuditLog.facility_id == facility_id)
            count_stmt = count_stmt.where(AuditLog.facility_id == facility_id)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
            count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)

        records_res = await self.session.execute(stmt)
        count_res = await self.session.execute(count_stmt)

        return records_res.scalars().all(), count_res.scalar() or 0
