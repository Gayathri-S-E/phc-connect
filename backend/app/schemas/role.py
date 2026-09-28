import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    module: str
    resource: str
    action: str
    description: Optional[str] = None
    is_active: bool


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[uuid.UUID]] = None


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RolePermissionAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_ids: List[uuid.UUID]


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []
