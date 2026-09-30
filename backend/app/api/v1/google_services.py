"""Optional Google Cloud services: Maps nearest-facility ranking and BigQuery aggregate export/rollup.

Everything is env-gated. When a service is not configured the endpoint answers 503 AI_NOT_CONFIGURED; it never
returns fabricated data. (Nearest-facility still works without a Maps key, using real haversine distances, and says so.)
"""
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import safety
from app.ai.llm import gemini_configured
from app.api.deps import AuthenticatedUserContext, get_current_user
from app.api.scope import resolve_jurisdiction
from app.core.config import settings
from app.core.database import get_db_session
from app.core.exceptions import AppException
from app.core.permissions import SystemPermissions as P
from app.integrations.google import auth as google_auth
from app.integrations.google.bigquery import (
    EXPORT_COLUMN_NAMES, BigQueryClientProtocol, collect_facility_aggregates, get_bigquery_client,
)
from app.integrations.google.errors import GoogleError, NotConfigured, to_app_exception
from app.integrations.google.maps import FacilityPoint, MapsClient, get_maps_client, rank_nearest
from app.models.facility import Facility, FacilityType
from app.models.identity import ScopeLevel
from app.schemas.common import DataResponse
from app.schemas.google_services import (
    BigQueryExportRequest, BigQueryExportResponse, GoogleServiceStatus, NationalSummaryResponse,
    NationalSummaryRow, NearestFacilitiesRequest, NearestFacilitiesResponse, NearestFacility,
)

router = APIRouter(prefix="/google", tags=["Google Cloud services"])

EXPORT_PERMISSION = P.GOVERNANCE_REPORT_GENERATE
SUMMARY_PERMISSION = P.GOVERNANCE_REPORT_GENERATE


def _limit(user: AuthenticatedUserContext, op: str) -> None:
    safety.rate_limiter.check(f"google:{op}:{user.id}", limit=settings.GOOGLE_INTEGRATIONS_RATE_LIMIT_PER_MINUTE)


def _bq_ready(bq: BigQueryClientProtocol) -> None:
    if not bq.is_configured():
        raise to_app_exception(NotConfigured("BigQuery"), "BigQuery")


@router.get("/status", response_model=DataResponse[GoogleServiceStatus])
async def google_status(user: AuthenticatedUserContext = Depends(get_current_user)):
    creds = google_auth.is_configured()
    vertex = (os.environ.get("FORECAST_BACKEND", "local").strip().lower() == "vertex"
              and all(os.environ.get(k) for k in ("VERTEX_PROJECT", "VERTEX_LOCATION", "VERTEX_ENDPOINT_ID"))
              and creds)
    return DataResponse(data=GoogleServiceStatus(
        gemini=gemini_configured(),
        voice_translate=bool(settings.GOOGLE_CLOUD_API_KEY),
        maps=bool(settings.GOOGLE_MAPS_API_KEY),
        service_account=creds,
        bigquery=bool(settings.GOOGLE_CLOUD_PROJECT and settings.BIGQUERY_DATASET and creds),
        vertex_forecast=bool(vertex),
    ))


@router.post("/maps/nearest-facilities", response_model=DataResponse[NearestFacilitiesResponse])
async def nearest_facilities(
    payload: NearestFacilitiesRequest,
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    maps: MapsClient = Depends(get_maps_client),
):
    _limit(user, "maps")
    lat, lng, label = payload.latitude, payload.longitude, None
    if lat is None:
        if not maps.is_configured():
            raise to_app_exception(NotConfigured("Maps"), "Google Maps geocoding")
        try:
            hit = await maps.geocode(payload.address or "")
        except GoogleError as exc:
            raise to_app_exception(exc, "Google Maps geocoding")
        if hit is None:
            raise AppException("Address Not Found", "No location matched that address.", 404, "ADDRESS_NOT_FOUND")
        lat, lng, label = hit

    stmt = select(Facility).where(Facility.is_active.is_(True), Facility.latitude.is_not(None),
                                  Facility.longitude.is_not(None))
    if payload.facility_type:
        try:
            stmt = stmt.where(Facility.facility_type == FacilityType(payload.facility_type.strip().upper()))
        except ValueError:
            raise AppException("Invalid Facility Type", "Unknown facility_type.", 422, "INVALID_FACILITY_TYPE") from None
    found = list((await session.execute(stmt)).scalars().all())
    points = [FacilityPoint(str(f.id), f.name, f.code, getattr(f.facility_type, "value", str(f.facility_type)),
                            f.state, f.district, float(f.latitude), float(f.longitude)) for f in found]
    method, rows = await rank_nearest(maps, lat, lng, points, payload.limit)
    if method == "google_routes":
        note = "Ranked by straight-line distance, then re-ranked by Google driving time for the closest candidates."
    else:
        why = ("Google Maps is not configured." if not maps.is_configured()
               else "the Google Routes request failed.")
        note = f"Ranked by straight-line (great-circle) distance; driving time is unavailable because {why}"
    return DataResponse(data=NearestFacilitiesResponse(
        origin_latitude=lat, origin_longitude=lng, origin_label=label, method=method, method_note=note,
        facilities=[NearestFacility(id=r["facility"].id, name=r["facility"].name, code=r["facility"].code,
                                    facility_type=r["facility"].facility_type, state=r["facility"].state,
                                    district=r["facility"].district, latitude=r["facility"].latitude,
                                    longitude=r["facility"].longitude, straight_line_km=r["straight_line_km"],
                                    driving_distance_km=r["driving_distance_km"],
                                    driving_minutes=r["driving_minutes"]) for r in rows]))


@router.post("/bigquery/export", response_model=DataResponse[BigQueryExportResponse])
async def bigquery_export(
    payload: BigQueryExportRequest,
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    bq: BigQueryClientProtocol = Depends(get_bigquery_client),
):
    jurisdiction = await resolve_jurisdiction(user, EXPORT_PERMISSION, session)  # 403 without permission
    _limit(user, "bq-export")
    _bq_ready(bq)
    today = datetime.now(timezone.utc).date()
    day = payload.aggregate_date or today
    if day > today + timedelta(days=1):
        raise AppException("Invalid Date", "aggregate_date cannot be in the future.", 422, "INVALID_DATE")
    result = await collect_facility_aggregates(session, day, jurisdiction)
    try:
        await bq.ensure_table()
        count = await bq.insert_rows(result.rows)
    except GoogleError as exc:
        raise to_app_exception(exc, "BigQuery")
    return DataResponse(data=BigQueryExportResponse(
        aggregate_date=day, scope=jurisdiction.label, rows_exported=count,
        beds_included=result.beds_included, columns=EXPORT_COLUMN_NAMES))


@router.get("/bigquery/national-summary", response_model=DataResponse[NationalSummaryResponse])
async def bigquery_national_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    bq: BigQueryClientProtocol = Depends(get_bigquery_client),
):
    jurisdiction = await resolve_jurisdiction(user, SUMMARY_PERMISSION, session)
    _limit(user, "bq-summary")
    _bq_ready(bq)
    end = date_to or datetime.now(timezone.utc).date()
    start = date_from or end - timedelta(days=30)
    if start > end or (end - start).days > 366:
        raise AppException("Invalid Range", "date_from must be on or before date_to, within 366 days.", 422,
                           "INVALID_DATE_RANGE")
    # Scope comes from the caller's facility, never from client input.
    state = None if jurisdiction.scope == ScopeLevel.GLOBAL else jurisdiction.state
    district = jurisdiction.district if jurisdiction.scope not in (ScopeLevel.GLOBAL, ScopeLevel.STATE) else None
    try:
        rows = await bq.query_national_summary(start, end, state, district)
    except GoogleError as exc:
        raise to_app_exception(exc, "BigQuery")
    return DataResponse(data=NationalSummaryResponse(
        date_from=start, date_to=end, scope=jurisdiction.label, rows=[NationalSummaryRow(**r) for r in rows]))
