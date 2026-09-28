import enum
import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FacilityType(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"
    DISTRICT_HOSPITAL = "DISTRICT_HOSPITAL"
    CENTRAL_WAREHOUSE = "CENTRAL_WAREHOUSE"
    DISTRICT_WAREHOUSE = "DISTRICT_WAREHOUSE"


class Facility(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "facilities"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    facility_type: Mapped[FacilityType] = mapped_column(
        Enum(FacilityType, name="facility_type_enum"),
        nullable=False,
        default=FacilityType.PHC,
    )
    state: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="facilities")
    users = relationship("User", back_populates="facility")
