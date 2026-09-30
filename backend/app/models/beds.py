import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WardType(str, enum.Enum):
    GENERAL = "GENERAL"
    MATERNITY = "MATERNITY"
    PAEDIATRIC = "PAEDIATRIC"
    ISOLATION = "ISOLATION"
    ICU = "ICU"


class BedInventory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Current bed capacity/occupancy for one ward type at a facility. `updated_at` is the freshness marker."""
    __tablename__ = "bed_inventory"
    __table_args__ = (
        UniqueConstraint("facility_id", "ward_type", name="uq_bed_inventory_facility_ward"),
        CheckConstraint("total_beds >= 0", name="chk_bed_total_non_negative"),
        CheckConstraint("occupied_beds >= 0", name="chk_bed_occupied_non_negative"),
        CheckConstraint("occupied_beds <= total_beds", name="chk_bed_occupied_lte_total"),
    )

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    ward_type: Mapped[WardType] = mapped_column(Enum(WardType, name="ward_type_enum"), nullable=False)
    total_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    facility = relationship("Facility")

    @property
    def available_beds(self) -> int:
        return self.total_beds - self.occupied_beds


class BedCensusLog(Base, UUIDPrimaryKeyMixin):
    """Append-only history of every capacity/occupancy change (never updated or deleted by the application)."""
    __tablename__ = "bed_census_log"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    ward_type: Mapped[WardType] = mapped_column(Enum(WardType, name="ward_type_enum"), nullable=False)
    total_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_total_beds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_occupied_beds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
