"""Real-time bed and staff-attendance capacity roll-ups.

Rules: only recorded values are summed. A facility with no bed rows is NO_DATA (its beds are
never counted as zero capacity), one whose latest bed update is older than 24h is STALE, and
staff-present figures are only reported for facilities with attendance recorded in the last 24h.
"""
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jurisdiction import Jurisdiction
from app.models.beds import BedInventory
from app.models.facility import Facility
from app.models.healthcare import Patient, StaffAttendance
from app.models.identity import User
from app.services.health_aggregation_service import PRESENT_STATES, HealthAggregationService

STALE_AFTER = timedelta(hours=24)
FLAGGED_LIMIT = 200


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def freshness(ts: Optional[datetime], now: datetime) -> str:
    ts = _aware(ts)
    if ts is None:
        return "NO_DATA"
    return "STALE" if now - ts > STALE_AFTER else "FRESH"


def bed_status_for(rows: List[BedInventory], now: datetime) -> tuple:
    """(status, latest_update) for one facility's bed rows."""
    if not rows:
        return "NO_DATA", None
    latest = max(_aware(r.updated_at) for r in rows)
    return freshness(latest, now), latest


class CapacityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def facility_beds(self, facility_id: uuid.UUID, now: Optional[datetime] = None) -> dict:
        now = now or datetime.now(timezone.utc)
        rows = list((await self.session.execute(
            select(BedInventory).where(BedInventory.facility_id == facility_id).order_by(BedInventory.ward_type)
        )).scalars().all())
        status, latest = bed_status_for(rows, now)
        out = {"facility_id": facility_id, "as_of": now, "status": status, "last_updated_at": latest,
               "total_beds": None, "occupied_beds": None, "available_beds": None, "wards": rows}
        if rows:
            out["total_beds"] = sum(r.total_beds for r in rows)
            out["occupied_beds"] = sum(r.occupied_beds for r in rows)
            out["available_beds"] = out["total_beds"] - out["occupied_beds"]
        return out

    async def _facility_rows(self, facilities: List[Facility], now: datetime) -> List[dict]:
        ids = [f.id for f in facilities]
        if not ids:
            return []
        today = now.date()
        beds: Dict[uuid.UUID, List[BedInventory]] = defaultdict(list)
        for r in (await self.session.execute(select(BedInventory).where(BedInventory.facility_id.in_(ids)))).scalars():
            beds[r.facility_id].append(r)

        patient_user_ids = select(Patient.user_id).where(Patient.user_id.is_not(None))
        assigned = dict((await self.session.execute(
            select(User.facility_id, func.count(User.id))
            .where(User.facility_id.in_(ids), User.is_active.is_(True), User.id.not_in(patient_user_ids))
            .group_by(User.facility_id)
        )).all())
        present = dict((await self.session.execute(
            select(StaffAttendance.facility_id, func.count(func.distinct(StaffAttendance.user_id)))
            .where(StaffAttendance.facility_id.in_(ids), StaffAttendance.attendance_date == today,
                   StaffAttendance.status.in_(PRESENT_STATES))
            .group_by(StaffAttendance.facility_id)
        )).all())
        last_att = dict((await self.session.execute(
            select(StaffAttendance.facility_id, func.max(StaffAttendance.check_in_time))
            .where(StaffAttendance.facility_id.in_(ids)).group_by(StaffAttendance.facility_id)
        )).all())

        out = []
        for f in facilities:
            frows = beds.get(f.id, [])
            b_status, b_latest = bed_status_for(frows, now)
            total = sum(r.total_beds for r in frows) if frows else None
            occ = sum(r.occupied_beds for r in frows) if frows else None
            a_latest = _aware(last_att.get(f.id))
            a_status = freshness(a_latest, now)
            out.append({
                "facility_id": f.id, "facility_name": f.name, "facility_code": f.code,
                "facility_type": f.facility_type.value, "state": f.state, "district": f.district,
                "beds": {
                    "status": b_status, "last_updated_at": b_latest, "total": total, "occupied": occ,
                    "available": None if total is None else total - occ,
                    "wards": {r.ward_type.value: {"total": r.total_beds, "occupied": r.occupied_beds,
                                                  "available": r.total_beds - r.occupied_beds}
                              for r in frows},
                },
                "staff": {
                    "status": a_status, "last_attendance_at": a_latest,
                    "assigned": assigned.get(f.id, 0),
                    # only reported when attendance was recorded in the last 24h; otherwise unknown, not 0
                    "present_today": present.get(f.id, 0) if a_status == "FRESH" else None,
                },
            })
        return out

    @staticmethod
    def _aggregate(rows: List[dict]) -> dict:
        beds_reported = [r for r in rows if r["beds"]["total"] is not None]
        beds_fresh = [r for r in beds_reported if r["beds"]["status"] == "FRESH"]
        tot = sum(r["beds"]["total"] for r in beds_reported)
        occ = sum(r["beds"]["occupied"] for r in beds_reported)
        ftot = sum(r["beds"]["total"] for r in beds_fresh)
        focc = sum(r["beds"]["occupied"] for r in beds_fresh)
        by_ward: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "occupied": 0, "available": 0})
        for r in beds_reported:
            for w, v in r["beds"]["wards"].items():
                for k in ("total", "occupied", "available"):
                    by_ward[w][k] += v[k]
        staff_fresh = [r for r in rows if r["staff"]["status"] == "FRESH"]
        assigned_fresh = sum(r["staff"]["assigned"] for r in staff_fresh)
        present_fresh = sum(r["staff"]["present_today"] or 0 for r in staff_fresh)
        return {
            "facilities": len(rows),
            "beds": {
                "total": tot, "occupied": occ, "available": tot - occ,
                "occupancy_pct": round(100 * occ / tot, 1) if tot else None,
                "fresh_total": ftot, "fresh_occupied": focc, "fresh_available": ftot - focc,
                "by_ward": dict(by_ward),
                "facilities_fresh": len(beds_fresh),
                "facilities_stale": sum(1 for r in beds_reported if r["beds"]["status"] == "STALE"),
                "facilities_no_data": sum(1 for r in rows if r["beds"]["status"] == "NO_DATA"),
            },
            "staff": {
                "assigned_total": sum(r["staff"]["assigned"] for r in rows),
                "assigned_in_reporting_facilities": assigned_fresh,
                "present_today": present_fresh,
                "availability_pct": round(100 * present_fresh / assigned_fresh, 1) if assigned_fresh else None,
                "facilities_attendance_fresh": len(staff_fresh),
                "facilities_attendance_stale": sum(1 for r in rows if r["staff"]["status"] == "STALE"),
                "facilities_attendance_no_data": sum(1 for r in rows if r["staff"]["status"] == "NO_DATA"),
            },
        }

    async def rollup(self, j: Jurisdiction, group_by: str, now: Optional[datetime] = None) -> dict:
        """group_by: 'facility' (district view), 'district' (state view) or 'state' (national view)."""
        now = now or datetime.now(timezone.utc)
        facilities = await HealthAggregationService(self.session).facilities(j)
        rows = await self._facility_rows(facilities, now)
        result = {"scope": j.label, "as_of": now, "stale_after_hours": 24, **self._aggregate(rows)}

        flagged = [
            {"facility_id": r["facility_id"], "facility_name": r["facility_name"], "state": r["state"],
             "district": r["district"], "beds_status": r["beds"]["status"],
             "beds_last_updated_at": r["beds"]["last_updated_at"],
             "attendance_status": r["staff"]["status"], "last_attendance_at": r["staff"]["last_attendance_at"]}
            for r in rows if r["beds"]["status"] != "FRESH" or r["staff"]["status"] != "FRESH"
        ]
        result["flagged_facilities_count"] = len(flagged)
        result["flagged_facilities"] = flagged[:FLAGGED_LIMIT]
        result["flagged_truncated"] = len(flagged) > FLAGGED_LIMIT

        if group_by == "facility":
            result["breakdown"] = rows
        else:
            groups: Dict[tuple, List[dict]] = defaultdict(list)
            for r in rows:
                groups[(r["state"],) if group_by == "state" else (r["state"], r["district"])].append(r)
            breakdown = []
            for key, grp in sorted(groups.items()):
                item = {"state": key[0], **self._aggregate(grp)}
                if group_by == "district":
                    item["district"] = key[1]
                breakdown.append(item)
            result["breakdown"] = breakdown
        return result
