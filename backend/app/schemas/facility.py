import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.organization import OrganizationType
from app.models.facility import FacilityType


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=100)
    org_type: OrganizationType = OrganizationType.DISTRICT_HEALTH_OFFICE


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    org_type: OrganizationType
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FacilityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: uuid.UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=100)
    facility_type: FacilityType = FacilityType.PHC
    state: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FacilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str
    facility_type: FacilityType
    state: str
    district: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
