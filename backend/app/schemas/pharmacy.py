import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pharmacy import (
    BatchStatus,
    ShortageSeverity,
    ShortageStatus,
    StockMovementType,
    StockTransferStatus,
)
from app.schemas.healthcare import MedicationResponse


# ============================================================================
# INVENTORY ITEM SCHEMAS
# ============================================================================

class InventoryItemBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reorder_level: int = Field(default=50, ge=0)
    minimum_stock_level: int = Field(default=20, ge=0)
    maximum_stock_level: int = Field(default=1000, ge=1)
    unit_cost: Optional[float] = Field(default=None, ge=0.0)


class InventoryItemCreate(InventoryItemBase):
    facility_id: uuid.UUID
    medication_id: uuid.UUID


class InventoryItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reorder_level: Optional[int] = Field(default=None, ge=0)
    minimum_stock_level: Optional[int] = Field(default=None, ge=0)
    maximum_stock_level: Optional[int] = Field(default=None, ge=1)
    unit_cost: Optional[float] = Field(default=None, ge=0.0)


class InventoryItemResponse(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    quantity_on_hand: int
    quantity_reserved: int
    available_quantity: int
    stock_status: str = "NORMAL"  # NORMAL, LOW_STOCK, SHORTAGE_RISK, OUT_OF_STOCK
    created_at: datetime
    updated_at: datetime
    medication: Optional[MedicationResponse] = None


# ============================================================================
# BATCH SCHEMAS
# ============================================================================

class InventoryBatchBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_number: str = Field(min_length=2, max_length=100)
    manufacture_date: date
    expiry_date: date
    supplier_name: Optional[str] = Field(default=None, max_length=255)


class InventoryBatchCreate(InventoryBatchBase):
    initial_quantity: int = Field(gt=0)


class InventoryBatchStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BatchStatus
    notes: Optional[str] = None


class InventoryBatchResponse(InventoryBatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inventory_item_id: uuid.UUID
    initial_quantity: int
    current_quantity: int
    status: BatchStatus
    created_at: datetime
    updated_at: datetime


# ============================================================================
# STOCK ADJUSTMENTS & RECEIPTS
# ============================================================================

class StockReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: uuid.UUID
    medication_id: uuid.UUID
    batch_number: str = Field(min_length=2, max_length=100)
    manufacture_date: date
    expiry_date: date
    quantity: int = Field(gt=0)
    supplier_name: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: uuid.UUID
    quantity: int = Field(description="Negative to deduct (damage, expiry), positive for correction")
    movement_type: StockMovementType = Field(description="ADJUSTMENT, DAMAGE, EXPIRY, RETURN")
    notes: str = Field(min_length=3, max_length=500)

    @field_validator("quantity")
    @classmethod
    def validate_non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Adjustment quantity cannot be zero")
        return v


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    inventory_item_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    movement_type: StockMovementType
    quantity: int
    balance_after: int
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    actor_id: uuid.UUID
    created_at: datetime


# ============================================================================
# DISPENSING & FEFO SCHEMAS
# ============================================================================

class DispenseItemFEFO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prescription_item_id: uuid.UUID
    quantity: int = Field(gt=0)


class DispensePrescriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[DispenseItemFEFO] = Field(min_length=1)
    notes: Optional[str] = None


class DispensingAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    batch_id: uuid.UUID
    allocated_quantity: int
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None


class DispensingRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prescription_id: uuid.UUID
    prescription_item_id: uuid.UUID
    facility_id: uuid.UUID
    dispensed_by_id: uuid.UUID
    quantity_dispensed: int
    notes: Optional[str] = None
    created_at: datetime
    allocations: List[DispensingAllocationResponse] = []


# ============================================================================
# STOCK TRANSFERS SCHEMAS
# ============================================================================

class StockTransferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_facility_id: uuid.UUID
    destination_facility_id: uuid.UUID
    medication_id: uuid.UUID
    requested_quantity: int = Field(gt=0)
    notes: Optional[str] = None


class StockTransferApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: Optional[str] = None


class StockTransferDispatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dispatched_quantity: int = Field(gt=0)
    batch_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class StockTransferReceiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    received_quantity: int = Field(gt=0)
    notes: Optional[str] = None


class StockTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transfer_number: str
    source_facility_id: uuid.UUID
    destination_facility_id: uuid.UUID
    medication_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    requested_quantity: int
    dispatched_quantity: Optional[int] = None
    received_quantity: Optional[int] = None
    status: StockTransferStatus
    requested_by_id: uuid.UUID
    approved_by_id: Optional[uuid.UUID] = None
    dispatched_by_id: Optional[uuid.UUID] = None
    received_by_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    medication: Optional[MedicationResponse] = None


# ============================================================================
# SHORTAGE INCIDENTS SCHEMAS
# ============================================================================

class ShortageIncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: uuid.UUID
    medication_id: uuid.UUID
    severity: ShortageSeverity = ShortageSeverity.MEDIUM
    description: str = Field(min_length=5, max_length=1000)
    estimated_impact_patients: Optional[int] = Field(default=None, ge=0)


class ShortageIncidentResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution_notes: str = Field(min_length=5, max_length=1000)


class ShortageIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_number: str
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    severity: ShortageSeverity
    status: ShortageStatus
    reported_by_id: uuid.UUID
    description: str
    estimated_impact_patients: Optional[int] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    medication: Optional[MedicationResponse] = None


# ============================================================================
# INTELLIGENCE, ANALYTICS & AI ASSISTANT SCHEMAS
# ============================================================================

class DemandForecastResponse(BaseModel):
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    medication_name: str
    current_stock: int
    avg_daily_consumption: float
    days_of_supply_remaining: float
    forecast_30d_demand: int
    predicted_stockout_date: Optional[date] = None
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float
    explainability: str


class AnomalyItem(BaseModel):
    facility_id: uuid.UUID
    medication_id: uuid.UUID
    medication_name: str
    anomaly_type: str  # SPIKE, RAPID_DEPLETION, UNUSUAL_ADJUSTMENT
    severity: str
    description: str
    confidence: float
    timestamp: datetime


class TransferRecommendationItem(BaseModel):
    medication_id: uuid.UUID
    medication_name: str
    shortage_facility_id: uuid.UUID
    shortage_facility_name: str
    surplus_facility_id: uuid.UUID
    surplus_facility_name: str
    recommended_quantity: int
    rationale: str
    confidence: float


class AIAssistantQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=500)
    facility_id: Optional[uuid.UUID] = None


class AIAssistantQueryResponse(BaseModel):
    query: str
    answer: str
    intent: str
    evidence: Dict[str, Any]
    confidence: float
    data_freshness: datetime
    disclaimer: str = "Decision-support recommendation only. Requires authorized human verification before taking clinical or procurement actions."
