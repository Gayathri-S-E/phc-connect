import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Any, Dict

from app.ai.llm import LLMClient, get_llm_client
from app.api.scope import ensure_facility_access, facility_ids_in_scope, resolve_jurisdiction
from app.core.exceptions import BadRequestException
from app.core.jurisdiction import norm
from app.services.forecast_federation_service import ForecastFederationService, explain_with_gemini
from app.services.vertex_forecast import VertexForecastBackend, get_vertex_backend
from app.api.deps import (
    AuthenticatedUserContext,
    get_current_user,
    get_db_session,
    require_permission,
)
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions
from app.models.identity import ScopeLevel
from app.schemas.common import DataResponse
from app.schemas.pharmacy import (
    AIAssistantQueryRequest,
    AIAssistantQueryResponse,
    AnomalyItem,
    DemandForecastResponse,
    TransferRecommendationItem,
)
from app.services.intelligence_service import IntelligenceService

router = APIRouter(tags=["Intelligence, Analytics & AI Assistant"])


@router.get(
    "/analytics/demand-forecast",
    response_model=DataResponse[List[DemandForecastResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_FORECAST_VIEW))],
)
async def get_demand_forecast(
    facility_id: Optional[uuid.UUID] = Query(None),
    medication_id: Optional[uuid.UUID] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if not target_facility_id:
        raise PermissionDeniedException("A facility_id must be provided or assigned to the user")

    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        if target_facility_id != user_ctx.user.facility_id:
            raise PermissionDeniedException("Cannot view demand forecast for another facility")
        target_facility_id = user_ctx.user.facility_id

    service = IntelligenceService(session)
    forecasts = await service.get_demand_forecast(
        facility_id=target_facility_id,
        medication_id=medication_id,
    )
    return DataResponse(data=forecasts)


@router.get(
    "/analytics/anomalies",
    response_model=DataResponse[List[AnomalyItem]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def detect_anomalies(
    facility_id: Optional[uuid.UUID] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        target_facility_id = user_ctx.user.facility_id

    service = IntelligenceService(session)
    anomalies = await service.detect_anomalies(facility_id=target_facility_id)
    return DataResponse(data=anomalies)


@router.get(
    "/analytics/transfer-recommendations",
    response_model=DataResponse[List[TransferRecommendationItem]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def get_transfer_recommendations(
    facility_id: Optional[uuid.UUID] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    target_facility_id = facility_id or user_ctx.user.facility_id
    if user_ctx.scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
        target_facility_id = user_ctx.user.facility_id

    service = IntelligenceService(session)
    recommendations = await service.get_transfer_recommendations(facility_id=target_facility_id)
    return DataResponse(data=recommendations)


@router.post(
    "/ai/assistant/query",
    response_model=DataResponse[AIAssistantQueryResponse],
    dependencies=[Depends(require_permission(SystemPermissions.AI_FORECAST_VIEW))],
)
async def query_ai_assistant(
    payload: AIAssistantQueryRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = IntelligenceService(session)
    response = await service.query_ai_assistant(
        query=payload.query,
        current_user=user_ctx.user,
        user_scope=user_ctx.scope,
        facility_id=payload.facility_id,
    )
    return DataResponse(data=response)


# ============================================================================
# Emergency-surge early warning, cross-district redistribution, federated modelling
# (all advisory; scope enforced server-side; see services/forecast_federation_service.py)
# ============================================================================
Lang = Query("en", pattern="^(en|ta|hi)$", description="Language for the optional Gemini explanation")


async def _attach_ai(result: Dict[str, Any], kind: str, evidence_key: str, det_lines: List[str], explain: bool,
                     lang: str, llm: LLMClient) -> Dict[str, Any]:
    deterministic = " ".join(det_lines) if det_lines else "No items require attention in your scope."
    if not explain:
        result.update({"explanation": deterministic, "ai_explanation": None, "ai_explanation_reason": "NOT_REQUESTED"})
        return result
    top = {"count": result["count"], evidence_key: result[evidence_key][:8]}
    result.update(await explain_with_gemini(kind, top, deterministic, lang, llm))
    return result


@router.get(
    "/analytics/surge-risk",
    response_model=DataResponse[Dict[str, Any]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def surge_risk(
    facility_id: Optional[uuid.UUID] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    medication_id: Optional[uuid.UUID] = Query(None),
    horizon_days: int = Query(30, ge=1, le=180),
    min_tier: str = Query("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    use_federated_prior: bool = Query(True),
    explain: bool = Query(False),
    lang: str = Lang,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    llm: LLMClient = Depends(get_llm_client),
):
    perm = SystemPermissions.AI_RISK_ANALYZE
    if state or district:
        j = await resolve_jurisdiction(user_ctx, perm, session)
        j.ensure_covers(state or j.state, district)
    if facility_id:
        await ensure_facility_access(user_ctx, facility_id, perm, session)
        ids = [facility_id]
    else:
        ids = await facility_ids_in_scope(user_ctx, perm, session)
    svc = ForecastFederationService(session)
    result = await svc.surge_risk(ids, medication_id, state, district, horizon_days, min_tier, use_federated_prior)
    lines = [i["explanation"] for i in result["items"][:3]]
    return DataResponse(data=await _attach_ai(result, "emergency_surge_stockout_risk", "items", lines, explain, lang, llm))


@router.get(
    "/analytics/redistribution",
    response_model=DataResponse[Dict[str, Any]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def redistribution_recommendations(
    medication_id: Optional[uuid.UUID] = Query(None),
    max_distance_km: Optional[float] = Query(None, gt=0),
    allow_cross_state: bool = Query(True),
    cross_district_only: bool = Query(False),
    donor_cover_days: int = Query(14, ge=1, le=90),
    target_cover_days: int = Query(30, ge=1, le=180),
    explain: bool = Query(False),
    lang: str = Lang,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    llm: LLMClient = Depends(get_llm_client),
):
    ids = await facility_ids_in_scope(user_ctx, SystemPermissions.AI_RISK_ANALYZE, session)
    svc = ForecastFederationService(session)
    result = await svc.redistribution(ids, medication_id, 30, donor_cover_days, target_cover_days,
                                      max_distance_km, allow_cross_state, cross_district_only)
    lines = [r["rationale"] for r in result["recommendations"][:3]]
    return DataResponse(data=await _attach_ai(result, "cross_district_redistribution", "recommendations", lines, explain, lang, llm))


async def _federation_state(user_ctx: AuthenticatedUserContext, session: AsyncSession, state_param: Optional[str],
                            require_state: bool):
    """State-level (or national) authority only; the state is derived from the caller's own facility, never trusted."""
    j = await resolve_jurisdiction(user_ctx, SystemPermissions.AI_RISK_ANALYZE, session)
    if j.scope not in (ScopeLevel.GLOBAL, ScopeLevel.STATE):
        raise PermissionDeniedException("Federated model parameters require state or national authority.")
    if j.scope == ScopeLevel.STATE:
        if state_param:
            j.ensure_covers(state_param)
        return j.state
    if require_state and not state_param:
        raise BadRequestException("state is required for national-scope callers.")
    return state_param


@router.post(
    "/analytics/federation/local-update",
    response_model=DataResponse[Dict[str, Any]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def federation_compute_local(
    state: Optional[str] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    st = await _federation_state(user_ctx, session, state, True)
    return DataResponse(data=await ForecastFederationService(session).compute_local_update(st, user_ctx.id))


@router.get(
    "/analytics/federation/local-params",
    response_model=DataResponse[List[Dict[str, Any]]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def federation_local_params(
    state: Optional[str] = Query(None),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    st = await _federation_state(user_ctx, session, state, False)
    return DataResponse(data=await ForecastFederationService(session).list_local_params(norm(st) if st else None))


@router.post(
    "/analytics/federation/aggregate",
    response_model=DataResponse[Dict[str, Any]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_RISK_ANALYZE))],
)
async def federation_aggregate(
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(user_ctx, SystemPermissions.AI_RISK_ANALYZE, session)
    if j.scope != ScopeLevel.GLOBAL:
        raise PermissionDeniedException("Only the national aggregator (GLOBAL scope) can combine state parameters.")
    return DataResponse(data=await ForecastFederationService(session).aggregate_national(user_ctx.id))


@router.get(
    "/analytics/federation/prior",
    response_model=DataResponse[List[Dict[str, Any]]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_FORECAST_VIEW))],
)
async def federation_prior(
    medication_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    """The shared national prior (aggregate parameters only) that any authorised state may pull."""
    return DataResponse(data=await ForecastFederationService(session).get_priors(medication_id))


@router.get(
    "/analytics/federation/forecast",
    response_model=DataResponse[Dict[str, Any]],
    dependencies=[Depends(require_permission(SystemPermissions.AI_FORECAST_VIEW))],
)
async def federated_forecast(
    facility_id: Optional[uuid.UUID] = Query(None),
    medication_id: Optional[uuid.UUID] = Query(None),
    horizon_days: int = Query(30, ge=1, le=180),
    backend: str = Query("local", pattern="^(local|vertex)$"),
    explain: bool = Query(False),
    lang: str = Lang,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    llm: LLMClient = Depends(get_llm_client),
    vertex: VertexForecastBackend = Depends(get_vertex_backend),
):
    target = facility_id or user_ctx.facility_id
    if not target:
        raise BadRequestException("facility_id is required.")
    await ensure_facility_access(user_ctx, target, SystemPermissions.AI_FORECAST_VIEW, session)
    result = await ForecastFederationService(session).federated_forecast(
        target, medication_id, horizon_days, vertex=vertex if backend == "vertex" else None)
    result["count"] = len(result["items"])
    lines = [i["explanation"] for i in result["items"][:3]]
    return DataResponse(data=await _attach_ai(result, "federated_demand_forecast", "items", lines, explain, lang, llm))
