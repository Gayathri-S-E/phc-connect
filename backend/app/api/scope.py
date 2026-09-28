import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext
from app.core.authorization import check_scope_access
from app.core.exceptions import BadRequestException, PermissionDeniedException
from app.core.jurisdiction import Jurisdiction
from app.models.facility import Facility
from app.models.identity import ScopeLevel


async def resolve_facility_filter(
    user_ctx: AuthenticatedUserContext,
    facility_id: Optional[uuid.UUID],
    permission_code: str,
    session: AsyncSession,
) -> Optional[uuid.UUID]:
    """Facility to filter a list by. None (= all facilities) is only returned for GLOBAL scope."""
    target = facility_id or user_ctx.facility_id
    if target is None:
        if user_ctx.get_highest_scope(permission_code) == ScopeLevel.GLOBAL:
            return None
        raise BadRequestException("facility_id is required for your access scope.")
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=target,
        permission_code=permission_code,
        session=session,
    )
    return target


async def facility_ids_in_scope(
    user_ctx: AuthenticatedUserContext,
    permission_code: str,
    session: AsyncSession,
) -> Optional[List[uuid.UUID]]:
    """Facilities visible under the user's scope for a permission; None means all (GLOBAL)."""
    scope = user_ctx.get_highest_scope(permission_code)
    if scope == ScopeLevel.GLOBAL:
        return None
    if user_ctx.facility_id is None:
        return []
    if scope in (ScopeLevel.FACILITY, ScopeLevel.SELF):
        return [user_ctx.facility_id]

    own = await session.get(Facility, user_ctx.facility_id)
    if own is None:
        return []
    stmt = select(Facility.id).where(func.lower(func.trim(Facility.state)) == own.state.strip().lower())
    if scope == ScopeLevel.DISTRICT:
        stmt = stmt.where(func.lower(func.trim(Facility.district)) == own.district.strip().lower())
    return list((await session.execute(stmt)).scalars().all())


async def ensure_facility_access(
    user_ctx: AuthenticatedUserContext,
    facility_id: Optional[uuid.UUID],
    permission_code: str,
    session: AsyncSession,
) -> None:
    await check_scope_access(
        current_user=user_ctx,
        target_facility_id=facility_id,
        permission_code=permission_code,
        session=session,
    )


async def resolve_jurisdiction(
    user_ctx: AuthenticatedUserContext,
    permission_code: str,
    session: AsyncSession,
) -> Jurisdiction:
    """Never trusts client-supplied state/district: everything comes from the user's assigned facility."""
    if not user_ctx.has_permission(permission_code):
        raise PermissionDeniedException(f"Missing required permission: '{permission_code}'")
    scope = user_ctx.get_highest_scope(permission_code)
    if scope == ScopeLevel.GLOBAL:
        return Jurisdiction(ScopeLevel.GLOBAL, None, None, None)
    if user_ctx.facility_id is None:
        raise PermissionDeniedException("Your account has no assigned facility, so no jurisdiction can be resolved.")
    own = await session.get(Facility, user_ctx.facility_id)
    if own is None:
        raise PermissionDeniedException("Your assigned facility could not be found.")
    return Jurisdiction(scope, own.state.strip(), own.district.strip(), own.id)


async def ensure_any_facility_access(
    user_ctx: AuthenticatedUserContext,
    facility_ids: List[Optional[uuid.UUID]],
    permission_code: str,
    session: AsyncSession,
) -> None:
    last_error: Optional[Exception] = None
    for facility_id in [f for f in facility_ids if f is not None]:
        try:
            await ensure_facility_access(user_ctx, facility_id, permission_code, session)
            return
        except PermissionDeniedException as exc:
            last_error = exc
    if last_error:
        raise last_error
