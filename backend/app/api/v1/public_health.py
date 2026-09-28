"""State Public Health Analyst (Role 11) endpoints."""
import math
import uuid
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
    require_permission,
)
from app.api.scope import resolve_jurisdiction
from app.core.permissions import SystemPermissions as P
from app.models.public_health import DataQualityStatus
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.public_health import (
    AggregateResponse,
    AggregateSubmit,
    AggregateValidate,
    AnalysisJobResponse,
    AnalysisRun,
    DataQualityAction,
    DataQualityResponse,
    IndicatorCreate,
    IndicatorResponse,
    TrendResponse,
)
from app.services.public_health_service import PublicHealthService

router = APIRouter(prefix="/public-health", tags=["State Public Health Analytics"])


def _ctx(req: RequestContext):
    return req.ip_address, req.user_agent


def _page(items, total, page, page_size, schema) -> PaginatedResponse:
    return PaginatedResponse(data=[schema.model_validate(i) for i in items],
                             pagination=PaginationMeta(page=page, page_size=page_size, total=total,
                                                       total_pages=math.ceil(total / page_size) if total else 0))


@router.get("/dashboard", dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def analyst_dashboard(user: AuthenticatedUserContext = Depends(get_current_user),
                            session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_INDICATOR_READ, session)
    return DataResponse[Dict[str, Any]](data=await PublicHealthService(session).dashboard(j))


@router.get("/indicators", response_model=DataResponse[List[IndicatorResponse]],
            dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def list_indicators(active_only: bool = True, session: AsyncSession = Depends(get_db_session)):
    return DataResponse(data=[IndicatorResponse.model_validate(i)
                              for i in await PublicHealthService(session).list_indicators(active_only)])


@router.post("/indicators", response_model=DataResponse[IndicatorResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_MANAGE))])
async def create_indicator(payload: IndicatorCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                           req: RequestContext = Depends(get_request_context),
                           session: AsyncSession = Depends(get_db_session)):
    ind = await PublicHealthService(session).create_indicator(payload, user.id, _ctx(req))
    return DataResponse(data=IndicatorResponse.model_validate(ind))


@router.post("/aggregates", response_model=DataResponse[AggregateResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.ANALYTICS_AGGREGATE_SUBMIT))])
async def submit_aggregate(payload: AggregateSubmit, user: AuthenticatedUserContext = Depends(get_current_user),
                           req: RequestContext = Depends(get_request_context),
                           session: AsyncSession = Depends(get_db_session)):
    """Submit an aggregated (non-identifiable) indicator value; duplicates for the same period are rejected."""
    j = await resolve_jurisdiction(user, P.ANALYTICS_AGGREGATE_SUBMIT, session)
    source_role = ",".join(sorted(user.roles)) or "UNKNOWN"
    agg = await PublicHealthService(session).submit_aggregate(payload, j, user.id, source_role[:60], _ctx(req))
    return DataResponse(data=AggregateResponse.model_validate(agg))


