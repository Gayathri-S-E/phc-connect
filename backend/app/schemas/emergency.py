import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.emergency import (
    EmergencyEscalationStatus,
    EmergencyPriority,
    EmergencyStatus,
    EmergencyTaskStatus,
    EmergencyType,
)
from app.models.supply_chain import PurchaseRequestUrgency


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EmergencyCreate(_In):
    emergency_type: EmergencyType
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5, max_length=5000)
    affected_area: str = Field(min_length=2, max_length=255)
    source: str = Field(min_length=2, max_length=100)
    affected_facility_ids: List[uuid.UUID] = Field(default_factory=list, max_length=50)


class EmergencyStatusUpdate(_In):
    status: Literal["ACKNOWLEDGED", "RESPONSE_STARTED", "IN_PROGRESS", "CLOSED"]
    note: str = Field(min_length=2, max_length=2000)


class EmergencyPrioritySet(_In):
    priority: EmergencyPriority
    reason: str = Field(min_length=3, max_length=2000)


class EmergencyResolve(_In):
    resolution_summary: str = Field(min_length=10, max_length=5000)
    confirmation_reference: str = Field(min_length=3, max_length=255)


class AffectedFacilityUpsert(_In):
    facility_id: uuid.UUID
    service_disruption: Literal["NONE", "PARTIAL", "SEVERE", "CLOSED"] = "NONE"
    notes: Optional[str] = Field(None, max_length=2000)


class EmergencyTaskCreate(_In):
    assigned_role: str = Field(min_length=2, max_length=60)
    assigned_user_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    description: str = Field(min_length=3, max_length=2000)


class EmergencyTaskUpdate(_In):
    status: Literal["ACCEPTED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
    note: str = Field(min_length=2, max_length=2000)


class EmergencyEscalationCreate(_In):
    to_role: Literal["DISTRICT_HEALTH_OFFICER", "DISTRICT_SUPPLY_OFFICER", "STATE_HEALTH_ADMIN", "STATE_SUPPLY_MANAGER"]
    reason: str = Field(min_length=5, max_length=2000)


class EmergencyResourceRequestCreate(_In):
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=2000)
    priority: PurchaseRequestUrgency = PurchaseRequestUrgency.EMERGENCY


class AffectedFacilityResponse(_Out):
    id: uuid.UUID
    facility_id: uuid.UUID
    service_disruption: str
    notes: Optional[str] = None


class EmergencyTaskResponse(_Out):
    id: uuid.UUID
    incident_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    assigned_role: str
    assigned_user_id: Optional[uuid.UUID] = None
    description: str
    status: EmergencyTaskStatus
    created_by: uuid.UUID
    completion_note: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class EmergencyEscalationResponse(_Out):
    id: uuid.UUID
    from_role: str
    to_role: str
    reason: str
    status: EmergencyEscalationStatus
    escalated_by: uuid.UUID
    governance_action_id: Optional[uuid.UUID] = None
    response: Optional[str] = None
    created_at: datetime


class EmergencyUpdateResponse(_Out):
    id: uuid.UUID
    actor_id: uuid.UUID
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    note: str
    created_at: datetime


class EmergencyResponse(_Out):
    id: uuid.UUID
    reference: str
    state: str
    district: str
    emergency_type: EmergencyType
    title: str
    description: str
    affected_area: str
    source: str
    priority: EmergencyPriority
    status: EmergencyStatus
    reported_by: uuid.UUID
    coordinator_id: Optional[uuid.UUID] = None
    started_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmergencyDetailResponse(EmergencyResponse):
    affected_facilities: List[AffectedFacilityResponse] = []
    tasks: List[EmergencyTaskResponse] = []
    escalations: List[EmergencyEscalationResponse] = []
    updates: List[EmergencyUpdateResponse] = []


class EmergencyDashboard(BaseModel):
    as_of: datetime
    scope: str
    active_emergencies: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    affected_facilities: int
    severely_disrupted_facilities: int
    open_tasks: int
    open_escalations: int
    emergency_supply_requests_open: int
    recent: List[EmergencyResponse]


class StaffAvailabilityRow(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    staff_assigned: int
    staff_present_today: int
    present_staff: List[Dict[str, Any]]


class ResourceStatusRow(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    low_or_out_items: List[Dict[str, Any]]
    open_supply_requests: List[Dict[str, Any]]
