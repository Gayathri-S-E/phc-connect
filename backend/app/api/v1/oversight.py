"""District (Role 06), State (Role 09) and National (Role 12) oversight dashboards.

All figures are live aggregates; no patient identifiers are returned.
"""
import uuid
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, get_current_user, get_db_session, require_permission
from app.api.scope import resolve_jurisdiction
from app.core.exceptions import ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.core.permissions import SystemPermissions as P
from app.models.governance import (
    ActionStatus,
    ApprovalRequest,
    ApprovalStatus,
    GovernanceAction,
    GovernanceAlert,
    GovernanceAlertStatus,
    GovernanceReport,
    InsightReviewStatus,
    AIInsight,
    ReportReviewStatus,
)
from app.models.identity import ScopeLevel
from app.models.supply_chain import SupplyHealthImpact, SupplyRequest, PurchaseRequestUrgency
from app.schemas.common import DataResponse
from app.services.common import level_for, utcnow
from app.services.health_aggregation_service import HealthAggregationService, period
from app.services.supply_request_service import OPEN_REQUEST_STATES

district_router = APIRouter(prefix="/district", tags=["District Health Officer"])
state_router = APIRouter(prefix="/state", tags=["State Health Administration"])
national_router = APIRouter(prefix="/national", tags=["National Health Authority"])

OPEN_ACTION = [ActionStatus.PENDING, ActionStatus.IN_REVIEW, ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS,
               ActionStatus.RESPONDED, ActionStatus.CLARIFICATION_REQUESTED]
OPEN_ALERT = [GovernanceAlertStatus.OPEN, GovernanceAlertStatus.ACKNOWLEDGED, GovernanceAlertStatus.UNDER_REVIEW]


async def _count(session: AsyncSession, stmt) -> int:
    return (await session.execute(stmt)).scalar_one() or 0


def _dcol(j: Jurisdiction, model):
    return model.district if j.scope not in (ScopeLevel.STATE, ScopeLevel.GLOBAL) else None


async def _governance_counts(session: AsyncSession, j: Jurisdiction) -> Dict[str, Any]:
    my_level = level_for(j)
    alerts_by_cat = dict((await session.execute(j.filter(
        select(GovernanceAlert.category, func.count()).where(GovernanceAlert.status.in_(OPEN_ALERT))
        .group_by(GovernanceAlert.category), GovernanceAlert.state, _dcol(j, GovernanceAlert)))).all())
    return {
        "open_alerts": sum(alerts_by_cat.values()),
        "open_alerts_by_category": alerts_by_cat,
        "pending_actions": await _count(session, j.filter(select(func.count(GovernanceAction.id)).where(
            GovernanceAction.status.in_(OPEN_ACTION), GovernanceAction.level == my_level),
            GovernanceAction.state, _dcol(j, GovernanceAction))),
        "overdue_actions": await _count(session, j.filter(select(func.count(GovernanceAction.id)).where(
            GovernanceAction.status.in_(OPEN_ACTION), GovernanceAction.level == my_level,
            GovernanceAction.due_at.is_not(None), GovernanceAction.due_at < utcnow()),
            GovernanceAction.state, _dcol(j, GovernanceAction))),
        "reports_awaiting_review": await _count(session, j.filter(select(func.count(GovernanceReport.id)).where(
            GovernanceReport.review_status.in_([ReportReviewStatus.SUBMITTED, ReportReviewStatus.UNDER_REVIEW]),
            GovernanceReport.submitted_to_level == my_level), GovernanceReport.state, None)),
        "unacknowledged_supply_impacts": await _count(session, j.filter(select(func.count(SupplyHealthImpact.id)).where(
            SupplyHealthImpact.acknowledged_by.is_(None)), SupplyHealthImpact.state, _dcol(j, SupplyHealthImpact))),
        "open_supply_requests": await _count(session, j.filter(select(func.count(SupplyRequest.id)).where(
            SupplyRequest.status.in_(OPEN_REQUEST_STATES)), SupplyRequest.state, _dcol(j, SupplyRequest))),
        "open_emergency_supply_requests": await _count(session, j.filter(select(func.count(SupplyRequest.id)).where(
            SupplyRequest.status.in_(OPEN_REQUEST_STATES), SupplyRequest.priority == PurchaseRequestUrgency.EMERGENCY),
            SupplyRequest.state, _dcol(j, SupplyRequest))),
    }


