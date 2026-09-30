"""BigQuery (REST) export of anonymised, facility-level daily aggregates and a state-level rollup readback.

Privacy: rows contain only facility identifiers, geography, a date and counts. No patient, staff or user identifiers
ever leave the system (see EXPORT_COLUMNS, asserted by tests). Auth is a service-account Bearer token
(app.integrations.google.auth); the dataset/table are created on demand.
"""
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol, Sequence

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jurisdiction import Jurisdiction
from app.integrations.google.auth import BIGQUERY_SCOPE, get_access_token
from app.integrations.google.errors import GoogleError, GoogleRejected, NotConfigured
from app.integrations.google.http import request_json

logger = logging.getLogger("app.integrations.google.bigquery")

# (name, BigQuery type, description). This is the complete, reviewed list of what leaves the system.
EXPORT_COLUMNS: List[tuple] = [
    ("facility_id", "STRING", "Facility UUID (not a person)"),
    ("state", "STRING", "Facility state"),
    ("district", "STRING", "Facility district"),
    ("aggregate_date", "DATE", "Day the counts describe"),
    ("appointments", "INTEGER", "Appointments scheduled that day"),
    ("stockouts", "INTEGER", "Stockout/shortage incidents reported that day"),
    ("staff_present", "INTEGER", "Staff with attendance PRESENT/HALF_DAY/ON_DUTY_CAMP that day"),
    ("staff_assigned", "INTEGER", "Active staff assigned to the facility"),
    ("beds_total", "INTEGER", "Total beds (latest inventory); null if bed tracking unavailable"),
    ("beds_occupied", "INTEGER", "Occupied beds (latest inventory); null if bed tracking unavailable"),
    ("exported_at", "TIMESTAMP", "Export time (UTC)"),
]
EXPORT_COLUMN_NAMES = [c[0] for c in EXPORT_COLUMNS]

_IDENT = re.compile(r"^[A-Za-z0-9_]{1,128}$")


class BigQueryClientProtocol(Protocol):
    def is_configured(self) -> bool: ...

    async def ensure_table(self) -> None: ...

    async def insert_rows(self, rows: Sequence[Dict[str, Any]]) -> int: ...

    async def query_national_summary(self, date_from: date, date_to: date, state: Optional[str],
                                     district: Optional[str]) -> List[Dict[str, Any]]: ...


class BigQueryClient:
    def __init__(self, project: Optional[str] = None, dataset: Optional[str] = None, table: Optional[str] = None,
                 base: Optional[str] = None, location: Optional[str] = None, timeout: Optional[float] = None,
                 transport: Optional[httpx.AsyncBaseTransport] = None):
        self.project = settings.GOOGLE_CLOUD_PROJECT if project is None else project
        self.dataset = settings.BIGQUERY_DATASET if dataset is None else dataset
        self.table = settings.BIGQUERY_TABLE if table is None else table
        self.base = (base or settings.GOOGLE_BIGQUERY_API_BASE).rstrip("/")
        self.location = location or settings.BIGQUERY_LOCATION
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self._transport = transport

    def is_configured(self) -> bool:
        from app.integrations.google.auth import is_configured as creds_ok
        return bool(self.project and self.dataset) and creds_ok()

    def _require(self) -> None:
        if not (self.project and self.dataset):
            raise NotConfigured("GOOGLE_CLOUD_PROJECT / BIGQUERY_DATASET is not set")
        if not (_IDENT.match(self.dataset) and _IDENT.match(self.table)):
            raise NotConfigured("BIGQUERY_DATASET / BIGQUERY_TABLE contain invalid characters")
        if not re.match(r"^[A-Za-z0-9._:-]{1,128}$", self.project):
            raise NotConfigured("GOOGLE_CLOUD_PROJECT contains invalid characters")

    async def _call(self, method: str, path: str, body: Any = None) -> Any:
        self._require()
        token = await get_access_token([BIGQUERY_SCOPE])
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return await request_json(method, f"{self.base}/projects/{self.project}{path}", headers=headers,
                                  json_body=body, timeout=self.timeout, transport=self._transport)

    async def ensure_table(self) -> None:
        ds_path = f"/datasets/{self.dataset}"
        try:
            await self._call("GET", ds_path)
        except GoogleRejected as exc:
            if exc.http_status != 404:
                raise
            await self._call("POST", "/datasets", {
                "datasetReference": {"projectId": self.project, "datasetId": self.dataset},
                "location": self.location,
                "description": "PHC Connect anonymised facility aggregates (no patient data)",
            })
        try:
            await self._call("GET", f"{ds_path}/tables/{self.table}")
        except GoogleRejected as exc:
            if exc.http_status != 404:
                raise
            await self._call("POST", f"{ds_path}/tables", {
                "tableReference": {"projectId": self.project, "datasetId": self.dataset, "tableId": self.table},
                "schema": {"fields": [{"name": n, "type": t, "mode": "NULLABLE", "description": d}
                                      for n, t, d in EXPORT_COLUMNS]},
                "timePartitioning": {"type": "DAY", "field": "aggregate_date"},
            })

    async def insert_rows(self, rows: Sequence[Dict[str, Any]]) -> int:
        """Streaming insert (tabledata.insertAll). insertId makes re-exporting the same day idempotent (best effort)."""
        if not rows:
            return 0
        for r in rows:
            if set(r) - set(EXPORT_COLUMN_NAMES):
                raise GoogleError("row contains columns outside the approved export schema")
        body = {"kind": "bigquery#tableDataInsertAllRequest", "skipInvalidRows": False,
                "ignoreUnknownValues": False,
                "rows": [{"insertId": f"{r['facility_id']}:{r['aggregate_date']}", "json": dict(r)} for r in rows]}
        data = await self._call("POST", f"/datasets/{self.dataset}/tables/{self.table}/insertAll", body)
        if isinstance(data, dict) and data.get("insertErrors"):
            logger.error("BigQuery insertAll reported %d row errors", len(data["insertErrors"]))
            raise GoogleError(f"insertAll rejected {len(data['insertErrors'])} rows")
        return len(rows)

    async def query_national_summary(self, date_from: date, date_to: date, state: Optional[str],
                                     district: Optional[str]) -> List[Dict[str, Any]]:
        self._require()
        t = f"`{self.project}.{self.dataset}.{self.table}`"
        params = [_param("date_from", "DATE", date_from.isoformat()), _param("date_to", "DATE", date_to.isoformat())]
        where = "aggregate_date BETWEEN @date_from AND @date_to"
        if state:
            where += " AND LOWER(state) = LOWER(@state)"
            params.append(_param("state", "STRING", state))
        if district:
            where += " AND LOWER(district) = LOWER(@district)"
            params.append(_param("district", "STRING", district))
        sql = (
            "SELECT state, COUNT(DISTINCT facility_id) AS facilities, SUM(appointments) AS appointments, "
            "SUM(stockouts) AS stockouts, SUM(staff_present) AS staff_present_days, "
            "SUM(staff_assigned) AS staff_assigned_days, SUM(beds_total) AS beds_total_days, "
            f"SUM(beds_occupied) AS beds_occupied_days FROM {t} WHERE {where} GROUP BY state ORDER BY state"
        )
        body = {"query": sql, "useLegacySql": False, "parameterMode": "NAMED", "queryParameters": params,
                "location": self.location, "maxResults": 1000, "timeoutMs": int(self.timeout * 1000)}
        data = await self._call("POST", "/queries", body)
        if not isinstance(data, dict) or "jobComplete" in data and not data["jobComplete"]:
            raise GoogleError("query did not complete in time")
        fields = [f["name"] for f in (data.get("schema") or {}).get("fields", [])]
        out = []
        for row in data.get("rows") or []:
            vals = [c.get("v") for c in row.get("f", [])]
            rec = dict(zip(fields, vals))
            out.append({k: (v if k == "state" or v is None else int(v)) for k, v in rec.items()})
        return out


