"""Shared governance endpoints for district (Role 06), state (Roles 09/11) and national (Role 12) users.

Jurisdiction is always derived server-side from the caller's facility and
role scope; client-supplied state/district values are only accepted as
narrowing targets and are validated against that jurisdiction.
"""
import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse
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
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions as P
from app.models.governance import (
    ActionPriority,
    ActionStatus,
    ApprovalStatus,
    GovernanceAlertStatus,
    GovernanceLevel,
    InsightReviewStatus,
    ReportReviewStatus,
)
from app.schemas.common import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.governance import (
    ActionCreate,
    ActionDetailResponse,
    ActionResponse,
    ActionTransition,
    ApprovalClarification,
    ApprovalCreate,
    ApprovalDecision,
    ApprovalResponse,
    AssistantQuery,
    AssistantResponse,
    GovernanceAlertCreate,
    GovernanceAlertResponse,
    GovernanceAlertTransition,
    InsightResponse,
    InsightReview,
    ReportDetailResponse,
    ReportGenerate,
    ReportResponse,
    ReportReview,
    ReportTypeInfo,
    SchemeCreate,
    SchemeDetailResponse,
    SchemeProgressReport,
    SchemeRemark,
    SchemeResponse,
    SchemeTargetResponse,
    SchemeTargetSet,
)
from app.services.common import level_for
from app.services.governance_report_service import GovernanceReportService, target_view
from app.services.governance_service import GovernanceService
from app.services.role_assistant_service import RoleAssistantService

router = APIRouter(prefix="/governance", tags=["Governance (District / State / National)"])


def _ctx(req: RequestContext):
    return req.ip_address, req.user_agent


def _page(items, total: int, page: int, page_size: int, schema) -> PaginatedResponse:
    return PaginatedResponse(
        data=[schema.model_validate(i) for i in items],
        pagination=PaginationMeta(page=page, page_size=page_size, total=total,
                                  total_pages=math.ceil(total / page_size) if total else 0),
    )


def _first_held(user: AuthenticatedUserContext, *perms: str) -> str:
    for p in perms:
        if user.has_permission(p):
            return p
    raise PermissionDeniedException("Missing required permission: one of " + ", ".join(f"'{p}'" for p in perms))


# ============================================================================ ACTIONS
ACTION_PERMS = (P.GOVERNANCE_ACTION_MANAGE, P.GOVERNANCE_ACTION_CREATE, P.GOVERNANCE_ACTION_RESPOND)


