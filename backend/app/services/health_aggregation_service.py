"""Aggregates live PHC operational data for district / state / national oversight.

Every figure is computed from existing operational tables (appointments,
consultations, referrals, attendance, inventory, alerts, emergencies). Nothing
is estimated here; when a PHC has no data the snapshot says so explicitly.
Outputs are aggregate counts only — no patient identifiers leave this service.
"""
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.core.jurisdiction import Jurisdiction
from app.models.emergency import EmergencyAffectedFacility, EmergencyIncident, EmergencyStatus
from app.models.facility import Facility
from app.models.healthcare import (
    Appointment,
    AttendanceStatus,
    ColdChainEquipment,
    ComplaintStatus,
    Consultation,
    FeedbackComplaint,
    Patient,
    Referral,
    StaffAttendance,
)
from app.models.identity import User
from app.models.intelligence import Alert
from app.models.pharmacy import InventoryItem, ShortageIncident, ShortageStatus

ACTIVE_EMERGENCY_STATES = [
    EmergencyStatus.PENDING,
    EmergencyStatus.ACKNOWLEDGED,
    EmergencyStatus.RESPONSE_STARTED,
    EmergencyStatus.IN_PROGRESS,
    EmergencyStatus.ESCALATED,
]
OPEN_SHORTAGE_STATES = [
    ShortageStatus.REPORTED,
    ShortageStatus.INVESTIGATING,
    ShortageStatus.ESCALATED_DISTRICT,
    ShortageStatus.ESCALATED_STATE,
    ShortageStatus.ACTION_TAKEN,
]
PRESENT_STATES = [AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY, AttendanceStatus.ON_DUTY_CAMP]
OPEN_COMPLAINT_STATES = [ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW]


def day_bounds(start: date, end: date):
    return (
        datetime.combine(start, time.min, tzinfo=timezone.utc),
        datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc),
    )


def _key(v) -> str:
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


class HealthAggregationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def facilities(self, j: Jurisdiction, active_only: bool = True) -> List[Facility]:
        stmt = select(Facility)
        if active_only:
            stmt = stmt.where(Facility.is_active.is_(True))
        if j.is_facility_bound:
            stmt = stmt.where(Facility.id == j.facility_id)
        else:
            stmt = j.filter(stmt, Facility.state, Facility.district)
        return list((await self.session.execute(stmt.order_by(Facility.state, Facility.district, Facility.name))).scalars().all())

    async def _count_by_facility(self, column, *where) -> Dict[uuid.UUID, int]:
        rows = (await self.session.execute(select(column, func.count()).where(*where).group_by(column))).all()
        return {fid: n for fid, n in rows if fid is not None}

    async def facility_snapshots(self, facilities: List[Facility], start: date, end: date) -> List[dict]:
        ids = [f.id for f in facilities]
        if not ids:
            return []
        lo, hi = day_bounds(start, end)
        today = date.today()

        appointments = await self._count_by_facility(
            Appointment.facility_id, Appointment.facility_id.in_(ids),
            Appointment.appointment_date >= lo, Appointment.appointment_date < hi,
        )
        consultations = await self._count_by_facility(
            Consultation.facility_id, Consultation.facility_id.in_(ids),
            Consultation.started_at >= lo, Consultation.started_at < hi,
        )
        referrals = await self._count_by_facility(
            Referral.from_facility_id, Referral.from_facility_id.in_(ids),
            Referral.created_at >= lo, Referral.created_at < hi,
        )
        patient_user_ids = select(Patient.user_id).where(Patient.user_id.is_not(None))
        staff_assigned = await self._count_by_facility(
            User.facility_id, User.facility_id.in_(ids), User.is_active.is_(True), User.id.not_in(patient_user_ids),
        )
        present_rows = (await self.session.execute(
            select(StaffAttendance.facility_id, func.count(func.distinct(StaffAttendance.user_id)))
            .where(StaffAttendance.facility_id.in_(ids), StaffAttendance.attendance_date == today,
                   StaffAttendance.status.in_(PRESENT_STATES))
            .group_by(StaffAttendance.facility_id)
        )).all()
        staff_present = {fid: n for fid, n in present_rows}

        available = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
        stock_rows = (await self.session.execute(
            select(
                InventoryItem.facility_id,
                func.count(InventoryItem.id),
                func.sum(case((available <= InventoryItem.reorder_level, 1), else_=0)),
                func.sum(case((available <= 0, 1), else_=0)),
            ).where(InventoryItem.facility_id.in_(ids)).group_by(InventoryItem.facility_id)
        )).all()
        stock = {fid: (tracked or 0, int(low or 0), int(out or 0)) for fid, tracked, low, out in stock_rows}

        shortages = await self._count_by_facility(
            ShortageIncident.facility_id, ShortageIncident.facility_id.in_(ids),
            ShortageIncident.status.in_(OPEN_SHORTAGE_STATES),
        )
        alerts = await self._count_by_facility(
            Alert.facility_id, Alert.facility_id.in_(ids), Alert.is_acknowledged.is_(False),
        )
        cold_chain = await self._count_by_facility(
            ColdChainEquipment.facility_id, ColdChainEquipment.facility_id.in_(ids),
            (ColdChainEquipment.is_functional.is_(False)) | (ColdChainEquipment.is_temperature_in_range.is_(False)),
        )
        complaints = await self._count_by_facility(
            FeedbackComplaint.facility_id, FeedbackComplaint.facility_id.in_(ids),
            FeedbackComplaint.status.in_(OPEN_COMPLAINT_STATES),
        )
        disruption_rows = (await self.session.execute(
            select(EmergencyAffectedFacility.facility_id, EmergencyAffectedFacility.service_disruption,
                   EmergencyIncident.reference)
            .join(EmergencyIncident, EmergencyAffectedFacility.incident_id == EmergencyIncident.id)
            .where(EmergencyAffectedFacility.facility_id.in_(ids), EmergencyIncident.status.in_(ACTIVE_EMERGENCY_STATES))
        )).all()
        disruptions: Dict[uuid.UUID, List[dict]] = defaultdict(list)
        for fid, level, ref in disruption_rows:
            disruptions[fid].append({"emergency_reference": ref, "service_disruption": level})

        snapshots = []
        for f in facilities:
            tracked, low, out = stock.get(f.id, (0, 0, 0))
            snap = {
                "facility_id": f.id,
                "facility_name": f.name,
                "facility_code": f.code,
                "facility_type": f.facility_type.value,
                "state": f.state,
                "district": f.district,
                "patient_volume": appointments.get(f.id, 0),
                "consultations": consultations.get(f.id, 0),
                "referrals": referrals.get(f.id, 0),
                "staff_assigned": staff_assigned.get(f.id, 0),
                "staff_present_today": staff_present.get(f.id, 0),
                "medicines_tracked": tracked,
                "low_stock_items": low,
                "stockout_items": out,
                "open_shortages": shortages.get(f.id, 0),
                "unacknowledged_alerts": alerts.get(f.id, 0),
                "cold_chain_issues": cold_chain.get(f.id, 0),
                "open_complaints": complaints.get(f.id, 0),
                "active_emergencies": disruptions.get(f.id, []),
            }
            snap["operational_status"], snap["status_reasons"] = self._operational_status(snap)
            snapshots.append(snap)
        return snapshots

    @staticmethod
    def _operational_status(s: dict):
        """Rule-based, explainable status. Rules are listed in the returned reasons."""
        reasons: List[str] = []
        severe = [e for e in s["active_emergencies"] if e["service_disruption"] in ("SEVERE", "CLOSED")]
        if severe:
            reasons.append(f"Service disruption from emergency {severe[0]['emergency_reference']}.")
            return "DISRUPTED", reasons
        if s["staff_assigned"] and s["staff_present_today"] == 0:
            reasons.append("No staff attendance recorded today.")
        if s["stockout_items"]:
            reasons.append(f"{s['stockout_items']} medicine(s) out of stock.")
        if s["cold_chain_issues"]:
            reasons.append(f"{s['cold_chain_issues']} cold-chain unit(s) faulty or out of range.")
        if s["open_shortages"]:
            reasons.append(f"{s['open_shortages']} open shortage incident(s).")
        if s["active_emergencies"]:
            reasons.append("Affected by an active emergency (partial/no disruption).")
        if reasons:
            return "NEEDS_ATTENTION", reasons
        if not any((s["staff_assigned"], s["medicines_tracked"], s["patient_volume"])):
            return "NO_DATA", ["No staff, inventory, or patient activity recorded for this facility yet."]
        return "OPERATIONAL", ["No attention rules triggered."]

    @staticmethod
    def totals(snapshots: List[dict]) -> dict:
        keys = ("patient_volume", "consultations", "referrals", "staff_assigned", "staff_present_today",
                "low_stock_items", "stockout_items", "open_shortages", "unacknowledged_alerts",
                "cold_chain_issues", "open_complaints")
        out = {k: sum(s[k] for s in snapshots) for k in keys}
        status_counts: Dict[str, int] = defaultdict(int)
        for s in snapshots:
            status_counts[s["operational_status"]] += 1
        out["facilities"] = len(snapshots)
        out["facilities_by_status"] = dict(status_counts)
        out["staff_availability_pct"] = (
            round(100 * out["staff_present_today"] / out["staff_assigned"], 1) if out["staff_assigned"] else None
        )
        return out

    async def daily_series(self, facility_ids: Iterable[uuid.UUID], start: date, end: date) -> List[dict]:
        ids = list(facility_ids)
        lo, hi = day_bounds(start, end)
        series = {(start + timedelta(days=i)).isoformat(): {"appointments": 0, "consultations": 0, "referrals": 0}
                  for i in range((end - start).days + 1)}
        if not ids:
            return [{"date": d, **v} for d, v in series.items()]
        for label, col, fcol in (
            ("appointments", Appointment.appointment_date, Appointment.facility_id),
            ("consultations", Consultation.started_at, Consultation.facility_id),
            ("referrals", Referral.created_at, Referral.from_facility_id),
        ):
            day = func.date(col)
            rows = (await self.session.execute(
                select(day, func.count()).where(fcol.in_(ids), col >= lo, col < hi).group_by(day)
            )).all()
            for d, n in rows:
                k = _key(d)[:10]
                if k in series:
                    series[k][label] = n
        return [{"date": d, **v} for d, v in series.items()]

    async def group_by_region(self, snapshots: List[dict], key: str) -> List[dict]:
        """Roll facility snapshots up to district (key='district') or state (key='state')."""
        groups: Dict[tuple, List[dict]] = defaultdict(list)
        for s in snapshots:
            region = (s["state"], s["district"]) if key == "district" else (s["state"],)
            groups[region].append(s)
        out = []
        for region, snaps in sorted(groups.items()):
            t = self.totals(snaps)
            row = {"state": region[0], **t}
            if key == "district":
                row["district"] = region[1]
            out.append(row)
        return out

    async def active_emergency_count(self, j: Jurisdiction) -> int:
        stmt = select(func.count(EmergencyIncident.id)).where(EmergencyIncident.status.in_(ACTIVE_EMERGENCY_STATES))
        stmt = j.filter(stmt, EmergencyIncident.state, EmergencyIncident.district)
        return (await self.session.execute(stmt)).scalar_one() or 0


def period(start: Optional[date], end: Optional[date], default_days: int = 7):
    end = end or date.today()
    start = start or end - timedelta(days=default_days - 1)
    if start > end:
        raise BadRequestException("start_date must be on or before end_date.")
    if (end - start).days > 366:
        raise BadRequestException("Date range cannot exceed 366 days.")
    return start, end
