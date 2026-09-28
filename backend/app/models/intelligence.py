import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDPrimaryKeyMixin


class AlertType(str, enum.Enum):
    LOW_STOCK = "LOW_STOCK"
    CRITICAL_SHORTAGE = "CRITICAL_SHORTAGE"
    BATCH_EXPIRING = "BATCH_EXPIRING"
    COLD_CHAIN_BREACH = "COLD_CHAIN_BREACH"
    ABNORMAL_DEMAND = "ABNORMAL_DEMAND"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class Alert(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "alerts"

    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type_enum"),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    facility = relationship("Facility")
    acknowledger = relationship("User")


class SystemConfig(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "system_configs"

    config_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    config_value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updater = relationship("User")


class ForecastRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "forecast_records"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("medications.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_consumption: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    confidence_interval_lower: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    confidence_interval_upper: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    facility = relationship("Facility")
    medication = relationship("Medication")