@router.get("/actions", response_model=PaginatedResponse[ActionResponse])
async def list_actions(
    action_status: Optional[ActionStatus] = Query(None, alias="status"),
    category: Optional[str] = Query(None, max_length=60),
    priority: Optional[ActionPriority] = None,
    level: Optional[GovernanceLevel] = None,
    assigned_to_me: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Pending district actions, state follow-ups and national coordination requests within your jurisdiction."""
    j = await resolve_jurisdiction(user, _first_held(user, *ACTION_PERMS), session)
    items, total = await GovernanceService(session).list_actions(j, user.id, action_status, category, priority, level,
                                                                  assigned_to_me, page, page_size)
    return _page(items, total, page, page_size, ActionResponse)


@router.post("/actions", response_model=DataResponse[ActionDetailResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.GOVERNANCE_ACTION_CREATE))])
async def create_action(payload: ActionCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                        req: RequestContext = Depends(get_request_context),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_ACTION_CREATE, session)
    action = await GovernanceService(session).create_action(payload, j, user.id, _ctx(req))
    return DataResponse(data=ActionDetailResponse.model_validate(action))


@router.get("/actions/{action_id}", response_model=DataResponse[ActionDetailResponse])
async def get_action(action_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                     session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _first_held(user, *ACTION_PERMS), session)
    return DataResponse(data=ActionDetailResponse.model_validate(await GovernanceService(session).get_action(action_id, j, user.id)))


@router.post("/actions/{action_id}/transitions", response_model=DataResponse[ActionDetailResponse])
async def transition_action(action_id: uuid.UUID, payload: ActionTransition,
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            req: RequestContext = Depends(get_request_context),
                            session: AsyncSession = Depends(get_db_session)):
    """Assign, review, respond, request clarification, resolve (with evidence), close, escalate or comment."""
    perm = _first_held(user, *ACTION_PERMS)
    j = await resolve_jurisdiction(user, perm, session)
    action = await GovernanceService(session).transition_action(
        action_id, payload, j, user.id, user.has_permission(P.GOVERNANCE_ACTION_MANAGE), _ctx(req))
    return DataResponse(data=ActionDetailResponse.model_validate(action))


# ============================================================================ ALERTS
@router.get("/alerts", response_model=PaginatedResponse[GovernanceAlertResponse],
            dependencies=[Depends(require_permission(P.GOVERNANCE_ALERT_READ))])
async def list_alerts(
    alert_status: Optional[GovernanceAlertStatus] = Query(None, alias="status"),
    category: Optional[str] = Query(None, max_length=60),
    severity: Optional[ActionPriority] = None,
    district: Optional[str] = Query(None, max_length=100),
    open_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_ALERT_READ, session)
    items, total = await GovernanceService(session).list_alerts(j, alert_status, category, severity, district, open_only,
                                                                 page, page_size)
    return _page(items, total, page, page_size, GovernanceAlertResponse)


@router.post("/alerts", response_model=DataResponse[GovernanceAlertResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.GOVERNANCE_ALERT_MANAGE))])
async def raise_alert(payload: GovernanceAlertCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                      req: RequestContext = Depends(get_request_context),
                      session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_ALERT_MANAGE, session)
    alert = await GovernanceService(session).create_alert(payload, j, user.id, _ctx(req))
    return DataResponse(data=GovernanceAlertResponse.model_validate(alert))


@router.get("/alerts/{alert_id}", response_model=DataResponse[GovernanceAlertResponse],
            dependencies=[Depends(require_permission(P.GOVERNANCE_ALERT_READ))])
async def get_alert(alert_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                    session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_ALERT_READ, session)
    return DataResponse(data=GovernanceAlertResponse.model_validate(await GovernanceService(session).get_alert(alert_id, j)))


@router.post("/alerts/{alert_id}/transitions", response_model=DataResponse[GovernanceAlertResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_ALERT_MANAGE))])
async def transition_alert(alert_id: uuid.UUID, payload: GovernanceAlertTransition,
                           user: AuthenticatedUserContext = Depends(get_current_user),
                           req: RequestContext = Depends(get_request_context),
                           session: AsyncSession = Depends(get_db_session)):
    """Acknowledge, review, set human-assigned severity, escalate upward, resolve or dismiss."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_ALERT_MANAGE, session)
    alert = await GovernanceService(session).transition_alert(alert_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=GovernanceAlertResponse.model_validate(alert))


# ============================================================================ REPORTS
REPORT_PERMS = (P.GOVERNANCE_REPORT_REVIEW, P.GOVERNANCE_REPORT_GENERATE)


@router.get("/reports/types", response_model=DataResponse[list[ReportTypeInfo]],
            dependencies=[Depends(require_permission(P.GOVERNANCE_REPORT_GENERATE))])
async def report_types(user: AuthenticatedUserContext = Depends(get_current_user),
                       session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_REPORT_GENERATE, session)
    return DataResponse(data=[ReportTypeInfo(**t) for t in GovernanceReportService.report_types(level_for(j))])


@router.get("/reports", response_model=PaginatedResponse[ReportResponse])
async def list_reports(
    report_type: Optional[str] = Query(None, max_length=60),
    review_status: Optional[ReportReviewStatus] = None,
    level: Optional[GovernanceLevel] = None,
    district: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(user, _first_held(user, *REPORT_PERMS), session)
    items, total = await GovernanceReportService(session).list_reports(j, user.id, report_type, review_status, level,
                                                                       district, page, page_size)
    return _page(items, total, page, page_size, ReportResponse)


@router.post("/reports/generate", response_model=DataResponse[ReportDetailResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.GOVERNANCE_REPORT_GENERATE))])
async def generate_report(payload: ReportGenerate, user: AuthenticatedUserContext = Depends(get_current_user),
                          req: RequestContext = Depends(get_request_context),
                          session: AsyncSession = Depends(get_db_session)):
    """Generate a report snapshot from live aggregates (labelled with period, sources, generation time)."""
    j = await resolve_jurisdiction(user, P.GOVERNANCE_REPORT_GENERATE, session)
    report = await GovernanceReportService(session).generate(payload, j, user.id, _ctx(req))
    return DataResponse(data=ReportDetailResponse.model_validate(report))


