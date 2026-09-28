import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