def _param(name: str, typ: str, value: str) -> Dict[str, Any]:
    return {"name": name, "parameterType": {"type": typ}, "parameterValue": {"value": value}}


def get_bigquery_client() -> BigQueryClientProtocol:
    """Dependency seam: tests replace this."""
    return BigQueryClient()


# --------------------------------------------------------------------------- aggregate collection
@dataclass
class CollectResult:
    rows: List[Dict[str, Any]]
    beds_included: bool


async def collect_facility_aggregates(session: AsyncSession, day: date, jurisdiction: Jurisdiction) -> CollectResult:
    """Build anonymised rows for every active facility inside `jurisdiction` for `day`."""
    from app.models.facility import Facility
    from app.models.healthcare import Appointment, AttendanceStatus, StaffAttendance
    from app.models.identity import User
    from app.models.pharmacy import ShortageIncident

    fq = jurisdiction.filter(select(Facility).where(Facility.is_active.is_(True)), Facility.state, Facility.district)
    facilities = list((await session.execute(fq)).scalars().all())
    if not facilities:
        return CollectResult([], False)
    ids = [f.id for f in facilities]
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    async def counts(stmt) -> Dict[Any, int]:
        return {k: int(v) for k, v in (await session.execute(stmt)).all()}

    appts = await counts(select(Appointment.facility_id, func.count()).where(
        Appointment.facility_id.in_(ids), Appointment.appointment_date >= start, Appointment.appointment_date < end,
    ).group_by(Appointment.facility_id))
    stock = await counts(select(ShortageIncident.facility_id, func.count()).where(
        ShortageIncident.facility_id.in_(ids), ShortageIncident.created_at >= start, ShortageIncident.created_at < end,
    ).group_by(ShortageIncident.facility_id))
    present = await counts(select(StaffAttendance.facility_id, func.count(func.distinct(StaffAttendance.user_id))).where(
        StaffAttendance.facility_id.in_(ids), StaffAttendance.attendance_date == day,
        StaffAttendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY, AttendanceStatus.ON_DUTY_CAMP]),
    ).group_by(StaffAttendance.facility_id))
    assigned = await counts(select(User.facility_id, func.count()).where(
        User.facility_id.in_(ids), User.is_active.is_(True)).group_by(User.facility_id))

    beds: Dict[Any, tuple] = {}
    beds_included = False
    try:
        from app.models.beds import BedInventory  # bed tracking may not exist in every deployment
        beds_included = True
        for fid, total, occ in (await session.execute(
            select(BedInventory.facility_id, func.sum(BedInventory.total_beds), func.sum(BedInventory.occupied_beds))
            .where(BedInventory.facility_id.in_(ids)).group_by(BedInventory.facility_id)
        )).all():
            beds[fid] = (int(total or 0), int(occ or 0))
    except ImportError:
        beds_included = False

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for f in facilities:
        b = beds.get(f.id)
        rows.append({
            "facility_id": str(f.id), "state": f.state.strip(), "district": f.district.strip(),
            "aggregate_date": day.isoformat(), "appointments": appts.get(f.id, 0), "stockouts": stock.get(f.id, 0),
            "staff_present": present.get(f.id, 0), "staff_assigned": assigned.get(f.id, 0),
            "beds_total": b[0] if b else None, "beds_occupied": b[1] if b else None, "exported_at": now,
        })
    return CollectResult(rows, beds_included)
