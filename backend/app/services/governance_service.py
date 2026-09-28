"""Shared governance workflows: actions/coordination requests, health alerts, approvals, insight review.

Used by the DHO (district), State Health Administrator (state), Public Health
Analyst (state) and National Health Authority (national). Every query is scoped
by a server-derived Jurisdiction; every state change is audited.
"""
import uuid
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.models.facility import Facility
from app.models.governance import (
    ActionPriority,
    ActionStatus,
    ActionUpdateType,
    AIInsight,
    AlertOrigin,
    ApprovalRequest,
    ApprovalStatus,
    GovernanceAction,
    GovernanceActionUpdate,
    GovernanceAlert,
    GovernanceAlertStatus,
    GovernanceLevel,
    InsightReviewStatus,
)
from app.models.identity import ScopeLevel, User
from app.schemas.governance import (
    ActionCreate,
    ActionTransition,
    ApprovalClarification,
    ApprovalCreate,
    ApprovalDecision,
    GovernanceAlertCreate,
    GovernanceAlertTransition,
    InsightReview,
)
from app.services.common import NEXT_LEVEL, AuditCtx, AuditMixin, level_for, make_reference, paginate, utcnow

TERMINAL_ACTION = {ActionStatus.RESOLVED, ActionStatus.CLOSED, ActionStatus.ESCALATED}
ACTION_TRANSITIONS = {
    "ASSIGN": ({ActionStatus.PENDING, ActionStatus.IN_REVIEW, ActionStatus.ASSIGNED, ActionStatus.CLARIFICATION_REQUESTED},
               ActionStatus.ASSIGNED),
    "START_REVIEW": ({ActionStatus.PENDING, ActionStatus.RESPONDED}, ActionStatus.IN_REVIEW),
    "START_WORK": ({ActionStatus.ASSIGNED, ActionStatus.PENDING, ActionStatus.CLARIFICATION_REQUESTED}, ActionStatus.IN_PROGRESS),
    "RESPOND": ({ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS, ActionStatus.CLARIFICATION_REQUESTED, ActionStatus.PENDING},
                ActionStatus.RESPONDED),
    "REQUEST_CLARIFICATION": ({ActionStatus.RESPONDED, ActionStatus.IN_REVIEW}, ActionStatus.CLARIFICATION_REQUESTED),
    "RESOLVE": ({ActionStatus.PENDING, ActionStatus.IN_REVIEW, ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS,
                 ActionStatus.RESPONDED}, ActionStatus.RESOLVED),
    "CLOSE": ({ActionStatus.RESOLVED}, ActionStatus.CLOSED),
    "ESCALATE": ({ActionStatus.PENDING, ActionStatus.IN_REVIEW, ActionStatus.ASSIGNED, ActionStatus.IN_PROGRESS,
                  ActionStatus.RESPONDED, ActionStatus.CLARIFICATION_REQUESTED}, ActionStatus.ESCALATED),
}
RESPONDER_OPERATIONS = {"START_WORK", "RESPOND", "COMMENT"}

OPEN_ALERT = {GovernanceAlertStatus.OPEN, GovernanceAlertStatus.ACKNOWLEDGED, GovernanceAlertStatus.UNDER_REVIEW}


