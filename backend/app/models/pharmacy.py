import enum
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BatchStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    QUARANTINED = "QUARANTINED"
    EXPIRED = "EXPIRED"
    DEPLETED = "DEPLETED"
    DAMAGED = "DAMAGED"
    RECALLED = "RECALLED"


class StockMovementType(str, enum.Enum):
    RECEIPT = "RECEIPT"
    DISPENSE = "DISPENSE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    ADJUSTMENT = "ADJUSTMENT"
    DAMAGE = "DAMAGE"
    EXPIRY = "EXPIRY"
    RETURN = "RETURN"


class StockTransferStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ShortageSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ShortageStatus(str, enum.Enum):
    REPORTED = "REPORTED"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED_DISTRICT = "ESCALATED_DISTRICT"
    ESCALATED_STATE = "ESCALATED_STATE"
    ACTION_TAKEN = "ACTION_TAKEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class StockMovementReferenceType(str, enum.Enum):
    PRESCRIPTION = "PRESCRIPTION"
    TRANSFER = "TRANSFER"
    PO = "PO"
    ADJUSTMENT = "ADJUSTMENT"


class TransferUrgency(str, enum.Enum):
    NORMAL = "NORMAL"
    EMERGENCY_SHORTAGE = "EMERGENCY_SHORTAGE"


class InventoryItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Facility-level aggregated stock for a specific Medication.
    Tracks total stock, safety thresholds, and reservations.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("facility_id", "medication_id", name="uq_facility_medication_inventory"),
        CheckConstraint("quantity_on_hand >= 0", name="chk_inventory_qty_non_negative"),
        CheckConstraint("quantity_reserved >= 0", name="chk_inventory_reserved_non_negative"),
        CheckConstraint("reorder_level >= critical_level", name="chk_inventory_reorder_gte_critical"),
    )

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    critical_level: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    minimum_stock_level: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    maximum_stock_level: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    # Relationships
    facility = relationship("Facility")
    medication = relationship("Medication")
    batches = relationship("InventoryBatch", back_populates="inventory_item", cascade="all, delete-orphan")
    movements = relationship("StockMovement", back_populates="inventory_item", cascade="all, delete-orphan")

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity_on_hand - self.quantity_reserved)


class InventoryBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual manufactured batch/lot of medication at a health facility.
    Essential for FEFO (First-Expire, First-Out) physical stock allocation.
    """
    __tablename__ = "inventory_batches"
    __table_args__ = (
        UniqueConstraint("inventory_item_id", "batch_number", name="uq_item_batch_number"),
        CheckConstraint("current_quantity >= 0", name="chk_batch_qty_non_negative"),
        CheckConstraint("initial_quantity > 0", name="chk_batch_initial_qty_positive"),
        Index("ix_inventory_batches_item_expiry", "inventory_item_id", "expiry_date"),
    )

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    batch_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    manufacture_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    initial_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status_enum"),
        default=BatchStatus.AVAILABLE,
        nullable=False,
    )
    supplier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="batches")
    supplier = relationship("Supplier")
    allocations = relationship("DispensingAllocation", back_populates="batch")


class StockMovement(Base, UUIDPrimaryKeyMixin):
    """
    Append-only physical stock ledger. Every physical adjustment,
    receipt, dispense, or transfer creates an immutable ledger row.
    """
    __tablename__ = "stock_movements"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_batches.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    movement_type: Mapped[StockMovementType] = mapped_column(
        Enum(StockMovementType, name="stock_movement_type_enum"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[Optional[StockMovementReferenceType]] = mapped_column(
        Enum(StockMovementReferenceType, name="stock_movement_reference_type_enum"),
        nullable=True,
    )
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    facility = relationship("Facility")
    inventory_item = relationship("InventoryItem", back_populates="movements")
    batch = relationship("InventoryBatch")
    actor = relationship("User")


class DispensingRecord(Base, UUIDPrimaryKeyMixin):
    """
    Physical pharmacy dispensing record connecting clinical prescription to stock deductions.
    """
    __tablename__ = "dispensing_records"

    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    prescription_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescription_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    dispensed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity_dispensed: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    prescription = relationship("Prescription")
    prescription_item = relationship("PrescriptionItem")
    facility = relationship("Facility")
    dispensed_by = relationship("User")
    allocations = relationship("DispensingAllocation", back_populates="dispensing_record", cascade="all, delete-orphan")


class DispensingAllocation(Base, UUIDPrimaryKeyMixin):
    """
    Specific batch breakdown for a dispensing transaction (FEFO multi-batch fulfillment).
    """
    __tablename__ = "dispensing_allocations"

    dispensing_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dispensing_records.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_batches.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    allocated_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    dispensing_record = relationship("DispensingRecord", back_populates="allocations")
    batch = relationship("InventoryBatch", back_populates="allocations")


class StockTransfer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Facility-to-facility medicine transfer request and 2-phase dispatch/receive pipeline.
    """
    __tablename__ = "stock_transfers"

    transfer_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    source_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    destination_facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    dispatched_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    received_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[StockTransferStatus] = mapped_column(
        Enum(StockTransferStatus, name="stock_transfer_status_enum"),
        default=StockTransferStatus.REQUESTED,
        nullable=False,
    )
    urgency: Mapped[TransferUrgency] = mapped_column(
        Enum(TransferUrgency, name="transfer_urgency_enum"),
        default=TransferUrgency.NORMAL,
        nullable=False,
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    dispatched_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    received_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    source_facility = relationship("Facility", foreign_keys=[source_facility_id])
    destination_facility = relationship("Facility", foreign_keys=[destination_facility_id])
    medication = relationship("Medication")
    batch = relationship("InventoryBatch")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    dispatched_by = relationship("User", foreign_keys=[dispatched_by_id])
    received_by = relationship("User", foreign_keys=[received_by_id])


class ShortageIncident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Facility stockout and critical medicine shortage escalation incident.
    """
    __tablename__ = "shortage_incidents"

    incident_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    severity: Mapped[ShortageSeverity] = mapped_column(
        Enum(ShortageSeverity, name="shortage_severity_enum"),
        default=ShortageSeverity.MEDIUM,
        nullable=False,
    )
    status: Mapped[ShortageStatus] = mapped_column(
        Enum(ShortageStatus, name="shortage_status_enum"),
        default=ShortageStatus.REPORTED,
        nullable=False,
    )
    reported_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_impact_patients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    facility = relationship("Facility")
    medication = relationship("Medication")
    reported_by = relationship("User")
