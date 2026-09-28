import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.governance import (
    ActionPriority,
    ActionStatus,
    ActionUpdateType,
    AlertOrigin,
    ApprovalStatus,
    GovernanceAlertStatus,
    GovernanceLevel,
    InsightReviewStatus,
    ReportReviewStatus,
)


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- actions
class ActionCreate(_In):
    category: str = Field(min_length=2, max_length=60)
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5, max_length=5000)
    priority: ActionPriority = ActionPriority.MEDIUM
    assigned_role: Optional[str] = Field(None, max_length=60)
    assigned_user_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None
    source_facility_id: Optional[uuid.UUID] = None
    target_state: Optional[str] = Field(None, max_length=100)
    target_district: Optional[str] = Field(None, max_length=100)
    source_reference: Optional[str] = Field(None, max_length=255)


class ActionTransition(_In):
    operation: Literal["ASSIGN", "START_REVIEW", "START_WORK", "RESPOND", "REQUEST_CLARIFICATION",
                       "RESOLVE", "CLOSE", "ESCALATE", "COMMENT"]
    note: str = Field(min_length=2, max_length=5000)
    assigned_role: Optional[str] = Field(None, max_length=60)
    assigned_user_id: Optional[uuid.UUID] = None
    evidence_reference: Optional[str] = Field(None, max_length=500)


class ActionUpdateResponse(_Out):
    id: uuid.UUID
    actor_id: uuid.UUID
    update_type: ActionUpdateType
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    note: str
    evidence_reference: Optional[str] = None
    created_at: datetime


class ActionResponse(_Out):
    id: uuid.UUID
    reference: str
    level: GovernanceLevel
    state: str
    district: Optional[str] = None
    source_facility_id: Optional[uuid.UUID] = None
    category: str
    title: str
    description: str
    priority: ActionPriority
    status: ActionStatus
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[uuid.UUID] = None
    created_by: uuid.UUID
    due_at: Optional[datetime] = None
    escalated_to_level: Optional[GovernanceLevel] = None
    parent_action_id: Optional[uuid.UUID] = None
    source_reference: Optional[str] = None
    resolution_evidence: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ActionDetailResponse(ActionResponse):
    updates: List[ActionUpdateResponse] = []


# ---------------------------------------------------------------- alerts
class GovernanceAlertCreate(_In):
    category: str = Field(min_length=2, max_length=60)
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5, max_length=5000)
    severity: Optional[ActionPriority] = None
    facility_id: Optional[uuid.UUID] = None
    target_state: Optional[str] = Field(None, max_length=100)
    target_district: Optional[str] = Field(None, max_length=100)
    source_reference: Optional[str] = Field(None, max_length=255)
    data_period: Optional[str] = Field(None, max_length=60)


class GovernanceAlertTransition(_In):
    operation: Literal["ACKNOWLEDGE", "START_REVIEW", "ESCALATE", "RESOLVE", "DISMISS", "SET_SEVERITY"]
    note: str = Field(min_length=2, max_length=5000)
    severity: Optional[ActionPriority] = None


class GovernanceAlertResponse(_Out):
    id: uuid.UUID
    reference: str
    level: GovernanceLevel
    state: str
    district: Optional[str] = None
    facility_id: Optional[uuid.UUID] = None
    category: str
    title: str
    description: str
    severity: Optional[ActionPriority] = None
    origin: AlertOrigin
    status: GovernanceAlertStatus
    source_reference: Optional[str] = None
    data_period: Optional[str] = None
    related_insight_id: Optional[uuid.UUID] = None
    raised_by: Optional[uuid.UUID] = None
    acknowledged_by: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    escalated_action_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- reports
class ReportGenerate(_In):
    report_type: str = Field(min_length=3, max_length=60)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    target_state: Optional[str] = Field(None, max_length=100)
    target_district: Optional[str] = Field(None, max_length=100)
    facility_id: Optional[uuid.UUID] = None


class ReportReview(_In):
    decision: Literal["ACCEPT", "REJECT", "REQUEST_CLARIFICATION"]
    notes: str = Field(min_length=3, max_length=5000)


