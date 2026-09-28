"""State public-health analytics domain (Role 11).

Holds aggregated indicator values only — never patient-level identifiers.
Insights and alerts produced from these aggregates live in the shared
governance tables (AIInsight, GovernanceAlert).
"""
import enum
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AggregationLevel(str, enum.Enum):
    PHC = "PHC"
    DISTRICT = "DISTRICT"
    STATE = "STATE"


class ValidationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class DataQualityIssueType(str, enum.Enum):
    MISSING_REPORT = "MISSING_REPORT"
    DELAYED_REPORT = "DELAYED_REPORT"
    DUPLICATE_SUBMISSION = "DUPLICATE_SUBMISSION"
    OUTLIER = "OUTLIER"
    INCONSISTENT_VALUE = "INCONSISTENT_VALUE"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"


class DataQualityStatus(str, enum.Enum):
    OPEN = "OPEN"
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AnalysisJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PublicHealthIndicator(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "public_health_indicators"

    code: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    numerator_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    denominator_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aggregation_level: Mapped[AggregationLevel] = mapped_column(
        Enum(AggregationLevel, name="aggregation_level_enum"), default=AggregationLevel.DISTRICT, nullable=False
    )
    # Higher is worse (e.g. case counts) vs higher is better (e.g. coverage) — drives trend wording.
    higher_is_worse: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aggregates = relationship("HealthIndicatorAggregate", back_populates="indicator")


class HealthIndicatorAggregate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "health_indicator_aggregates"
    __table_args__ = (
        UniqueConstraint(
            "indicator_id", "state", "district", "facility_id", "period_start", "period_end",
            name="uq_indicator_aggregate_period",
        ),
    )

    indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public_health_indicators.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), index=True, nullable=True
    )
    period_start: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    numerator: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    denominator: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    source_role: Mapped[str] = mapped_column(String(60), nullable=False)
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus, name="validation_status_enum"), default=ValidationStatus.PENDING, index=True, nullable=False
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    indicator = relationship("PublicHealthIndicator", back_populates="aggregates")


class DataQualityIssue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "data_quality_issues"

    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    issue_type: Mapped[DataQualityIssueType] = mapped_column(
        Enum(DataQualityIssueType, name="data_quality_issue_type_enum"), index=True, nullable=False
    )
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    indicator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("public_health_indicators.id", ondelete="SET NULL"), nullable=True
    )
    aggregate_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("health_indicator_aggregates.id", ondelete="SET NULL"), nullable=True
    )
    reporting_period: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DataQualityStatus] = mapped_column(
        Enum(DataQualityStatus, name="data_quality_status_enum"), default=DataQualityStatus.OPEN, index=True, nullable=False
    )
    verification_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class AIAnalysisJob(Base, UUIDPrimaryKeyMixin):
    """Idempotent record of each automatic analysis run (AIAnalysisJob + AIAnalysisAudit)."""
    __tablename__ = "ai_analysis_jobs"

    job_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    scope_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reporting_period: Mapped[str] = mapped_column(String(60), nullable=False)
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    method_version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[AnalysisJobStatus] = mapped_column(
        Enum(AnalysisJobStatus, name="analysis_job_status_enum"), default=AnalysisJobStatus.QUEUED, nullable=False
    )
    insights_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
