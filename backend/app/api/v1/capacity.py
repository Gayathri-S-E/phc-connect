"""Bed availability and staff-attendance capacity visibility.

Facility endpoints: staff record ward occupancy (append-only census log) and read beds.
Roll-up endpoints: district / state / national totals restricted to the caller's jurisdiction,
with data-freshness flags (stale >24h and no-data facilities are never silently counted).
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, get_current_user, get_db_session, require_permission
from app.api.scope import ensure_facility_access, resolve_jurisdiction
from app.core.exceptions import BadRequestException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.core.permissions import SystemPermissions as P
from app.models.beds import BedCensusLog, BedInventory, WardType
from app.models.facility import Facility
from app.models.identity import ScopeLevel
from app.schemas.beds import (
    BedCensusLogResponse,
    BedInventoryResponse,
    BedOccupancyUpdate,
    FacilityBedsResponse,
)
from app.schemas.common import DataResponse
from app.services.capacity_service import CapacityService

router = APIRouter(prefix="/capacity", tags=["Bed Availability & Capacity"])


async def _get_facility(session: AsyncSession, facility_id: uuid.UUID) -> Facility:
    facility = await session.get(Facility, facility_id)
    if facility is None:
        raise ResourceNotFoundException("Facility not found.")
    return facility


@router.get(
    "/facilities/{facility_id}/beds",
    response_model=DataResponse[FacilityBedsResponse],
    summary="Current bed inventory and occupancy for a facility",
)
async def get_facility_beds(
    facility_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(require_permission(P.BEDS_READ)),
    session: AsyncSession = Depends(get_db_session),
):
    await ensure_facility_access(user_ctx, facility_id, P.BEDS_READ, session)
    await _get_facility(session, facility_id)
    return DataResponse(data=await CapacityService(session).facility_beds(facility_id))


@router.put(
    "/facilities/{facility_id}/beds/{ward_type}",
    response_model=DataResponse[BedInventoryResponse],
    summary="Update ward occupancy (and, with beds.inventory.manage, ward capacity)",
)
async def update_ward_beds(
    facility_id: uuid.UUID,
    ward_type: WardType,
    payload: BedOccupancyUpdate,
    user_ctx: AuthenticatedUserContext = Depends(require_permission(P.BEDS_OCCUPANCY_UPDATE)),
    session: AsyncSession = Depends(get_db_session),
):
    await ensure_facility_access(user_ctx, facility_id, P.BEDS_OCCUPANCY_UPDATE, session)
    await _get_facility(session, facility_id)

    row = (await session.execute(
        select(BedInventory).where(BedInventory.facility_id == facility_id, BedInventory.ward_type == ward_type)
    )).scalar_one_or_none()

    changes_capacity = payload.total_beds is not None and (row is None or payload.total_beds != row.total_beds)
    if changes_capacity or row is None:
        if not user_ctx.has_permission(P.BEDS_INVENTORY_MANAGE):
            if row is None:
                raise ResourceNotFoundException(
                    f"No {ward_type.value} ward is registered at this facility; a bed-inventory manager must create it.")
            raise PermissionDeniedException(f"Changing ward capacity requires '{P.BEDS_INVENTORY_MANAGE}'.")
        await ensure_facility_access(user_ctx, facility_id, P.BEDS_INVENTORY_MANAGE, session)
        if row is None and payload.total_beds is None:
            raise BadRequestException("total_beds is required when registering a new ward.")

    new_total = payload.total_beds if payload.total_beds is not None else row.total_beds
    if payload.occupied_beds > new_total:
        raise BadRequestException(f"occupied_beds ({payload.occupied_beds}) cannot exceed total_beds ({new_total}).")

    now = datetime.now(timezone.utc)
    prev_total = row.total_beds if row else None
    prev_occ = row.occupied_beds if row else None
    if row is None:
        row = BedInventory(facility_id=facility_id, ward_type=ward_type, total_beds=new_total,
                           occupied_beds=payload.occupied_beds, last_updated_by=user_ctx.id)
        session.add(row)
    else:
        row.total_beds = new_total
        row.occupied_beds = payload.occupied_beds
        row.last_updated_by = user_ctx.id
    row.updated_at = now  # always refresh: a re-confirmed unchanged count is still a fresh observation
    session.add(BedCensusLog(
        facility_id=facility_id, ward_type=ward_type, total_beds=new_total, occupied_beds=payload.occupied_beds,
        previous_total_beds=prev_total, previous_occupied_beds=prev_occ, recorded_by=user_ctx.id,
        note=payload.note, recorded_at=now,
    ))
    await session.flush()
    return DataResponse(data=BedInventoryResponse.model_validate(row))


@router.get(
    "/facilities/{facility_id}/beds/history",
    response_model=DataResponse[List[BedCensusLogResponse]],
    summary="Append-only bed census history for a facility",
)
async def get_bed_history(
    facility_id: uuid.UUID,
    ward_type: Optional[WardType] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    user_ctx: AuthenticatedUserContext = Depends(require_permission(P.BEDS_READ)),
    session: AsyncSession = Depends(get_db_session),
):
    await ensure_facility_access(user_ctx, facility_id, P.BEDS_READ, session)
    await _get_facility(session, facility_id)
    stmt = select(BedCensusLog).where(BedCensusLog.facility_id == facility_id)
    if ward_type:
        stmt = stmt.where(BedCensusLog.ward_type == ward_type)
    rows = (await session.execute(stmt.order_by(BedCensusLog.recorded_at.desc()).limit(limit))).scalars().all()
    return DataResponse(data=[BedCensusLogResponse.model_validate(r) for r in rows])


# --------------------------------------------------------------------------- roll-ups
def _narrow(j: Jurisdiction, level: ScopeLevel, state: Optional[str], district: Optional[str]) -> Jurisdiction:
    """Narrow the server-derived jurisdiction to a requested state/district; never widen it."""
    if level == ScopeLevel.GLOBAL:
        return j
    if j.scope == ScopeLevel.GLOBAL and j.state is None:
        if not state:
            raise BadRequestException("state is required.")
        if level == ScopeLevel.DISTRICT and not district:
            raise BadRequestException("district is required.")
    st = state or j.state
    di = district or j.district if level == ScopeLevel.DISTRICT else None
    if level == ScopeLevel.DISTRICT and not di:
        raise BadRequestException("district is required.")
    j.ensure_covers(st, di if level == ScopeLevel.DISTRICT else None)
    return Jurisdiction(level, st, di, None)


def _first_held(user_ctx: AuthenticatedUserContext, *codes: str) -> str:
    """Higher-level governance viewers may also open lower-level roll-ups within their jurisdiction."""
    for code in codes:
        if user_ctx.has_permission(code):
            return code
    raise PermissionDeniedException(f"Missing required permission: '{codes[0]}'")


@router.get("/district", response_model=DataResponse[Dict[str, Any]],
            summary="District bed availability and staff attendance roll-up")
async def district_capacity(
    state: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(
        user_ctx, _first_held(user_ctx, P.GOVERNANCE_DISTRICT_VIEW, P.GOVERNANCE_STATE_VIEW, P.GOVERNANCE_NATIONAL_VIEW), session)
    if j.is_facility_bound:
        raise PermissionDeniedException("District roll-ups require district, state or national scope.")
    nj = _narrow(j, ScopeLevel.DISTRICT, state, district)
    return DataResponse(data=await CapacityService(session).rollup(nj, "facility"))


@router.get("/state", response_model=DataResponse[Dict[str, Any]],
            summary="State bed availability and staff attendance roll-up, by district")
async def state_capacity(
    state: Optional[str] = Query(default=None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(
        user_ctx, _first_held(user_ctx, P.GOVERNANCE_STATE_VIEW, P.GOVERNANCE_NATIONAL_VIEW), session)
    if j.is_facility_bound or j.scope == ScopeLevel.DISTRICT:
        raise PermissionDeniedException("State roll-ups require state or national scope.")
    nj = _narrow(j, ScopeLevel.STATE, state, None)
    return DataResponse(data=await CapacityService(session).rollup(nj, "district"))


@router.get("/national", response_model=DataResponse[Dict[str, Any]],
            summary="National bed availability and staff attendance roll-up, by state")
async def national_capacity(
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(user_ctx, P.GOVERNANCE_NATIONAL_VIEW, session)
    if j.scope != ScopeLevel.GLOBAL:
        raise PermissionDeniedException("National roll-ups require national scope.")
    return DataResponse(data=await CapacityService(session).rollup(j, "state"))