@router.get("/reports/{report_id}", response_model=DataResponse[ReportDetailResponse])
async def get_report(report_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                     session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _first_held(user, *REPORT_PERMS), session)
    return DataResponse(data=ReportDetailResponse.model_validate(
        await GovernanceReportService(session).get_report(report_id, j, user.id)))


@router.get("/reports/{report_id}/export", response_class=PlainTextResponse)
async def export_report(report_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                        req: RequestContext = Depends(get_request_context),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _first_held(user, *REPORT_PERMS), session)
    service = GovernanceReportService(session)
    report = await service.get_report(report_id, j, user.id)
    await service._audit("GOVERNANCE_REPORT_EXPORTED", "governance_report", report.id, user.id, _ctx(req))
    return PlainTextResponse(service.to_csv(report), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{report.reference}.csv"'})


@router.post("/reports/{report_id}/submit", response_model=DataResponse[ReportResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_REPORT_GENERATE))])
async def submit_report(report_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                        req: RequestContext = Depends(get_request_context),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_REPORT_GENERATE, session)
    return DataResponse(data=ReportResponse.model_validate(
        await GovernanceReportService(session).submit(report_id, j, user.id, _ctx(req))))


@router.post("/reports/{report_id}/review", response_model=DataResponse[ReportResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_REPORT_REVIEW))])
async def review_report(report_id: uuid.UUID, payload: ReportReview,
                        user: AuthenticatedUserContext = Depends(get_current_user),
                        req: RequestContext = Depends(get_request_context),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_REPORT_REVIEW, session)
    return DataResponse(data=ReportResponse.model_validate(
        await GovernanceReportService(session).review(report_id, payload, j, user.id, _ctx(req))))


# ============================================================================ APPROVALS
@router.get("/approvals", response_model=PaginatedResponse[ApprovalResponse])
async def list_approvals(
    approval_status: Optional[ApprovalStatus] = Query(None, alias="status"),
    mine: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    perm = _first_held(user, P.GOVERNANCE_APPROVAL_DECIDE, P.GOVERNANCE_APPROVAL_REQUEST)
    j = await resolve_jurisdiction(user, perm, session)
    items, total = await GovernanceService(session).list_approvals(
        j, user.id, approval_status, mine or perm == P.GOVERNANCE_APPROVAL_REQUEST, page, page_size)
    return _page(items, total, page, page_size, ApprovalResponse)


@router.post("/approvals", response_model=DataResponse[ApprovalResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.GOVERNANCE_APPROVAL_REQUEST))])
async def create_approval(payload: ApprovalCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                          req: RequestContext = Depends(get_request_context),
                          session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_APPROVAL_REQUEST, session)
    return DataResponse(data=ApprovalResponse.model_validate(
        await GovernanceService(session).create_approval(payload, j, user.id, _ctx(req))))


@router.get("/approvals/{request_id}", response_model=DataResponse[ApprovalResponse])
async def get_approval(request_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                       session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, _first_held(user, P.GOVERNANCE_APPROVAL_DECIDE, P.GOVERNANCE_APPROVAL_REQUEST), session)
    return DataResponse(data=ApprovalResponse.model_validate(await GovernanceService(session).get_approval(request_id, j, user.id)))


