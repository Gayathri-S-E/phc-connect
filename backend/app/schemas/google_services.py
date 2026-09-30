from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class GoogleServiceStatus(BaseModel):
    """Booleans only: never any key, path, project id or credential content."""
    gemini: bool
    voice_translate: bool
    maps: bool
    service_account: bool
    bigquery: bool
    vertex_forecast: bool


class NearestFacilitiesRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, min_length=3, max_length=300)  # geocoded when lat/lng are absent
    limit: int = Field(5, ge=1, le=20)
    facility_type: Optional[str] = Field(None, max_length=40)

    @model_validator(mode="after")
    def _need_location(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude.")
        if self.latitude is None and not self.address:
            raise ValueError("Provide latitude and longitude, or an address.")
        return self


class NearestFacility(BaseModel):
    id: str
    name: str
    code: str
    facility_type: str
    state: str
    district: str
    latitude: float
    longitude: float
    straight_line_km: float
    driving_distance_km: Optional[float] = None
    driving_minutes: Optional[float] = None


class NearestFacilitiesResponse(BaseModel):
    origin_latitude: float
    origin_longitude: float
    origin_label: Optional[str] = None
    method: str  # 'google_routes' (haversine shortlist refined by driving time) | 'haversine_only'
    method_note: str
    facilities: List[NearestFacility]


class BigQueryExportRequest(BaseModel):
    aggregate_date: Optional[date] = None  # defaults to today (UTC)


class BigQueryExportResponse(BaseModel):
    aggregate_date: date
    scope: str
    rows_exported: int
    beds_included: bool
    columns: List[str]


class NationalSummaryRow(BaseModel):
    state: Optional[str] = None
    facilities: Optional[int] = None
    appointments: Optional[int] = None
    stockouts: Optional[int] = None
    staff_present_days: Optional[int] = None
    staff_assigned_days: Optional[int] = None
    beds_total_days: Optional[int] = None
    beds_occupied_days: Optional[int] = None


class NationalSummaryResponse(BaseModel):
    date_from: date
    date_to: date
    scope: str
    rows: List[NationalSummaryRow]
    source: str = "bigquery"
