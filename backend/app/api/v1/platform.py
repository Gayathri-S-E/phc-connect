"""Role 13 platform administration and the permission-driven navigation contract."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, get_current_user, get_db_session, require_permission
from app.core.permissions import SystemPermissions as P
from app.schemas.audit import AuditLogResponse
from app.schemas.common import DataResponse
from app.services.platform_service import PlatformService, navigation_for

router = APIRouter(tags=["Platform Administration & Navigation"])


@router.get("/navigation/me")
async def my_navigation(user: AuthenticatedUserContext = Depends(get_current_user)):
    """Menu items the caller is authorized for, derived from database-backed permissions (no role-name checks)."""
    return DataResponse[Dict[str, Any]](data={
        "items": navigation_for(user.permissions),
        "permissions": sorted(user.permissions),
        "roles": user.roles,
        "scope": user.get_highest_scope().value,
    })


@router.get("/platform/dashboard", dependencies=[Depends(require_permission(P.PLATFORM_DASHBOARD_VIEW))])
async def platform_dashboard(session: AsyncSession = Depends(get_db_session)):
    """System health, security telemetry, jobs and integration status (no clinical data)."""
    return DataResponse[Dict[str, Any]](data=await PlatformService(session).dashboard())


@router.get("/platform/security-events", response_model=DataResponse[List[AuditLogResponse]],
            dependencies=[Depends(require_permission(P.PLATFORM_SECURITY_READ))])
async def security_events(limit: int = Query(100, ge=1, le=500), session: AsyncSession = Depends(get_db_session)):
    events = await PlatformService(session).security_events(limit)
    return DataResponse(data=[AuditLogResponse.model_validate(e) for e in events])
