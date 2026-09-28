import enum
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationType(str, enum.Enum):
    MINISTRY = "MINISTRY"
    STATE_HEALTH_DEPT = "STATE_HEALTH_DEPT"
    DISTRICT_HEALTH_OFFICE = "DISTRICT_HEALTH_OFFICE"
    VENDOR = "VENDOR"


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    org_type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="organization_type_enum"),
        nullable=False,
        default=OrganizationType.DISTRICT_HEALTH_OFFICE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    facilities = relationship("Facility", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")
