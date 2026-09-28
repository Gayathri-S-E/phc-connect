import uuid
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facilities.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


from sqlalchemy import event


@event.listens_for(AuditLog, "before_update")
def _audit_log_before_update(mapper, connection, target):
    raise RuntimeError("Audit logs are strictly immutable and cannot be modified.")


@event.listens_for(AuditLog, "before_delete")
def _audit_log_before_delete(mapper, connection, target):
    raise RuntimeError("Audit logs are strictly immutable and cannot be deleted.")

