import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.supply_chain import (
    PurchaseRequestUrgency,
    ReceiptVerificationStatus,
    SupplyRequestLevel,
    SupplyRequestStatus,
)


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SupplyRequestCreate(_In):
    requesting_facility_id: uuid.UUID
    medication_id: uuid.UUID
    requested_quantity: int = Field(gt=0, le=1_000_000)
    priority: PurchaseRequestUrgency = PurchaseRequestUrgency.ROUTINE
    reason: str = Field(min_length=5, max_length=2000)
    required_by: Optional[date] = None
    emergency_incident_id: Optional[uuid.UUID] = None


class SupplyRequestDecision(_In):
    decision: Literal["START_REVIEW", "APPROVE", "PARTIALLY_APPROVE", "REJECT", "REQUEST_CLARIFICATION", "CLOSE"]
    approved_quantity: Optional[int] = Field(None, gt=0)
    reason: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode="after")
    def _rules(self):
        if self.decision in ("PARTIALLY_APPROVE", "REJECT", "REQUEST_CLARIFICATION", "CLOSE") and not self.reason:
            raise ValueError(f"reason is required for {self.decision}")
        if self.decision == "PARTIALLY_APPROVE" and not self.approved_quantity:
            raise ValueError("approved_quantity is required for PARTIALLY_APPROVE")
        return self


class SupplyRequestClarify(_In):
    note: str = Field(min_length=3, max_length=2000)
    requested_quantity: Optional[int] = Field(None, gt=0)


class SupplyAllocationCreate(_In):
    fulfilling_facility_id: uuid.UUID
    quantity: int = Field(gt=0)
    notes: Optional[str] = Field(None, max_length=1000)


class SupplyEscalationCreate(_In):
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=5, max_length=2000)


class SupplyRequestEventResponse(_Out):
    id: uuid.UUID
    actor_id: uuid.UUID
    from_status: Optional[str] = None
    to_status: str
    note: Optional[str] = None
    created_at: datetime


class SupplyRequestResponse(_Out):
    id: uuid.UUID
    reference: str
    level: SupplyRequestLevel
    requesting_facility_id: uuid.UUID
    fulfilling_facility_id: Optional[uuid.UUID] = None
    state: str
    district: str
    medication_id: uuid.UUID
    requested_quantity: int
    approved_quantity: Optional[int] = None
    received_quantity: Optional[int] = None
    priority: PurchaseRequestUrgency
    status: SupplyRequestStatus
    reason: str
    required_by: Optional[date] = None
    emergency_incident_id: Optional[uuid.UUID] = None
    parent_request_id: Optional[uuid.UUID] = None
    transfer_id: Optional[uuid.UUID] = None
    requested_by: uuid.UUID
    reviewed_by: Optional[uuid.UUID] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StockOption(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    facility_type: str
    district: str
    available_quantity: int
    committed_quantity: int
    allocatable_quantity: int
    nearest_expiry: Optional[date] = None


class SupplyRequestDetail(SupplyRequestResponse):
    medication_name: Optional[str] = None
    requesting_facility_name: Optional[str] = None
    requesting_facility_stock: Optional[int] = None
    requesting_facility_30d_consumption: Optional[int] = None
    events: List[SupplyRequestEventResponse] = []
    stock_options: List[StockOption] = []


class SupplyReceiptResponse(_Out):
    id: uuid.UUID
    transfer_id: uuid.UUID
    supply_request_id: Optional[uuid.UUID] = None
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    dispatched_quantity: int
    received_quantity: int
    damaged_quantity: int
    batch_number: str
    expiry_date: date
    verification_status: ReceiptVerificationStatus
    discrepancy_reason: Optional[str] = None
    verified_by: uuid.UUID
    verified_at: datetime


class HealthImpactCreate(_In):
    affected_facility_id: Optional[uuid.UUID] = None
    shortage_incident_id: Optional[uuid.UUID] = None
    medication_id: Optional[uuid.UUID] = None
    impact_summary: str = Field(min_length=10, max_length=3000)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class HealthImpactResponse(_Out):
    id: uuid.UUID
    state: str
    district: str
    affected_facility_id: Optional[uuid.UUID] = None
    shortage_incident_id: Optional[uuid.UUID] = None
    medication_id: Optional[uuid.UUID] = None
    impact_summary: str
    severity: str
    shared_by: uuid.UUID
    acknowledged_by: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime


class MonitoringRunResponse(BaseModel):
    scope: str
    run_at: datetime
    checks: Dict[str, int]
    alerts_created: int
    alerts_already_open: int
    method: str


class StateSupplyDashboard(BaseModel):
    as_of: datetime
    scope: str
    warehouses: List[Dict[str, Any]]
    district_overview: List[Dict[str, Any]]
    requests_by_status: Dict[str, int]
    pending_district_requests: int
    emergency_requests_open: int
    allocations_awaiting_dispatch: int
    in_transit_transfers: int
    delayed_transfers: int
    receipt_discrepancies_30d: int
    warehouse_batches_expiring_60d: int
    unacknowledged_supply_alerts: int
