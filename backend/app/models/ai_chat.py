import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIPendingActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class AIConversation(Base, UUIDPrimaryKeyMixin):
    """One multi-turn chat between a single user and a single role assistant."""
    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    assistant: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="New conversation")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, index=True, nullable=False
    )

    messages = relationship(
        "AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at"
    )
    pending_actions = relationship("AIPendingAction", cascade="all, delete-orphan")


class AIMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(12), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    conversation = relationship("AIConversation", back_populates="messages")


class AIPendingAction(Base, UUIDPrimaryKeyMixin):
    """A consequential action the assistant proposed. Nothing runs until the same user confirms it here."""
    __tablename__ = "ai_pending_actions"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    assistant: Mapped[str] = mapped_column(String(40), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    arguments: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AIPendingActionStatus] = mapped_column(
        Enum(AIPendingActionStatus, name="ai_pending_action_status_enum"),
        default=AIPendingActionStatus.PENDING, nullable=False, index=True,
    )
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
