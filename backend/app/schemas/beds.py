import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.beds import WardType


class BedOccupancyUpdate(BaseModel):
    """`occupied_beds` is always required. `total_beds` changes capacity and needs beds.inventory.manage."""
    model_config = ConfigDict(extra="forbid")

    occupied_beds: int = Field(ge=0, le=100000)
    total_beds: Optional[int] = Field(default=None, ge=0, le=100000)
    note: Optional[str] = Field(default=None, max_length=500)


class BedInventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    ward_type: WardType
    total_beds: int
    occupied_beds: int
    available_beds: int
    last_updated_by: Optional[uuid.UUID] = None
    updated_at: datetime


class BedCensusLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    ward_type: WardType
    total_beds: int
    occupied_beds: int
    previous_total_beds: Optional[int] = None
    previous_occupied_beds: Optional[int] = None
    recorded_by: Optional[uuid.UUID] = None
    note: Optional[str] = None
    recorded_at: datetime


class FacilityBedsResponse(BaseModel):
    facility_id: uuid.UUID
    as_of: datetime
    status: str  # FRESH | STALE | NO_DATA
    last_updated_at: Optional[datetime] = None
    total_beds: Optional[int] = None
    occupied_beds: Optional[int] = None
    available_beds: Optional[int] = None
    wards: List[BedInventoryResponse]
