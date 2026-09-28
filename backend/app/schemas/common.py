from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class DataResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    data: List[T]
    pagination: PaginationMeta