class GovernanceService(AuditMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ geography helpers
    async def _target_geo(self, j: Jurisdiction, target_state: Optional[str], target_district: Optional[str],
                          facility_id: Optional[uuid.UUID] = None):
        """Resolve the (state, district) a new record belongs to, validated against the caller's jurisdiction."""
        if facility_id:
            facility = await self.session.get(Facility, facility_id)
            if not facility:
                raise ResourceNotFoundException("Facility", str(facility_id))
            j.ensure_covers(facility.state, facility.district)
            if j.is_facility_bound and facility.id != j.facility_id:
                raise PermissionDeniedException("You may only reference your own facility.")
            return facility.state, facility.district
        if j.scope == ScopeLevel.GLOBAL:
            if not target_state:
                raise BadRequestException("target_state is required for national-level records.")
            return target_state.strip(), target_district.strip() if target_district else None
        if j.scope == ScopeLevel.STATE:
            district = target_district.strip() if target_district else None
            return j.state, district
        if target_district and target_district.strip().lower() != (j.district or "").lower():
            raise PermissionDeniedException("You cannot create records for another district.")
        return j.state, j.district

    def _scoped(self, stmt, model, j: Jurisdiction):
        return j.filter(stmt, model.state, model.district)

    # ------------------------------------------------------------------ actions
    async def create_action(self, data: ActionCreate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx,
                            level: Optional[GovernanceLevel] = None, parent_id: Optional[uuid.UUID] = None,
                            status: ActionStatus = ActionStatus.PENDING) -> GovernanceAction:
        state, district = await self._target_geo(j, data.target_state, data.target_district, data.source_facility_id)
        if data.assigned_user_id:
            await self._ensure_assignable(data.assigned_user_id, j)
        action = GovernanceAction(
            reference=make_reference("ACT"),
            level=level or level_for(j),
            state=state,
            district=district,
            source_facility_id=data.source_facility_id,
            category=data.category.upper(),
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=ActionStatus.ASSIGNED if (data.assigned_user_id or data.assigned_role) and status == ActionStatus.PENDING else status,
            assigned_role=data.assigned_role,
            assigned_user_id=data.assigned_user_id,
            created_by=actor_id,
            due_at=data.due_at,
            parent_action_id=parent_id,
            source_reference=data.source_reference,
        )
        self.session.add(action)
        await self.session.flush()
        self.session.add(GovernanceActionUpdate(
            action_id=action.id, actor_id=actor_id, update_type=ActionUpdateType.STATUS_CHANGE,
            to_status=action.status.value, note="Action created.",
        ))
        await self.session.flush()
        await self._audit("GOVERNANCE_ACTION_CREATED", "governance_action", action.id, actor_id, ctx,
                          facility_id=data.source_facility_id,
                          new_state={"reference": action.reference, "level": action.level.value,
                                     "category": action.category, "priority": action.priority.value})
        return await self.get_action(action.id, j, actor_id)

    async def _ensure_assignable(self, user_id: uuid.UUID, j: Jurisdiction) -> None:
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            raise BadRequestException("Assigned user does not exist or is inactive.")
        if j.scope == ScopeLevel.GLOBAL:
            return
        if user.facility_id is None:
            raise BadRequestException("Assigned user has no facility and cannot be verified inside your jurisdiction.")
        facility = await self.session.get(Facility, user.facility_id)
        if not facility or not j.covers(facility.state, facility.district if j.scope != ScopeLevel.STATE else None):
            raise PermissionDeniedException("Assigned user is outside your jurisdiction.")

    def _action_visibility(self, stmt, j: Jurisdiction, actor_id: uuid.UUID):
        if j.is_facility_bound:
            return stmt.where(or_(GovernanceAction.source_facility_id == j.facility_id,
                                  GovernanceAction.assigned_user_id == actor_id))
        return self._scoped(stmt, GovernanceAction, j)

    async def list_actions(self, j: Jurisdiction, actor_id: uuid.UUID, status: Optional[ActionStatus],
                           category: Optional[str], priority: Optional[ActionPriority],
                           level: Optional[GovernanceLevel], assigned_to_me: bool, page: int, page_size: int):
        stmt = self._action_visibility(select(GovernanceAction), j, actor_id)
        if status:
            stmt = stmt.where(GovernanceAction.status == status)
        if category:
            stmt = stmt.where(GovernanceAction.category == category.upper())
        if priority:
            stmt = stmt.where(GovernanceAction.priority == priority)
        if level:
            stmt = stmt.where(GovernanceAction.level == level)
        if assigned_to_me:
            stmt = stmt.where(GovernanceAction.assigned_user_id == actor_id)
        return await paginate(self.session, stmt, GovernanceAction.created_at.desc(), page, page_size)

    async def get_action(self, action_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID) -> GovernanceAction:
        stmt = self._action_visibility(
            select(GovernanceAction).where(GovernanceAction.id == action_id)
            .options(selectinload(GovernanceAction.updates))
            .execution_options(populate_existing=True), j, actor_id,
        )
        action = (await self.session.execute(stmt)).scalar_one_or_none()
        if not action:
            raise ResourceNotFoundException("GovernanceAction", str(action_id))
        return action

    async def transition_action(self, action_id: uuid.UUID, data: ActionTransition, j: Jurisdiction,
                                actor_id: uuid.UUID, can_manage: bool, ctx: AuditCtx) -> GovernanceAction:
        action = await self.get_action(action_id, j, actor_id)
        op = data.operation
        is_assignee = action.assigned_user_id == actor_id
        if not can_manage and not (op in RESPONDER_OPERATIONS and (is_assignee or op == "COMMENT")):
            raise PermissionDeniedException(f"You are not permitted to perform '{op}' on this action.")

        old = action.status
        if op == "COMMENT":
            if action.status == ActionStatus.CLOSED:
                raise BadRequestException("Closed actions cannot receive comments.")
            update_type = ActionUpdateType.COMMENT
        else:
            allowed, target = ACTION_TRANSITIONS[op]
            if action.status not in allowed:
                raise BadRequestException(f"Cannot {op.lower().replace('_', ' ')} an action in status {action.status.value}.")
            update_type = ActionUpdateType.STATUS_CHANGE
            if op == "ASSIGN":
                if not (data.assigned_role or data.assigned_user_id):
                    raise BadRequestException("assigned_role or assigned_user_id is required to assign.")
                if data.assigned_user_id:
                    await self._ensure_assignable(data.assigned_user_id, j)
                action.assigned_role = data.assigned_role or action.assigned_role
                action.assigned_user_id = data.assigned_user_id or action.assigned_user_id
                update_type = ActionUpdateType.ASSIGNMENT
            elif op == "RESPOND":
                update_type = ActionUpdateType.RESPONSE
            elif op == "RESOLVE":
                owned_elsewhere = action.assigned_user_id not in (None, actor_id) or (
                    action.assigned_role is not None and action.assigned_user_id is None
                )
                if owned_elsewhere and not data.evidence_reference and action.status != ActionStatus.RESPONDED:
                    raise BadRequestException(
                        "This action belongs to another operational role; resolving requires their response "
                        "or an evidence_reference confirming completion."
                    )
                action.resolution_evidence = data.evidence_reference or data.note
                action.resolved_at = utcnow()
            elif op == "ESCALATE":
                nxt = NEXT_LEVEL.get(action.level)
                if nxt is None:
                    raise BadRequestException("National-level actions cannot be escalated further.")
                action.escalated_to_level = nxt
                child = GovernanceAction(
                    reference=make_reference("ACT"), level=nxt, state=action.state,
                    district=action.district if nxt == GovernanceLevel.STATE else None,
                    source_facility_id=action.source_facility_id, category=action.category,
                    title=f"[Escalated] {action.title}", description=f"{action.description}\n\nEscalation note: {data.note}",
                    priority=action.priority, status=ActionStatus.PENDING, created_by=actor_id,
                    parent_action_id=action.id, source_reference=action.reference,
                )
                self.session.add(child)
                await self.session.flush()
                self.session.add(GovernanceActionUpdate(
                    action_id=child.id, actor_id=actor_id, update_type=ActionUpdateType.ESCALATION,
                    to_status=ActionStatus.PENDING.value, note=f"Escalated from {action.reference}: {data.note}",
                ))
                update_type = ActionUpdateType.ESCALATION
            action.status = target

        self.session.add(GovernanceActionUpdate(
            action_id=action.id, actor_id=actor_id, update_type=update_type,
            from_status=old.value, to_status=action.status.value, note=data.note,
            evidence_reference=data.evidence_reference,
        ))
        await self.session.flush()
        await self._audit(f"GOVERNANCE_ACTION_{op}", "governance_action", action.id, actor_id, ctx,
                          facility_id=action.source_facility_id,
                          old_state={"status": old.value}, new_state={"status": action.status.value, "note": data.note})
        return await self.get_action(action.id, j, actor_id)

    # ------------------------------------------------------------------ alerts
    async def create_alert(self, data: GovernanceAlertCreate, j: Jurisdiction, actor_id: Optional[uuid.UUID],
                           ctx: AuditCtx, origin: AlertOrigin = AlertOrigin.HUMAN,
                           related_insight_id: Optional[uuid.UUID] = None,
                           level: Optional[GovernanceLevel] = None) -> GovernanceAlert:
        state, district = await self._target_geo(j, data.target_state, data.target_district, data.facility_id)
        alert = GovernanceAlert(
            reference=make_reference("HAL"),
            level=level or (GovernanceLevel.DISTRICT if district else level_for(j)),
            state=state, district=district, facility_id=data.facility_id,
            category=data.category.upper(), title=data.title, description=data.description,
            severity=data.severity, origin=origin, status=GovernanceAlertStatus.OPEN,
            source_reference=data.source_reference, data_period=data.data_period,
            related_insight_id=related_insight_id, raised_by=actor_id,
        )
        self.session.add(alert)
        await self.session.flush()
        await self._audit("GOVERNANCE_ALERT_RAISED", "governance_alert", alert.id, actor_id, ctx,
                          facility_id=data.facility_id,
                          new_state={"reference": alert.reference, "category": alert.category, "origin": origin.value})
        return alert

    async def list_alerts(self, j: Jurisdiction, status: Optional[GovernanceAlertStatus], category: Optional[str],
                          severity: Optional[ActionPriority], district: Optional[str], open_only: bool,
                          page: int, page_size: int):
        stmt = self._scoped(select(GovernanceAlert), GovernanceAlert, j)
        if j.is_facility_bound:
            stmt = stmt.where(GovernanceAlert.facility_id == j.facility_id)
        if status:
            stmt = stmt.where(GovernanceAlert.status == status)
        elif open_only:
            stmt = stmt.where(GovernanceAlert.status.in_(OPEN_ALERT))
        if category:
            stmt = stmt.where(GovernanceAlert.category == category.upper())
        if severity:
            stmt = stmt.where(GovernanceAlert.severity == severity)
        if district:
            stmt = stmt.where(GovernanceAlert.district == district)
        return await paginate(self.session, stmt, GovernanceAlert.created_at.desc(), page, page_size)

    async def get_alert(self, alert_id: uuid.UUID, j: Jurisdiction) -> GovernanceAlert:
        stmt = self._scoped(select(GovernanceAlert).where(GovernanceAlert.id == alert_id), GovernanceAlert, j)
        alert = (await self.session.execute(stmt)).scalar_one_or_none()
        if not alert:
            raise ResourceNotFoundException("GovernanceAlert", str(alert_id))
        return alert

    async def transition_alert(self, alert_id: uuid.UUID, data: GovernanceAlertTransition, j: Jurisdiction,
                               actor_id: uuid.UUID, ctx: AuditCtx) -> GovernanceAlert:
        alert = await self.get_alert(alert_id, j)
        old = alert.status
        op = data.operation
        if alert.status in (GovernanceAlertStatus.RESOLVED, GovernanceAlertStatus.DISMISSED, GovernanceAlertStatus.ESCALATED):
            raise BadRequestException(f"Alert is {alert.status.value}; no further actions are possible.")
        if op == "ACKNOWLEDGE":
            if alert.status != GovernanceAlertStatus.OPEN:
                raise ConflictException("Alert has already been acknowledged.")
            alert.status = GovernanceAlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = actor_id
            alert.acknowledged_at = utcnow()
        elif op == "START_REVIEW":
            alert.status = GovernanceAlertStatus.UNDER_REVIEW
        elif op == "SET_SEVERITY":
            if not data.severity:
                raise BadRequestException("severity is required for SET_SEVERITY.")
            alert.severity = data.severity
        elif op == "ESCALATE":
            nxt = NEXT_LEVEL.get(alert.level)
            if nxt is None:
                raise BadRequestException("National alerts cannot be escalated further.")
            action = GovernanceAction(
                reference=make_reference("ACT"), level=nxt, state=alert.state,
                district=alert.district if nxt == GovernanceLevel.STATE else None,
                source_facility_id=alert.facility_id, category=alert.category,
                title=f"[Alert escalation] {alert.title}", description=f"{alert.description}\n\nEscalation note: {data.note}",
                priority=alert.severity or ActionPriority.HIGH, status=ActionStatus.PENDING,
                created_by=actor_id, source_reference=alert.reference,
            )
            self.session.add(action)
            await self.session.flush()
            self.session.add(GovernanceActionUpdate(
                action_id=action.id, actor_id=actor_id, update_type=ActionUpdateType.ESCALATION,
                to_status=ActionStatus.PENDING.value, note=f"Escalated from alert {alert.reference}: {data.note}",
            ))
            alert.escalated_action_id = action.id
            alert.status = GovernanceAlertStatus.ESCALATED
        elif op in ("RESOLVE", "DISMISS"):
            alert.status = GovernanceAlertStatus.RESOLVED if op == "RESOLVE" else GovernanceAlertStatus.DISMISSED
        alert.resolution_notes = f"{alert.resolution_notes}\n[{op}] {data.note}" if alert.resolution_notes else f"[{op}] {data.note}"
        await self.session.flush()
        await self._audit(f"GOVERNANCE_ALERT_{op}", "governance_alert", alert.id, actor_id, ctx,
                          facility_id=alert.facility_id, old_state={"status": old.value},
                          new_state={"status": alert.status.value, "note": data.note})
        return alert

    # ------------------------------------------------------------------ approvals
    async def create_approval(self, data: ApprovalCreate, j: Jurisdiction, actor_id: uuid.UUID,
                              ctx: AuditCtx) -> ApprovalRequest:
        own_level = level_for(j)
        target = NEXT_LEVEL.get(own_level)
        if target is None:
            raise BadRequestException("National users have no higher approval authority in this workflow.")
        if j.scope == ScopeLevel.GLOBAL:
            raise BadRequestException("National users cannot raise state approval requests.")
        req = ApprovalRequest(
            reference=make_reference("APR"), level=target, state=j.state,
            district=j.district if own_level == GovernanceLevel.DISTRICT else None,
            request_type=data.request_type.upper(), title=data.title, reason=data.reason,
            evidence_reference=data.evidence_reference, requested_by=actor_id, status=ApprovalStatus.PENDING,
        )
        self.session.add(req)
        await self.session.flush()
        await self._audit("APPROVAL_REQUEST_SUBMITTED", "approval_request", req.id, actor_id, ctx,
                          new_state={"reference": req.reference, "type": req.request_type, "to_level": target.value})
        return req

    async def list_approvals(self, j: Jurisdiction, actor_id: uuid.UUID, status: Optional[ApprovalStatus],
                             mine: bool, page: int, page_size: int):
        stmt = select(ApprovalRequest)
        if mine:
            stmt = stmt.where(ApprovalRequest.requested_by == actor_id)
        else:
            stmt = j.filter(stmt, ApprovalRequest.state, None if j.scope == ScopeLevel.STATE else ApprovalRequest.district)
        if status:
            stmt = stmt.where(ApprovalRequest.status == status)
        return await paginate(self.session, stmt, ApprovalRequest.created_at.desc(), page, page_size)

    async def get_approval(self, request_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID) -> ApprovalRequest:
        req = await self.session.get(ApprovalRequest, request_id)
        if not req or (req.requested_by != actor_id and not j.covers(req.state, req.district)):
            raise ResourceNotFoundException("ApprovalRequest", str(request_id))
        return req

    async def decide_approval(self, request_id: uuid.UUID, data: ApprovalDecision, j: Jurisdiction,
                              actor_id: uuid.UUID, ctx: AuditCtx) -> ApprovalRequest:
        req = await self.get_approval(request_id, j, actor_id)
        if level_for(j) != req.level and j.scope != ScopeLevel.GLOBAL:
            raise PermissionDeniedException(f"This request is routed to {req.level.value}-level authority.")
        j.ensure_covers(req.state, req.district if j.scope == ScopeLevel.DISTRICT else None)
        if req.status != ApprovalStatus.PENDING:
            raise ConflictException(f"Request is {req.status.value}; only PENDING requests can be decided.")
        if req.requested_by == actor_id:
            raise BadRequestException("Segregation of duties: you cannot decide your own request.")
        old = req.status
        req.status = {"APPROVE": ApprovalStatus.APPROVED, "REJECT": ApprovalStatus.REJECTED,
                      "REQUEST_CLARIFICATION": ApprovalStatus.CLARIFICATION_REQUESTED}[data.decision]
        req.decided_by = actor_id
        req.decided_at = utcnow()
        req.decision_reason = data.reason
        await self.session.flush()
        await self._audit(f"APPROVAL_{data.decision}", "approval_request", req.id, actor_id, ctx,
                          old_state={"status": old.value}, new_state={"status": req.status.value, "reason": data.reason})
        return req

    async def clarify_approval(self, request_id: uuid.UUID, data: ApprovalClarification, actor_id: uuid.UUID,
                               ctx: AuditCtx) -> ApprovalRequest:
        req = await self.session.get(ApprovalRequest, request_id)
        if not req or req.requested_by != actor_id:
            raise ResourceNotFoundException("ApprovalRequest", str(request_id))
        if req.status != ApprovalStatus.CLARIFICATION_REQUESTED:
            raise BadRequestException("Clarification can only be supplied when it has been requested.")
        req.reason = f"{req.reason}\n\n[Clarification] {data.note}"
        if data.evidence_reference:
            req.evidence_reference = data.evidence_reference
        req.status = ApprovalStatus.PENDING
        await self.session.flush()
        await self._audit("APPROVAL_CLARIFICATION_SUPPLIED", "approval_request", req.id, actor_id, ctx,
                          new_state={"status": req.status.value})
        return req

    # ------------------------------------------------------------------ insights
    async def list_insights(self, j: Jurisdiction, level: Optional[GovernanceLevel],
                            review_status: Optional[InsightReviewStatus], insight_type: Optional[str],
                            page: int, page_size: int):
        stmt = j.filter(select(AIInsight), AIInsight.state, None if j.scope == ScopeLevel.STATE else AIInsight.district)
        if level:
            stmt = stmt.where(AIInsight.level == level)
        if review_status:
            stmt = stmt.where(AIInsight.review_status == review_status)
        if insight_type:
            stmt = stmt.where(AIInsight.insight_type == insight_type)
        return await paginate(self.session, stmt, AIInsight.created_at.desc(), page, page_size)

    async def review_insight(self, insight_id: uuid.UUID, data: InsightReview, j: Jurisdiction,
                             actor_id: uuid.UUID, ctx: AuditCtx) -> AIInsight:
        insight = await self.session.get(AIInsight, insight_id)
        if not insight or not j.covers(insight.state, insight.district if j.scope == ScopeLevel.DISTRICT else None):
            raise ResourceNotFoundException("AIInsight", str(insight_id))
        if insight.review_status != InsightReviewStatus.PENDING_REVIEW:
            raise ConflictException(f"Insight already reviewed ({insight.review_status.value}).")
        if data.raise_alert and data.decision != "ACCEPTED":
            raise BadRequestException("Only an ACCEPTED insight can raise an alert.")
        insight.review_status = InsightReviewStatus(data.decision)
        insight.reviewed_by = actor_id
        insight.reviewed_at = utcnow()
        insight.review_notes = data.notes
        await self.session.flush()
        if data.raise_alert:
            await self.create_alert(
                GovernanceAlertCreate(
                    category=insight.insight_type, title=insight.observation[:250],
                    description=f"{insight.explanation}\n\nReviewer notes: {data.notes}\nLimitations: {insight.limitations}",
                    severity=data.alert_severity, target_state=insight.state, target_district=insight.district,
                    source_reference=f"insight:{insight.id}", data_period=insight.reporting_period,
                ),
                _GlobalJurisdiction, actor_id, ctx, origin=AlertOrigin.AI_ANALYSIS, related_insight_id=insight.id,
                level=GovernanceLevel.DISTRICT if insight.district else insight.level,
            )
        await self._audit("AI_INSIGHT_REVIEWED", "ai_insight", insight.id, actor_id, ctx,
                          new_state={"decision": data.decision, "raise_alert": data.raise_alert})
        return insight


# Internal jurisdiction used only after the caller's own jurisdiction has already been verified.
_GlobalJurisdiction = Jurisdiction(ScopeLevel.GLOBAL, None, None, None)