async def _dashboard(session: AsyncSession, j: Jurisdiction, start: date, end: date, group: Optional[str]) -> dict:
    agg = HealthAggregationService(session)
    facilities = await agg.facilities(j)
    snaps = await agg.facility_snapshots(facilities, start, end)
    body = {
        "as_of": utcnow(), "scope": j.label, "period": {"start": start, "end": end},
        "data_classification": "ACTUAL_REPORTED",
        "totals": agg.totals(snaps),
        "active_emergencies": await agg.active_emergency_count(j),
        "governance": await _governance_counts(session, j),
        "daily_series": await agg.daily_series([f.id for f in facilities], start, end),
        "attention": [
            {k: s[k] for k in ("facility_id", "facility_name", "district", "state", "operational_status", "status_reasons")}
            for s in snaps if s["operational_status"] in ("NEEDS_ATTENTION", "DISRUPTED")
        ][:20],
    }
    if group:
        body[f"{group}s"] = await agg.group_by_region(snaps, group)
    else:
        body["facilities"] = snaps
    return body


# ============================================================================ DISTRICT (Role 06)
@district_router.get("/dashboard", dependencies=[Depends(require_permission(P.GOVERNANCE_DISTRICT_VIEW))])
async def district_dashboard(start_date: Optional[date] = None, end_date: Optional[date] = None,
                             user: AuthenticatedUserContext = Depends(get_current_user),
                             session: AsyncSession = Depends(get_db_session)):
    """District overview: PHC status, patient/service volume, staff availability, alerts, actions, supply impact."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_DISTRICT_VIEW, session)
    start, end = period(start_date, end_date, 1)
    return DataResponse[Dict[str, Any]](data=await _dashboard(session, j, start, end, None))


@district_router.get("/facilities/{facility_id}", dependencies=[Depends(require_permission(P.GOVERNANCE_DISTRICT_VIEW))])
async def district_facility(facility_id: uuid.UUID, start_date: Optional[date] = None, end_date: Optional[date] = None,
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            session: AsyncSession = Depends(get_db_session)):
    """One PHC's aggregated status within the caller's district (no patient-level data)."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_DISTRICT_VIEW, session)
    agg = HealthAggregationService(session)
    facility = next((f for f in await agg.facilities(j, active_only=False) if f.id == facility_id), None)
    if not facility:
        raise ResourceNotFoundException("Facility", str(facility_id))
    start, end = period(start_date, end_date, 7)
    snap = (await agg.facility_snapshots([facility], start, end))[0]
    snap["daily_series"] = await agg.daily_series([facility.id], start, end)
    snap["period"] = {"start": start, "end": end}
    return DataResponse[Dict[str, Any]](data=snap)