class ReportResponse(_Out):
    id: uuid.UUID
    reference: str
    level: GovernanceLevel
    report_type: str
    title: str
    state: str
    district: Optional[str] = None
    facility_id: Optional[uuid.UUID] = None
    period_start: date
    period_end: date
    generated_by: uuid.UUID
    review_status: ReportReviewStatus
    submitted_to_level: Optional[GovernanceLevel] = None
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    version: int
    created_at: datetime


class ReportDetailResponse(ReportResponse):
    content: Dict[str, Any]


class ReportTypeInfo(BaseModel):
    code: str
    name: str
    level: GovernanceLevel


# ---------------------------------------------------------------- approvals
class ApprovalCreate(_In):
    request_type: str = Field(min_length=3, max_length=60)
    title: str = Field(min_length=3, max_length=255)
    reason: str = Field(min_length=5, max_length=5000)
    evidence_reference: Optional[str] = Field(None, max_length=500)


class ApprovalDecision(_In):
    decision: Literal["APPROVE", "REJECT", "REQUEST_CLARIFICATION"]
    reason: str = Field(min_length=3, max_length=5000)


class ApprovalClarification(_In):
    note: str = Field(min_length=3, max_length=5000)
    evidence_reference: Optional[str] = Field(None, max_length=500)


class ApprovalResponse(_Out):
    id: uuid.UUID
    reference: str
    level: GovernanceLevel
    state: str
    district: Optional[str] = None
    request_type: str
    title: str
    reason: str
    evidence_reference: Optional[str] = None
    requested_by: uuid.UUID
    status: ApprovalStatus
    decided_by: Optional[uuid.UUID] = None
    decided_at: Optional[datetime] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- schemes
class SchemeCreate(_In):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_\-]+$")
    name: str = Field(min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    unit: str = Field(min_length=1, max_length=50)
    target_state: Optional[str] = Field(None, max_length=100)


class SchemeTargetSet(_In):
    district: str = Field(min_length=2, max_length=100)
    period_start: date
    period_end: date
    target_value: float = Field(gt=0)

    @model_validator(mode="after")
    def _period(self):
        if self.period_start > self.period_end:
            raise ValueError("period_start must be on or before period_end")
        return self


class SchemeProgressReport(_In):
    reported_value: float = Field(ge=0)
    remarks: Optional[str] = Field(None, max_length=2000)


class SchemeRemark(_In):
    remarks: str = Field(min_length=2, max_length=2000)


class SchemeTargetResponse(_Out):
    id: uuid.UUID
    scheme_id: uuid.UUID
    district: str
    period_start: date
    period_end: date
    target_value: float
    reported_value: Optional[float] = None
    reported_by: Optional[uuid.UUID] = None
    reported_at: Optional[datetime] = None
    remarks: Optional[str] = None
    progress_pct: Optional[float] = None
    reporting_status: str = "PENDING"


class SchemeResponse(_Out):
    id: uuid.UUID
    code: str
    name: str
    state: str
    description: Optional[str] = None
    unit: str
    is_active: bool
    created_at: datetime


class SchemeDetailResponse(SchemeResponse):
    targets: List[SchemeTargetResponse] = []


# ---------------------------------------------------------------- insights
class InsightReview(_In):
    decision: Literal["ACCEPTED", "REJECTED", "NEEDS_MORE_DATA"]
    notes: str = Field(min_length=3, max_length=5000)
    raise_alert: bool = False
    alert_severity: Optional[ActionPriority] = None


class InsightResponse(_Out):
    id: uuid.UUID
    level: GovernanceLevel
    insight_type: str
    state: str
    district: Optional[str] = None
    indicator_id: Optional[uuid.UUID] = None
    reporting_period: str
    observation: str
    explanation: str
    limitations: str
    suggested_follow_up: Optional[str] = None
    source_references: Optional[Dict[str, Any]] = None
    method: str
    confidence: Optional[float] = None
    review_status: InsightReviewStatus
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------- assistants
class AssistantQuery(_In):
    question: str = Field(min_length=2, max_length=1000)
    context_reference: Optional[str] = Field(None, max_length=255)
    language: Literal["en", "ta"] = "en"


class AssistantResponse(BaseModel):
    assistant: str
    intent: str
    answer: str
    answer_ta: Optional[str] = None
    refused: bool = False
    data_period: Optional[str] = None
    scope: str
    sources: List[str] = []
    suggestions: List[str] = []
    method: str
    disclaimer: str
    generated_at: datetime
