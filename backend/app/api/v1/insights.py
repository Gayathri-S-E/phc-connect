import math
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
    require_permission,
)
from app.api.scope import ensure_facility_access, facility_ids_in_scope
from app.core.exceptions import BadRequestException
from app.core.permissions import SystemPermissions
from app.models.intelligence import AlertSeverity, AlertType
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.intelligence import (
    AlertAcknowledgeRequest,
    AlertResponse,
    ForecastRequest,
    ForecastResponse,
    PHCDashboardResponse,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    SupplyChainDashboardResponse,
)
from app.services.insights_service import InsightsService
from app.services.supply_chain_service import SupplyChainService

router = APIRouter(tags=["Alerts, AI Forecasting & Dashboards"])

P = SystemPermissions


async def _target_facility(
    user_ctx: AuthenticatedUserContext, facility_id: Optional[uuid.UUID], permission: str, session: AsyncSession
) -> uuid.UUID:
    target = facility_id or user_ctx.facility_id
    if target is None:
        raise BadRequestException("facility_id is required when your account is not assigned to a facility.")
    await ensure_facility_access(user_ctx, target, permission, session)
    return target


# ============================================================================
# ALERTS
# ============================================================================

@router.get(
    "/alerts",
    response_model=PaginatedResponse[AlertResponse],
    dependencies=[Depends(require_permission(P.ALERTS_READ))],
)
async def list_alerts(
    state: Literal["active", "acknowledged", "all"] = Query("active"),
    severity: Optional[AlertSeverity] = Query(None),
    alert_type: Optional[AlertType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List alerts (stockout risk, cold-chain breach, shortage escalations) within the user's scope."""
    facility_ids = await facility_ids_in_scope(user_ctx, P.ALERTS_READ, session)
    acknowledged = {"active": False, "acknowledged": True, "all": None}[state]
    items, total = await SupplyChainService(session).list_alerts(
        facility_ids, acknowledged, severity, alert_type, page, page_size
    )
    return PaginatedResponse(
        data=[AlertResponse.model_validate(a) for a in items],
        pagination=PaginationMeta(
            page=page, page_size=page_size, total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


@router.post(
    "/alerts/{alert_id}/ack",
    response_model=DataResponse[AlertResponse],
    dependencies=[Depends(require_permission(P.ALERTS_ACKNOWLEDGE))],
)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    payload: Optional[AlertAcknowledgeRequest] = None,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Acknowledge an alert; the action and notes are written to the audit trail."""
    service = SupplyChainService(session)
    alert = await service.get_alert(alert_id)
    await ensure_facility_access(user_ctx, alert.facility_id, P.ALERTS_ACKNOWLEDGE, session)
    alert = await service.acknowledge_alert(
        alert, payload.notes if payload else None, user_ctx.id, (req.ip_address, req.user_agent)
    )
    return DataResponse(data=AlertResponse.model_validate(alert))


# ============================================================================
# AI: FORECAST & RISK ANALYSIS
# ============================================================================

@router.post(
    "/ai/forecast",
    response_model=DataResponse[ForecastResponse],
    dependencies=[Depends(require_permission(P.AI_FORECAST_VIEW))],
)
async def generate_forecast(
    payload: ForecastRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Generate a 30/60/90-day consumption forecast per medicine; results are persisted to forecast_records."""
    facility_id = await _target_facility(user_ctx, payload.facility_id, P.AI_FORECAST_VIEW, session)
    forecast = await InsightsService(session).forecast(facility_id, payload.medication_id, payload.horizon_days)
    return DataResponse(data=forecast)


@router.post(
    "/ai/risk-analysis",
    response_model=DataResponse[RiskAnalysisResponse],
    dependencies=[Depends(require_permission(P.AI_RISK_ANALYZE))],
)
async def risk_analysis(
    payload: RiskAnalysisRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Compute an explainable 0-100 facility vulnerability / stockout risk score."""
    facility_id = await _target_facility(user_ctx, payload.facility_id, P.AI_RISK_ANALYZE, session)
    return DataResponse(data=await InsightsService(session).risk_analysis(facility_id))


# ============================================================================
# DASHBOARDS
# ============================================================================

@router.get(
    "/dashboards/phc",
    response_model=DataResponse[PHCDashboardResponse],
    dependencies=[Depends(require_permission(P.DASHBOARDS_CLINICAL_VIEW))],
)
async def phc_dashboard(
    facility_id: Optional[uuid.UUID] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """PHC operational summary: today's patient volume, pending clinical work, and stock warnings."""
    target = await _target_facility(user_ctx, facility_id, P.DASHBOARDS_CLINICAL_VIEW, session)
    return DataResponse(data=await InsightsService(session).phc_dashboard(target))


@router.get(
    "/dashboards/supply-chain",
    response_model=DataResponse[SupplyChainDashboardResponse],
    dependencies=[Depends(require_permission(P.DASHBOARDS_SUPPLY_VIEW))],
)
async def supply_chain_dashboard(
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """District/state supply pipeline across every facility in the user's scope."""
    facility_ids = await facility_ids_in_scope(user_ctx, P.DASHBOARDS_SUPPLY_VIEW, session)
    scope = user_ctx.get_highest_scope(P.DASHBOARDS_SUPPLY_VIEW).value
    return DataResponse(data=await InsightsService(session).supply_chain_dashboard(facility_ids, scope))