@district_router.get("/analytics", dependencies=[Depends(require_permission(P.GOVERNANCE_DISTRICT_VIEW))])
async def district_analytics(start_date: Optional[date] = None, end_date: Optional[date] = None,
                             facility_id: Optional[uuid.UUID] = None,
                             user: AuthenticatedUserContext = Depends(get_current_user),
                             session: AsyncSession = Depends(get_db_session)):
    """Administrative trends (volume, consultations, referrals) and PHC comparison for planning."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_DISTRICT_VIEW, session)
    agg = HealthAggregationService(session)
    start, end = period(start_date, end_date, 30)
    facilities = [f for f in await agg.facilities(j) if facility_id is None or f.id == facility_id]
    if facility_id and not facilities:
        raise ResourceNotFoundException("Facility", str(facility_id))
    snaps = await agg.facility_snapshots(facilities, start, end)
    return DataResponse[Dict[str, Any]](data={
        "scope": j.label, "period": {"start": start, "end": end}, "data_classification": "ACTUAL_REPORTED",
        "daily_series": await agg.daily_series([f.id for f in facilities], start, end),
        "comparison": [{k: s[k] for k in ("facility_id", "facility_name", "patient_volume", "consultations",
                                          "referrals", "staff_present_today", "staff_assigned", "stockout_items",
                                          "operational_status")} for s in snaps],
        "totals": agg.totals(snaps),
    })


# ============================================================================ STATE (Role 09)
@state_router.get("/dashboard", dependencies=[Depends(require_permission(P.GOVERNANCE_STATE_VIEW))])
async def state_dashboard(start_date: Optional[date] = None, end_date: Optional[date] = None,
                          user: AuthenticatedUserContext = Depends(get_current_user),
                          session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_STATE_VIEW, session)
    start, end = period(start_date, end_date, 7)
    body = await _dashboard(session, j, start, end, "district")
    body["governance"]["pending_approvals"] = await _count(session, j.filter(
        select(func.count(ApprovalRequest.id)).where(ApprovalRequest.status == ApprovalStatus.PENDING),
        ApprovalRequest.state, None))
    body["governance"]["insights_pending_review"] = await _count(session, j.filter(
        select(func.count(AIInsight.id)).where(AIInsight.review_status == InsightReviewStatus.PENDING_REVIEW),
        AIInsight.state, None))
    return DataResponse[Dict[str, Any]](data=body)


@state_router.get("/districts", dependencies=[Depends(require_permission(P.GOVERNANCE_STATE_VIEW))])
async def state_districts(start_date: Optional[date] = None, end_date: Optional[date] = None,
                          user: AuthenticatedUserContext = Depends(get_current_user),
                          session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_STATE_VIEW, session)
    start, end = period(start_date, end_date, 7)
    agg = HealthAggregationService(session)
    snaps = await agg.facility_snapshots(await agg.facilities(j), start, end)
    return DataResponse[Dict[str, Any]](data={"scope": j.label, "period": {"start": start, "end": end},
                                              "districts": await agg.group_by_region(snaps, "district")})


@state_router.get("/districts/{district}/summary", dependencies=[Depends(require_permission(P.GOVERNANCE_STATE_VIEW))])
async def state_district_summary(district: str, start_date: Optional[date] = None, end_date: Optional[date] = None,
                                 user: AuthenticatedUserContext = Depends(get_current_user),
                                 session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_STATE_VIEW, session)
    state = j.state
    if j.scope == ScopeLevel.GLOBAL:
        raise ResourceNotFoundException("District", district)
    j.ensure_covers(state, district)
    dj = Jurisdiction(ScopeLevel.DISTRICT, state, district, None)
    start, end = period(start_date, end_date, 7)
    body = await _dashboard(session, dj, start, end, None)
    if not body["facilities"]:
        raise ResourceNotFoundException("District", district)
    return DataResponse[Dict[str, Any]](data=body)


# ============================================================================ NATIONAL (Role 12)
@national_router.get("/dashboard", dependencies=[Depends(require_permission(P.GOVERNANCE_NATIONAL_VIEW))])
async def national_dashboard(start_date: Optional[date] = None, end_date: Optional[date] = None,
                             user: AuthenticatedUserContext = Depends(get_current_user),
                             session: AsyncSession = Depends(get_db_session)):
    """State-level aggregates only; national users do not drill into facilities or patients."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_NATIONAL_VIEW, session)
    start, end = period(start_date, end_date, 7)
    body = await _dashboard(session, j, start, end, "state")
    body.pop("attention", None)
    return DataResponse[Dict[str, Any]](data=body)


@national_router.get("/supply-chain-overview", dependencies=[Depends(require_permission(P.GOVERNANCE_NATIONAL_VIEW))])
async def national_supply_overview(user: AuthenticatedUserContext = Depends(get_current_user),
                                   session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_NATIONAL_VIEW, session)
    agg = HealthAggregationService(session)
    today = date.today()
    snaps = await agg.facility_snapshots(await agg.facilities(j), today, today)
    states = await agg.group_by_region(snaps, "state")
    req_rows = (await session.execute(j.filter(
        select(SupplyRequest.state, SupplyRequest.priority, func.count()).where(SupplyRequest.status.in_(OPEN_REQUEST_STATES))
        .group_by(SupplyRequest.state, SupplyRequest.priority), SupplyRequest.state, None))).all()
    by_state: Dict[str, Dict[str, int]] = {}
    for s, pr, n in req_rows:
        by_state.setdefault(s, {})[pr.value] = n
    return DataResponse[Dict[str, Any]](data={
        "as_of": utcnow(), "scope": j.label,
        "states": [{"state": r["state"], "facilities": r["facilities"], "low_stock_items": r["low_stock_items"],
                    "stockout_items": r["stockout_items"], "open_shortages": r["open_shortages"],
                    "open_supply_requests": by_state.get(r["state"], {})} for r in states],
    })
