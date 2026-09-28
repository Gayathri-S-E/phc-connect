import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.supply_chain import (
    PurchaseOrderStatus,
    PurchaseRequestStatus,
    PurchaseRequestUrgency,
    ShipmentEventType,
    ShipmentStatus,
)


# --- Suppliers ---
class SupplierCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    license_number: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = None
    reliability_score: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    license_number: Optional[str] = None
    address: Optional[str] = None
    reliability_score: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Purchase requests ---
class PurchaseRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: uuid.UUID
    urgency: PurchaseRequestUrgency = PurchaseRequestUrgency.ROUTINE
    total_estimated_cost: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=2000)


class PurchaseRequestDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: Optional[str] = Field(default=None, max_length=2000)


class PurchaseRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    requested_by: uuid.UUID
    status: PurchaseRequestStatus
    urgency: PurchaseRequestUrgency
    total_estimated_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# --- Purchase orders ---
class PurchaseOrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: uuid.UUID
    destination_facility_id: uuid.UUID
    purchase_request_id: Optional[uuid.UUID] = None
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_number: str
    purchase_request_id: Optional[uuid.UUID] = None
    supplier_id: uuid.UUID
    destination_facility_id: uuid.UUID
    created_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None
    status: PurchaseOrderStatus
    total_amount: Optional[Decimal] = None
    expected_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


# --- Shipments ---
class ShipmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purchase_order_id: Optional[uuid.UUID] = None
    transfer_id: Optional[uuid.UUID] = None
    carrier_name: Optional[str] = Field(default=None, max_length=255)
    tracking_number: Optional[str] = Field(default=None, min_length=3, max_length=100)
    temperature_monitored: bool = False

    @model_validator(mode="after")
    def exactly_one_source(self):
        if (self.purchase_order_id is None) == (self.transfer_id is None):
            raise ValueError("Provide exactly one of purchase_order_id or transfer_id")
        return self


class ShipmentEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: ShipmentEventType
    location_name: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    recorded_temp: Optional[Decimal] = Field(default=None, ge=-100, le=100)
    notes: Optional[str] = Field(default=None, max_length=2000)


class ShipmentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    shipment_id: uuid.UUID
    event_type: ShipmentEventType
    location_name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    recorded_temp: Optional[Decimal] = None
    notes: Optional[str] = None
    logged_by: uuid.UUID
    timestamp: datetime


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tracking_number: str
    purchase_order_id: Optional[uuid.UUID] = None
    transfer_id: Optional[uuid.UUID] = None
    origin_facility_id: Optional[uuid.UUID] = None
    destination_facility_id: uuid.UUID
    status: ShipmentStatus
    carrier_name: Optional[str] = None
    temperature_monitored: bool
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    events: List[ShipmentEventResponse] = []


# --- Shortage escalation ---
class ShortageEscalateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["DISTRICT", "STATE"]
    notes: str = Field(min_length=5, max_length=1000)
