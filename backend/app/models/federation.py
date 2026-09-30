"""Federated modelling tables. They hold ONLY aggregate model parameters, never raw transactions or patients.

* FederatedLocalUpdate   - one row per (state, medication): the parameters a state computed from its own ledger.
* FederatedNationalPrior - one row per medication: the sample-size-weighted combination of the local updates.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPrimaryKeyMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FederatedLocalUpdate(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "federated_local_updates"
    __table_args__ = (UniqueConstraint("state_key", "medication_id", name="uq_fed_local_state_medication"),)

    state_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # lower(trim(state))
    state_label: Mapped[str] = mapped_column(String(100), nullable=False)
    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), index=True, nullable=False)
    round_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    n_facilities: Mapped[int] = mapped_column(Integer, nullable=False)
    n_samples: Mapped[int] = mapped_column(Integer, nullable=False)  # facility-days observed
    mean_daily_rate: Mapped[float] = mapped_column(Float, nullable=False)  # units / facility / day
    variance: Mapped[float] = mapped_column(Float, nullable=False)
    seasonality: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)  # {"1": {"factor": f, "n": n}}
    computed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class FederatedNationalPrior(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "federated_national_priors"

    medication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    round_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    n_states: Mapped[int] = mapped_column(Integer, nullable=False)
    n_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_daily_rate: Mapped[float] = mapped_column(Float, nullable=False)
    variance: Mapped[float] = mapped_column(Float, nullable=False)
    seasonality: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    contributing_states: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    aggregated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    aggregated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
