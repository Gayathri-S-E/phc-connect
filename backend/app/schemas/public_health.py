import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.public_health import (
    AggregationLevel,
    AnalysisJobStatus,
    DataQualityIssueType,
    DataQualityStatus,
    ValidationStatus,
)


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IndicatorCreate(_In):
    code: str = Field(min_length=2, max_length=60, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=3, max_length=255)
    category: str = Field(min_length=2, max_length=60)
    definition: str = Field(min_length=5, max_length=3000)
    unit: str = Field(min_length=1, max_length=50)
    numerator_definition: Optional[str] = Field(None, max_length=2000)
    denominator_definition: Optional[str] = Field(None, max_length=2000)
    aggregation_level: AggregationLevel = AggregationLevel.DISTRICT
    higher_is_worse: bool = True


class IndicatorResponse(_Out):
    id: uuid.UUID
    code: str
    name: str
    category: str
    definition: str
    unit: str
    numerator_definition: Optional[str] = None
    denominator_definition: Optional[str] = None
    aggregation_level: AggregationLevel
    higher_is_worse: bool
    version: int
    is_active: bool


class AggregateSubmit(_In):
    indicator_id: uuid.UUID
    district: Optional[str] = Field(None, max_length=100)
    facility_id: Optional[uuid.UUID] = None
    period_start: date
    period_end: date
    value: float = Field(ge=0)
    numerator: Optional[float] = Field(None, ge=0)
    denominator: Optional[float] = Field(None, gt=0)
    source_reference: str = Field(min_length=2, max_length=255)

    @model_validator(mode="after")
    def _rules(self):
        if self.period_start > self.period_end:
            raise ValueError("period_start must be on or before period_end")
        if (self.numerator is None) != (self.denominator is None):
            raise ValueError("numerator and denominator must be supplied together")
        return self


class AggregateValidate(_In):
    validation_status: ValidationStatus
    note: str = Field(min_length=2, max_length=2000)


class AggregateResponse(_Out):
    id: uuid.UUID
    indicator_id: uuid.UUID
    state: str
    district: str
    facility_id: Optional[uuid.UUID] = None
    period_start: date
    period_end: date
    value: float
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    source_reference: str
    source_role: str
    validation_status: ValidationStatus
    submitted_by: uuid.UUID
    created_at: datetime


class TrendPoint(BaseModel):
    district: str
    current_value: Optional[float]
    previous_value: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    submissions_current: int
    validation: Dict[str, int]


class TrendResponse(BaseModel):
    indicator: IndicatorResponse
    scope: str
    current_period: Dict[str, str]
    previous_period: Dict[str, str]
    state_current: Optional[float]
    state_previous: Optional[float]
    state_change_pct: Optional[float]
    reporting_coverage: Dict[str, Any]
    districts: List[TrendPoint]
    data_classification: str = "ACTUAL_REPORTED"
    sources: List[str]


class AnalysisRun(_In):
    period_end: Optional[date] = None
    window_days: int = Field(default=30, ge=7, le=180)


class AnalysisJobResponse(_Out):
    id: uuid.UUID
    job_type: str
    scope_reference: str
    reporting_period: str
    method: str
    method_version: str
    status: AnalysisJobStatus
    insights_created: int
    issues_created: int
    error_reference: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class DataQualityResponse(_Out):
    id: uuid.UUID
    issue_type: DataQualityIssueType
    state: str
    district: Optional[str] = None
    indicator_id: Optional[uuid.UUID] = None
    aggregate_id: Optional[uuid.UUID] = None
    reporting_period: str
    description: str
    status: DataQualityStatus
    verification_note: Optional[str] = None
    requested_by: Optional[uuid.UUID] = None
    resolution_reference: Optional[str] = None
    created_at: datetime


class DataQualityAction(_In):
    note: str = Field(min_length=3, max_length=2000)
    resolution_reference: Optional[str] = Field(None, max_length=500)