@router.post("/approvals/{request_id}/decision", response_model=DataResponse[ApprovalResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_APPROVAL_DECIDE))])
async def decide_approval(request_id: uuid.UUID, payload: ApprovalDecision,
                          user: AuthenticatedUserContext = Depends(get_current_user),
                          req: RequestContext = Depends(get_request_context),
                          session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_APPROVAL_DECIDE, session)
    return DataResponse(data=ApprovalResponse.model_validate(
        await GovernanceService(session).decide_approval(request_id, payload, j, user.id, _ctx(req))))


@router.post("/approvals/{request_id}/clarification", response_model=DataResponse[ApprovalResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_APPROVAL_REQUEST))])
async def clarify_approval(request_id: uuid.UUID, payload: ApprovalClarification,
                           user: AuthenticatedUserContext = Depends(get_current_user),
                           req: RequestContext = Depends(get_request_context),
                           session: AsyncSession = Depends(get_db_session)):
    return DataResponse(data=ApprovalResponse.model_validate(
        await GovernanceService(session).clarify_approval(request_id, payload, user.id, _ctx(req))))


# ============================================================================ SCHEMES
def _scheme_detail(scheme) -> SchemeDetailResponse:
    base = SchemeResponse.model_validate(scheme).model_dump()
    return SchemeDetailResponse(**base, targets=[SchemeTargetResponse(**target_view(t)) for t in scheme.targets])


@router.get("/schemes", response_model=DataResponse[list[SchemeDetailResponse]],
            dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_READ))])
async def list_schemes(user: AuthenticatedUserContext = Depends(get_current_user),
                       session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_READ, session)
    return DataResponse(data=[_scheme_detail(s) for s in await GovernanceReportService(session).list_schemes(j)])


@router.post("/schemes", response_model=DataResponse[SchemeDetailResponse], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_MANAGE))])
async def create_scheme(payload: SchemeCreate, user: AuthenticatedUserContext = Depends(get_current_user),
                        req: RequestContext = Depends(get_request_context),
                        session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_MANAGE, session)
    service = GovernanceReportService(session)
    scheme = await service.create_scheme(payload, j, user.id, _ctx(req))
    return DataResponse(data=_scheme_detail(await service.get_scheme(scheme.id, j)))


@router.get("/schemes/{scheme_id}", response_model=DataResponse[SchemeDetailResponse],
            dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_READ))])
async def get_scheme(scheme_id: uuid.UUID, user: AuthenticatedUserContext = Depends(get_current_user),
                     session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_READ, session)
    return DataResponse(data=_scheme_detail(await GovernanceReportService(session).get_scheme(scheme_id, j)))


@router.put("/schemes/{scheme_id}/targets", response_model=DataResponse[SchemeTargetResponse],
            dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_MANAGE))])
async def set_scheme_target(scheme_id: uuid.UUID, payload: SchemeTargetSet,
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            req: RequestContext = Depends(get_request_context),
                            session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_MANAGE, session)
    t = await GovernanceReportService(session).set_target(scheme_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=SchemeTargetResponse(**target_view(t)))


@router.post("/scheme-targets/{target_id}/progress", response_model=DataResponse[SchemeTargetResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_REPORT))])
async def report_scheme_progress(target_id: uuid.UUID, payload: SchemeProgressReport,
                                 user: AuthenticatedUserContext = Depends(get_current_user),
                                 req: RequestContext = Depends(get_request_context),
                                 session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_REPORT, session)
    t = await GovernanceReportService(session).report_progress(target_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=SchemeTargetResponse(**target_view(t)))


