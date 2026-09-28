"""District emergency coordination domain (Role 08).

Emergencies reference existing facilities, users, and medications; supply needs
are raised as shared SupplyRequests (emergency-linked) rather than a parallel
stock workflow.
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmergencyType(str, enum.Enum):
    FLOOD = "FLOOD"
    CYCLONE = "CYCLONE"
    HEATWAVE = "HEATWAVE"
    DISEASE_CLUSTER = "DISEASE_CLUSTER"
    MASS_CASUALTY = "MASS_CASUALTY"
    FIRE = "FIRE"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    OTHER = "OTHER"


class EmergencyPriority(str, enum.Enum):
    """Assigned by an authorized human through the emergency workflow — never by AI."""
    UNASSIGNED = "UNASSIGNED"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EmergencyStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESPONSE_STARTED = "RESPONSE_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class EmergencyTaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EmergencyEscalationStatus(str, enum.Enum):
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESPONDED = "RESPONDED"
    CLOSED = "CLOSED"


class EmergencyIncident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_incidents"

    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    emergency_type: Mapped[EmergencyType] = mapped_column(Enum(EmergencyType, name="emergency_type_enum"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_area: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[EmergencyPriority] = mapped_column(
        Enum(EmergencyPriority, name="emergency_priority_enum"), default=EmergencyPriority.UNASSIGNED, nullable=False
    )
    priority_set_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[EmergencyStatus] = mapped_column(
        Enum(EmergencyStatus, name="emergency_status_enum"), default=EmergencyStatus.PENDING, index=True, nullable=False
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    coordinator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_confirmed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    affected_facilities = relationship("EmergencyAffectedFacility", back_populates="incident", cascade="all, delete-orphan")
    tasks = relationship("EmergencyTask", back_populates="incident", cascade="all, delete-orphan",
                         order_by="EmergencyTask.created_at")
    escalations = relationship("EmergencyEscalation", back_populates="incident", cascade="all, delete-orphan",
                               order_by="EmergencyEscalation.created_at")
    updates = relationship("EmergencyUpdate", back_populates="incident", cascade="all, delete-orphan",
                           order_by="EmergencyUpdate.created_at")


class EmergencyAffectedFacility(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_affected_facilities"
    __table_args__ = (UniqueConstraint("incident_id", "facility_id", name="uq_emergency_facility"),)

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    service_disruption: Mapped[str] = mapped_column(String(40), default="NONE", nullable=False)  # NONE | PARTIAL | SEVERE | CLOSED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident = relationship("EmergencyIncident", back_populates="affected_facilities")
    facility = relationship("Facility")


class EmergencyTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_tasks"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True
    )
    assigned_role: Mapped[str] = mapped_column(String(60), nullable=False)
    assigned_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EmergencyTaskStatus] = mapped_column(
        Enum(EmergencyTaskStatus, name="emergency_task_status_enum"), default=EmergencyTaskStatus.OPEN, nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    completion_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    incident = relationship("EmergencyIncident", back_populates="tasks")


class EmergencyEscalation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emergency_escalations"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_role: Mapped[str] = mapped_column(String(60), nullable=False)
    to_role: Mapped[str] = mapped_column(String(60), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EmergencyEscalationStatus] = mapped_column(
        Enum(EmergencyEscalationStatus, name="emergency_escalation_status_enum"),
        default=EmergencyEscalationStatus.SENT, nullable=False,
    )
    escalated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    governance_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("governance_actions.id", ondelete="SET NULL"), nullable=True
    )
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident = relationship("EmergencyIncident", back_populates="escalations")


class EmergencyUpdate(Base, UUIDPrimaryKeyMixin):
    """Immutable timeline of status changes and coordination notes."""
    __tablename__ = "emergency_updates"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    incident = relationship("EmergencyIncident", back_populates="updates")
