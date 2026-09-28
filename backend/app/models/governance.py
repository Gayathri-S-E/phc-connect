"""District / State / National governance domain (Roles 06, 09, 11, 12).

One set of tables serves every administrative level; `level` plus the
`state`/`district` jurisdiction columns scope each record. This follows the
spec's "shared systems, no duplication" rule: DHOAction, state alert actions and
NationalCoordinationRequest are all GovernanceActions; DistrictReport,
StateReport, PublicHealthReport and NationalReport are all GovernanceReports.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GovernanceLevel(str, enum.Enum):
    DISTRICT = "DISTRICT"
    STATE = "STATE"
    NATIONAL = "NATIONAL"


class ActionPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESPONDED = "RESPONDED"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ActionUpdateType(str, enum.Enum):
    COMMENT = "COMMENT"
    STATUS_CHANGE = "STATUS_CHANGE"
    ASSIGNMENT = "ASSIGNMENT"
    RESPONSE = "RESPONSE"
    ESCALATION = "ESCALATION"


class GovernanceAlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertOrigin(str, enum.Enum):
    """Where the alert came from. RULE_ENGINE / AI_ANALYSIS alerts are advisory until a human reviews them."""
    HUMAN = "HUMAN"
    RULE_ENGINE = "RULE_ENGINE"
    AI_ANALYSIS = "AI_ANALYSIS"


class ReportReviewStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class InsightReviewStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"


class GovernanceAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Pending district action (DHOAction), state follow-up, or national coordination request."""
    __tablename__ = "governance_actions"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    level: Mapped[GovernanceLevel] = mapped_column(Enum(GovernanceLevel, name="governance_level_enum"), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    source_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), index=True, nullable=True
    )
    category: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[ActionPriority] = mapped_column(
        Enum(ActionPriority, name="action_priority_enum"), default=ActionPriority.MEDIUM, nullable=False
    )
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status_enum"), default=ActionStatus.PENDING, index=True, nullable=False
    )
    assigned_role: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_to_level: Mapped[Optional[GovernanceLevel]] = mapped_column(
        Enum(GovernanceLevel, name="governance_level_enum"), nullable=True
    )
    parent_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("governance_actions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    updates = relationship(
        "GovernanceActionUpdate", back_populates="action", cascade="all, delete-orphan",
        order_by="GovernanceActionUpdate.created_at",
    )


class GovernanceActionUpdate(Base, UUIDPrimaryKeyMixin):
    """Immutable history entry for an action: comment, status change, response, escalation."""
    __tablename__ = "governance_action_updates"

    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("governance_actions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    update_type: Mapped[ActionUpdateType] = mapped_column(
        Enum(ActionUpdateType, name="action_update_type_enum"), nullable=False
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    action = relationship("GovernanceAction", back_populates="updates")


class GovernanceAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """District health alert, state health alert/escalation, public-health alert, or national alert."""
    __tablename__ = "governance_alerts"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    level: Mapped[GovernanceLevel] = mapped_column(Enum(GovernanceLevel, name="governance_level_enum"), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), index=True, nullable=True
    )
    category: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Severity is only ever set by a human or a configured rule — never by free-form AI.
    severity: Mapped[Optional[ActionPriority]] = mapped_column(Enum(ActionPriority, name="action_priority_enum"), nullable=True)
    origin: Mapped[AlertOrigin] = mapped_column(Enum(AlertOrigin, name="alert_origin_enum"), default=AlertOrigin.HUMAN, nullable=False)
    status: Mapped[GovernanceAlertStatus] = mapped_column(
        Enum(GovernanceAlertStatus, name="governance_alert_status_enum"),
        default=GovernanceAlertStatus.OPEN, index=True, nullable=False,
    )
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_period: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    related_insight_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_insights.id", ondelete="SET NULL"), nullable=True
    )
    raised_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("governance_actions.id", ondelete="SET NULL"), nullable=True
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GovernanceReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Generated report built from real aggregates at the time of generation (content is a snapshot)."""
    __tablename__ = "governance_reports"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    level: Mapped[GovernanceLevel] = mapped_column(Enum(GovernanceLevel, name="governance_level_enum"), index=True, nullable=False)
    report_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    review_status: Mapped[ReportReviewStatus] = mapped_column(
        Enum(ReportReviewStatus, name="report_review_status_enum"),
        default=ReportReviewStatus.DRAFT, index=True, nullable=False,
    )
    submitted_to_level: Mapped[Optional[GovernanceLevel]] = mapped_column(
        Enum(GovernanceLevel, name="governance_level_enum"), nullable=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ApprovalRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Administrative request routed to a higher authority (e.g. district → State Health Administrator)."""
    __tablename__ = "approval_requests"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    level: Mapped[GovernanceLevel] = mapped_column(Enum(GovernanceLevel, name="governance_level_enum"), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    request_type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status_enum"), default=ApprovalStatus.PENDING, index=True, nullable=False
    )
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HealthScheme(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Project-configured health scheme. Names/targets are entered by authorized users, never invented."""
    __tablename__ = "health_schemes"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    targets = relationship("SchemeTarget", back_populates="scheme", cascade="all, delete-orphan")


class SchemeTarget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scheme_targets"
    __table_args__ = (
        UniqueConstraint("scheme_id", "district", "period_start", "period_end", name="uq_scheme_target_period"),
    )

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_schemes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    target_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reported_value: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    reported_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scheme = relationship("HealthScheme", back_populates="targets")


class AIInsight(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI/rule-generated observation awaiting human review (PublicHealthInsight, NationalAIInsight)."""
    __tablename__ = "ai_insights"

    level: Mapped[GovernanceLevel] = mapped_column(Enum(GovernanceLevel, name="governance_level_enum"), index=True, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    indicator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public_health_indicators.id", ondelete="SET NULL"), nullable=True
    )
    reporting_period: Mapped[str] = mapped_column(String(60), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_follow_up: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_references: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    review_status: Mapped[InsightReviewStatus] = mapped_column(
        Enum(InsightReviewStatus, name="insight_review_status_enum"),
        default=InsightReviewStatus.PENDING_REVIEW, index=True, nullable=False,
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AIInteraction(Base, UUIDPrimaryKeyMixin):
    """Audit trail of every role-specific AI assistant call (DHO, DSCO, Emergency, State, Analyst, National)."""
    __tablename__ = "ai_interactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    assistant: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    scope_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    context_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(60), nullable=False)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    refused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True, nullable=False)
