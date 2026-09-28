import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.identity import ScopeLevel


class UserRoleAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    scope_level: ScopeLevel = ScopeLevel.FACILITY


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_id: uuid.UUID
    role_name: str
    role_code: str
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    scope_level: ScopeLevel
    created_at: datetime


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    initial_role_ids: Optional[List[uuid.UUID]] = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    phone_number: Optional[str] = None
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: List[UserRoleResponse] = []
