import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8)


class RegisterPatientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=50)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str = Field(min_length=8)


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    phone_number: Optional[str] = None
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    is_active: bool
    is_verified: bool
    roles: List[str]
    permissions: List[str]