@router.post("/scheme-targets/{target_id}/remarks", response_model=DataResponse[SchemeTargetResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_SCHEME_MANAGE))])
async def add_scheme_remark(target_id: uuid.UUID, payload: SchemeRemark,
                            user: AuthenticatedUserContext = Depends(get_current_user),
                            req: RequestContext = Depends(get_request_context),
                            session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.GOVERNANCE_SCHEME_MANAGE, session)
    t = await GovernanceReportService(session).add_remark(target_id, payload, j, user.id, _ctx(req))
    return DataResponse(data=SchemeTargetResponse(**target_view(t)))


# ============================================================================ INSIGHTS (AI, human-reviewed)
INSIGHT_PERMS = (P.ANALYTICS_INSIGHT_REVIEW, P.GOVERNANCE_STATE_VIEW, P.GOVERNANCE_NATIONAL_VIEW)


@router.get("/insights", response_model=PaginatedResponse[InsightResponse])
async def list_insights(
    level: Optional[GovernanceLevel] = None,
    review_status: Optional[InsightReviewStatus] = None,
    insight_type: Optional[str] = Query(None, max_length=60),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    j = await resolve_jurisdiction(user, _first_held(user, *INSIGHT_PERMS), session)
    items, total = await GovernanceService(session).list_insights(j, level, review_status, insight_type, page, page_size)
    return _page(items, total, page, page_size, InsightResponse)


@router.post("/insights/{insight_id}/review", response_model=DataResponse[InsightResponse],
             dependencies=[Depends(require_permission(P.ANALYTICS_INSIGHT_REVIEW))])
async def review_insight(insight_id: uuid.UUID, payload: InsightReview,
                         user: AuthenticatedUserContext = Depends(get_current_user),
                         req: RequestContext = Depends(get_request_context),
                         session: AsyncSession = Depends(get_db_session)):
    j = await resolve_jurisdiction(user, P.ANALYTICS_INSIGHT_REVIEW, session)
    return DataResponse(data=InsightResponse.model_validate(
        await GovernanceService(session).review_insight(insight_id, payload, j, user.id, _ctx(req))))


# ============================================================================ ROLE AI ASSISTANTS
ASSISTANT_PERMISSION = {
    "DHO": P.GOVERNANCE_DISTRICT_VIEW,
    "DSCO": P.SUPPLY_REQUEST_REVIEW,
    "EMERGENCY": P.EMERGENCY_INCIDENT_MANAGE,
    "STATE_ADMIN": P.GOVERNANCE_STATE_VIEW,
    "STATE_SUPPLY": P.SUPPLY_ALLOCATION_MANAGE,
    "ANALYST": P.ANALYTICS_INDICATOR_READ,
    "NATIONAL": P.GOVERNANCE_NATIONAL_VIEW,
}


@router.get("/assistants", response_model=DataResponse[list[str]],
            dependencies=[Depends(require_permission(P.GOVERNANCE_AI_ASSIST))])
async def my_assistants(user: AuthenticatedUserContext = Depends(get_current_user)):
    """Assistants available to the caller, derived from permissions."""
    return DataResponse(data=[k for k, p in ASSISTANT_PERMISSION.items() if user.has_permission(p)])


@router.post("/assistant/{assistant}", response_model=DataResponse[AssistantResponse],
             dependencies=[Depends(require_permission(P.GOVERNANCE_AI_ASSIST))])
async def ask_assistant(assistant: str, payload: AssistantQuery,
                        user: AuthenticatedUserContext = Depends(get_current_user),
                        session: AsyncSession = Depends(get_db_session)):
    """Role-specific, jurisdiction-scoped advisory assistant. Never takes actions."""
    key = assistant.upper()
    perm = ASSISTANT_PERMISSION.get(key)
    if perm is None:
        raise PermissionDeniedException(f"Unknown assistant '{assistant}'.")
    j = await resolve_jurisdiction(user, perm, session)
    result = await RoleAssistantService(session).ask(key, payload.question, j, user.id, payload.context_reference,
                                                     payload.language)
    return DataResponse(data=AssistantResponse(**result))