@router.get("/aggregates", response_model=PaginatedResponse[AggregateResponse],
            dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def list_aggregates(indicator_id: Optional[uuid.UUID] = None, district: Optional[str] = Query(None, max_length=100),
                          start_date: Optional[date] = None, end_date: Optional[date] = None,
                          page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                          user: AuthenticatedUserContext = Depends(get_current_user),
                          session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_INDICATOR_READ, session)
    items, total = await PublicHealthService(session).list_aggregates(j, indicator_id, district, start_date, end_date,
                                                                      page, page_size)
    return _page(items, total, page, page_size, AggregateResponse)


@router.post("/aggregates/{aggregate_id}/validate", response_model=DataResponse[AggregateResponse],
             dependencies=[Depends(require_permission(P.ANALYTICS_DATA_QUALITY_MANAGE))])
async def validate_aggregate(aggregate_id: uuid.UUID, payload: AggregateValidate,
                             user: AuthenticatedUserContext = Depends(get_current_user),
                             req: RequestContext = Depends(get_request_context),
                             session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_DATA_QUALITY_MANAGE, session)
    agg = await PublicHealthService(session).validate_aggregate(aggregate_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=AggregateResponse.model_validate(agg))


@router.get("/trends", response_model=DataResponse[TrendResponse],
            dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def health_trends(indicator_id: uuid.UUID, district: Optional[str] = Query(None, max_length=100),
                        end_date: Optional[date] = None, window_days: int = Query(30, ge=7, le=180),
                        user: AuthenticatedUserContext = Depends(get_current_user),
                        session: AsyncSession = Depends(get_db_session)):
    """Current vs previous period by district, with reporting coverage and validation status."""
    j = await resolve_jurisdiction(user, P.ANALYTICS_INDICATOR_READ, session)
    if district and j.state:
        j.ensure_covers(j.state, district)
    data = await PublicHealthService(session).trends(indicator_id, j, district, end_date, window_days)
    data["indicator"] = IndicatorResponse.model_validate(data["indicator"])
    return DataResponse(data=TrendResponse(**data))


@router.post("/analysis/run", response_model=DataResponse[AnalysisJobResponse],
             dependencies=[Depends(require_permission(P.ANALYTICS_INSIGHT_REVIEW))])
async def run_analysis(payload: AnalysisRun, user: AuthenticatedUserContext = Depends(get_current_user),
                       session: AsyncSession = Depends(get_db_session)):
    """Run automatic trend/anomaly/data-quality analysis; outputs await human review."""
    j = await resolve_jurisdiction(user, P.ANALYTICS_INSIGHT_REVIEW, session)
    job = await PublicHealthService(session).run_analysis(j, payload.period_end, payload.window_days, user.id)
    return DataResponse(data=AnalysisJobResponse.model_validate(job))


@router.get("/analysis/jobs", response_model=PaginatedResponse[AnalysisJobResponse],
            dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def list_analysis_jobs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                             session: AsyncSession = Depends(get_db_session)):
    items, total = await PublicHealthService(session).list_jobs(page, page_size)
    return _page(items, total, page, page_size, AnalysisJobResponse)


@router.get("/data-quality", response_model=PaginatedResponse[DataQualityResponse],
            dependencies=[Depends(require_permission(P.ANALYTICS_INDICATOR_READ))])
async def list_data_quality(issue_status: Optional[DataQualityStatus] = Query(None, alias="status"),
                            page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_INDICATOR_READ, session)
    items, total = await PublicHealthService(session).list_issues(j, issue_status, page, page_size)
    return _page(items, total, page, page_size, DataQualityResponse)


@router.post("/data-quality/{issue_id}/request-verification", response_model=DataResponse[DataQualityResponse],
             dependencies=[Depends(require_permission(P.ANALYTICS_DATA_QUALITY_MANAGE))])
async def request_verification(issue_id: uuid.UUID, payload: DataQualityAction,
                               user: AuthenticatedUserContext = Depends(get_current_user),
                               req: RequestContext = Depends(get_request_context),
                               session: AsyncSession = Depends(get_db_session)):
    """Ask the district to verify; creates a DATA_VERIFICATION action. Source records are not modified."""
    j = await resolve_jurisdiction(user, P.ANALYTICS_DATA_QUALITY_MANAGE, session)
    issue = await PublicHealthService(session).request_verification(issue_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=DataQualityResponse.model_validate(issue))


@router.post("/data-quality/{issue_id}/{outcome}", response_model=DataResponse[DataQualityResponse],
             dependencies=[Depends(require_permission(P.ANALYTICS_DATA_QUALITY_MANAGE))])
async def close_data_quality_issue(issue_id: uuid.UUID, outcome: Literal["resolve", "dismiss"], payload: DataQualityAction,
                                   user: AuthenticatedUserContext = Depends(get_current_user),
                                   req: RequestContext = Depends(get_request_context),
                                   session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_DATA_QUALITY_MANAGE, session)
    issue = await PublicHealthService(session).close_issue(issue_id, outcome == "resolve", payload, j, user.id, _ctx(req))
    return DataResponse(data=DataQualityResponse.model_validate(issue))
