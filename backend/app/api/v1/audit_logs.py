import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_permission
from app.core.permissions import SystemPermissions
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/audit-logs", tags=["Audit & Compliance"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    dependencies=[Depends(require_permission(SystemPermissions.AUDIT_LOG_READ))],
)
async def list_audit_logs(
    facility_id: Optional[uuid.UUID] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve immutable audit trail with actor details, action timestamps, and state diffs."""
    repo = AuditRepository(session)
    offset = (page - 1) * page_size
    logs, total = await repo.list_logs(
        facility_id=facility_id,
        resource_type=resource_type,
        offset=offset,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        data=[AuditLogResponse.model_validate(log) for log in logs],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )
