import enum
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WarehouseStorageType(str, enum.Enum):
    AMBIENT = "AMBIENT"
    COLD_CHAIN = "COLD_CHAIN"
    HAZARDOUS = "HAZARDOUS"


class PurchaseRequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    DISTRICT_APPROVED = "DISTRICT_APPROVED"
    REJECTED = "REJECTED"
    CONVERTED_TO_PO = "CONVERTED_TO_PO"


class PurchaseRequestUrgency(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_TRANSIT = "IN_TRANSIT"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class ShipmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELAYED = "DELAYED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ShipmentEventType(str, enum.Enum):
    DEPARTED = "DEPARTED"
    MILESTONE_CHECKPOINT = "MILESTONE_CHECKPOINT"
    TEMPERATURE_EXCURSION = "TEMPERATURE_EXCURSION"
    DELAY_REPORTED = "DELAY_REPORTED"
    DELIVERED = "DELIVERED"


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reliability_score: Mapped[float] = mapped_column(Numeric(3, 2), default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class Warehouse(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "warehouses"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    storage_type: Mapped[WarehouseStorageType] = mapped_column(
        Enum(WarehouseStorageType, name="warehouse_storage_type_enum"),
        default=WarehouseStorageType.AMBIENT,
        nullable=False,
    )
    total_sqft: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    utilized_capacity_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    facility = relationship("Facility")


class PurchaseRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "purchase_requests"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[PurchaseRequestStatus] = mapped_column(
        Enum(PurchaseRequestStatus, name="purchase_request_status_enum"),
        default=PurchaseRequestStatus.SUBMITTED,
        nullable=False,
    )
    urgency: Mapped[PurchaseRequestUrgency] = mapped_column(
        Enum(PurchaseRequestUrgency, name="purchase_request_urgency_enum"),
        default=PurchaseRequestUrgency.ROUTINE,
        nullable=False,
    )
    total_estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    facility = relationship("Facility")
    requester = relationship("User", foreign_keys=[requested_by])
    purchase_orders = relationship("PurchaseOrder", back_populates="purchase_request")


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    purchase_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_requests.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    destination_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status_enum"),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
    )
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    destination_facility = relationship("Facility")
    purchase_request = relationship("PurchaseRequest", back_populates="purchase_orders")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    shipments = relationship("Shipment", back_populates="purchase_order")


class Shipment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shipments"

    tracking_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    transfer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stock_transfers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    origin_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    destination_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, name="shipment_status_enum"),
        default=ShipmentStatus.PENDING,
        nullable=False,
    )
    carrier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    temperature_monitored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="shipments")
    transfer = relationship("StockTransfer")
    origin_facility = relationship("Facility", foreign_keys=[origin_facility_id])
    destination_facility = relationship("Facility", foreign_keys=[destination_facility_id])
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "purchase_order_id IS NOT NULL OR transfer_id IS NOT NULL",
            name="ck_shipments_has_source",
        ),
    )


class ShipmentEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "shipment_events"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_type: Mapped[ShipmentEventType] = mapped_column(
        Enum(ShipmentEventType, name="shipment_event_type_enum"),
        nullable=False,
    )
    location_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    recorded_temp: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logged_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    shipment = relationship("Shipment", back_populates="events")
    logger = relationship("User")


# ============================================================================
# SUPPLY REQUESTS, RECEIPT VERIFICATION & HEALTH IMPACT (Roles 05, 07, 08, 10)
# Physical stock movement always goes through the shared StockTransfer ledger.
# ============================================================================

class SupplyRequestLevel(str, enum.Enum):
    PHC_TO_DISTRICT = "PHC_TO_DISTRICT"
    DISTRICT_TO_STATE = "DISTRICT_TO_STATE"


class SupplyRequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED = "REJECTED"
    ALLOCATED = "ALLOCATED"
    DISPATCHED = "DISPATCHED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class ReceiptVerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    DISCREPANCY_REPORTED = "DISCREPANCY_REPORTED"


class SupplyRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "supply_requests"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    level: Mapped[SupplyRequestLevel] = mapped_column(
        Enum(SupplyRequestLevel, name="supply_request_level_enum"), index=True, nullable=False
    )
    requesting_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    fulfilling_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), index=True, nullable=True
    )
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    received_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority: Mapped[PurchaseRequestUrgency] = mapped_column(
        Enum(PurchaseRequestUrgency, name="purchase_request_urgency_enum"),
        default=PurchaseRequestUrgency.ROUTINE, index=True, nullable=False,
    )
    status: Mapped[SupplyRequestStatus] = mapped_column(
        Enum(SupplyRequestStatus, name="supply_request_status_enum"),
        default=SupplyRequestStatus.SUBMITTED, index=True, nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    required_by: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    emergency_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="SET NULL"), index=True, nullable=True
    )
    parent_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supply_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    transfer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stock_transfers.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    medication = relationship("Medication")
    requesting_facility = relationship("Facility", foreign_keys=[requesting_facility_id])
    fulfilling_facility = relationship("Facility", foreign_keys=[fulfilling_facility_id])
    transfer = relationship("StockTransfer")
    events = relationship("SupplyRequestEvent", back_populates="request", cascade="all, delete-orphan",
                          order_by="SupplyRequestEvent.created_at")

    __table_args__ = (
        CheckConstraint("requested_quantity > 0", name="ck_supply_requests_qty_positive"),
    )


class SupplyRequestEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "supply_request_events"

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supply_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    request = relationship("SupplyRequest", back_populates="events")


class SupplyReceipt(Base, UUIDPrimaryKeyMixin):
    """Receiver-verified receipt for a transfer; stock is updated with the verified quantity only."""
    __tablename__ = "supply_receipts"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stock_transfers.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    supply_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supply_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False
    )
    dispatched_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    damaged_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    verification_status: Mapped[ReceiptVerificationStatus] = mapped_column(
        Enum(ReceiptVerificationStatus, name="receipt_verification_status_enum"), index=True, nullable=False
    )
    discrepancy_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SupplyHealthImpact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Aggregated shortage impact the DSCO shares with the DHO (no transaction-level detail)."""
    __tablename__ = "supply_health_impacts"

    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    affected_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True
    )
    shortage_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shortage_incidents.id", ondelete="SET NULL"), nullable=True
    )
    medication_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="SET NULL"), nullable=True
    )
    impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    shared_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
