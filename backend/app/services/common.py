"""Small helpers shared by the governance, supply-request, emergency and analytics services."""
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jurisdiction import Jurisdiction
from app.models.governance import GovernanceLevel
from app.models.identity import ScopeLevel
from app.repositories.audit_repository import AuditRepository

AuditCtx = Tuple[Optional[str], Optional[str]]

NEXT_LEVEL = {GovernanceLevel.DISTRICT: GovernanceLevel.STATE, GovernanceLevel.STATE: GovernanceLevel.NATIONAL}


def make_reference(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(4).upper()}"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def level_for(j: Jurisdiction) -> GovernanceLevel:
    if j.scope == ScopeLevel.GLOBAL:
        return GovernanceLevel.NATIONAL
    if j.scope == ScopeLevel.STATE:
        return GovernanceLevel.STATE
    return GovernanceLevel.DISTRICT


async def paginate(session: AsyncSession, stmt, order_by, page: int, page_size: int) -> Tuple[Sequence, int]:
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = await session.execute(stmt.order_by(order_by).offset((page - 1) * page_size).limit(page_size))
    return rows.scalars().unique().all(), total


class AuditMixin:
    session: AsyncSession

    async def _audit(self, action: str, resource_type: str, resource_id: Any, actor_id: Optional[uuid.UUID],
                     ctx: AuditCtx = (None, None), facility_id: Optional[uuid.UUID] = None,
                     old_state: Optional[Dict[str, Any]] = None, new_state: Optional[Dict[str, Any]] = None) -> None:
        await AuditRepository(self.session).record_event(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            actor_id=actor_id,
            facility_id=facility_id,
            old_state=old_state,
            new_state=new_state,
            ip_address=ctx[0],
            user_agent=ctx[1],
        )
