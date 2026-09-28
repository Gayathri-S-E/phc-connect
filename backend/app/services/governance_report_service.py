"""Report generation / review and scheme-target monitoring for district, state and national roles.

A generated report is an immutable snapshot of live aggregates at generation
time, labelled with its reporting period, data sources and generation time.
Reports travel upward (district → state → national) through submit/review.
"""
import csv
import io
import uuid
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.models.emergency import EmergencyIncident
from app.models.facility import Facility
from app.models.governance import (
    GovernanceAlert,
    GovernanceLevel,
    GovernanceReport,
    HealthScheme,
    ReportReviewStatus,
    SchemeTarget,
)
from app.models.healthcare import Medication
from app.models.identity import ScopeLevel
from app.models.pharmacy import ShortageIncident
from app.models.public_health import DataQualityIssue, HealthIndicatorAggregate, PublicHealthIndicator
from app.models.supply_chain import SupplyHealthImpact
from app.schemas.governance import (
    ReportGenerate,
    ReportReview,
    SchemeCreate,
    SchemeProgressReport,
    SchemeRemark,
    SchemeTargetSet,
)
from app.services.common import NEXT_LEVEL, AuditCtx, AuditMixin, level_for, make_reference, paginate, utcnow
from app.services.health_aggregation_service import HealthAggregationService, day_bounds, period

ANY = None
REPORT_TYPES: Dict[str, Tuple[str, Optional[GovernanceLevel]]] = {
    "DISTRICT_DAILY_SUMMARY": ("Daily District Health Summary", GovernanceLevel.DISTRICT),
    "PHC_PERFORMANCE": ("PHC Performance Summary", GovernanceLevel.DISTRICT),
    "SERVICE_UTILISATION": ("Patient Service Utilisation Report", ANY),
    "STAFF_AVAILABILITY": ("Staff Availability Report", ANY),
    "PHC_OPERATIONAL_STATUS": ("PHC Operational Status Report", ANY),
    "HEALTH_ALERTS": ("Health Alert Report", ANY),
    "SHORTAGE_IMPACT": ("Resource / Shortage Impact Summary", ANY),
    "EMERGENCY_IMPACT": ("Emergency Health Impact Summary", ANY),
    "STATE_OVERVIEW": ("State Health Overview Report", GovernanceLevel.STATE),
    "DISTRICT_COMPARISON": ("District Comparison Report", GovernanceLevel.STATE),
    "SCHEME_PROGRESS": ("Scheme & Target Progress Report", GovernanceLevel.STATE),
    "DATA_QUALITY": ("Reporting Completeness & Data Quality Report", GovernanceLevel.STATE),
    "PUBLIC_HEALTH_TRENDS": ("Public Health Indicator Trend Report", GovernanceLevel.STATE),
    "NATIONAL_OVERVIEW": ("National Health Overview", GovernanceLevel.NATIONAL),
    "STATE_COMPARISON": ("State Comparison Report", GovernanceLevel.NATIONAL),
}


def _in_period(col, start: date, end: date):
    lo, hi = day_bounds(start, end)
    return (col >= lo) & (col < hi)


class GovernanceReportService(AuditMixin):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.agg = HealthAggregationService(session)

    @staticmethod
    def report_types(level: GovernanceLevel) -> List[dict]:
        return [{"code": code, "name": name, "level": (lvl or level).value}
                for code, (name, lvl) in REPORT_TYPES.items() if lvl in (None, level)]

    # ------------------------------------------------------------------ generation
    def _narrow(self, j: Jurisdiction, target_state: Optional[str], target_district: Optional[str]) -> Jurisdiction:
        if target_district:
            state = target_state or j.state
            j.ensure_covers(state, target_district)
            return Jurisdiction(ScopeLevel.DISTRICT, state, target_district, None)
        if target_state:
            j.ensure_covers(target_state)
            if j.scope in (ScopeLevel.GLOBAL, ScopeLevel.STATE):
                return Jurisdiction(ScopeLevel.STATE, target_state, None, None)
        return j

    async def generate(self, data: ReportGenerate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> GovernanceReport:
        if data.report_type not in REPORT_TYPES:
            raise BadRequestException(f"Unknown report_type '{data.report_type}'.")
        scope = self._narrow(j, data.target_state, data.target_district)
        level = level_for(scope)
        name, required_level = REPORT_TYPES[data.report_type]
        if required_level and required_level != level:
            raise BadRequestException(f"{name} is a {required_level.value}-level report; your scope is {level.value}.")
        default_days = 1 if data.report_type == "DISTRICT_DAILY_SUMMARY" else 30
        start, end = period(data.period_start, data.period_end, default_days)
        content = await self._build(data.report_type, scope, start, end)
        content.update({
            "title": name, "report_type": data.report_type, "jurisdiction": scope.label,
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "generated_at": utcnow().isoformat(),
        })
        report = GovernanceReport(
            reference=make_reference("RPT"), level=level, report_type=data.report_type, title=name,
            state=scope.state or "ALL", district=scope.district if scope.scope == ScopeLevel.DISTRICT else None,
            facility_id=data.facility_id, period_start=start, period_end=end, content=content,
            generated_by=actor_id, review_status=ReportReviewStatus.DRAFT,
        )
        self.session.add(report)
        await self.session.flush()
        await self._audit("GOVERNANCE_REPORT_GENERATED", "governance_report", report.id, actor_id, ctx,
                          new_state={"reference": report.reference, "type": data.report_type, "scope": scope.label})
        return report

    async def _build(self, rtype: str, j: Jurisdiction, start: date, end: date) -> dict:
        facilities = await self.agg.facilities(j)
        base = {"data_classification": "ACTUAL_REPORTED", "notes": []}
        if rtype in ("DISTRICT_DAILY_SUMMARY", "PHC_PERFORMANCE", "SERVICE_UTILISATION", "STAFF_AVAILABILITY",
                     "PHC_OPERATIONAL_STATUS", "STATE_OVERVIEW", "DISTRICT_COMPARISON", "NATIONAL_OVERVIEW",
                     "STATE_COMPARISON"):
            snaps = await self.agg.facility_snapshots(facilities, start, end)
            base["source"] = "appointments, consultations, referrals, staff_attendance, inventory_items, shortage_incidents, alerts"
            base["summary"] = self.agg.totals(snaps)
            if rtype in ("DISTRICT_COMPARISON", "STATE_OVERVIEW"):
                rows = await self.agg.group_by_region(snaps, "district")
                cols = ["state", "district", "facilities", "patient_volume", "consultations", "referrals",
                        "staff_availability_pct", "stockout_items", "open_shortages"]
            elif rtype in ("STATE_COMPARISON", "NATIONAL_OVERVIEW"):
                rows = await self.agg.group_by_region(snaps, "state")
                cols = ["state", "facilities", "patient_volume", "consultations", "referrals",
                        "staff_availability_pct", "stockout_items", "open_shortages"]
            else:
                cols = {
                    "SERVICE_UTILISATION": ["facility_name", "district", "patient_volume", "consultations", "referrals"],
                    "STAFF_AVAILABILITY": ["facility_name", "district", "staff_assigned", "staff_present_today"],
                    "PHC_OPERATIONAL_STATUS": ["facility_name", "district", "operational_status", "status_reasons"],
                }.get(rtype, ["facility_name", "district", "operational_status", "patient_volume", "consultations",
                              "referrals", "staff_present_today", "staff_assigned", "stockout_items", "open_shortages",
                              "unacknowledged_alerts"])
                rows = snaps
            if rtype == "STAFF_AVAILABILITY":
                base["notes"].append("Staff presence reflects today's attendance records, not the whole period.")
            base["columns"] = cols
            base["rows"] = [{c: (", ".join(r[c]) if isinstance(r.get(c), list) else r.get(c)) for c in cols} for r in rows]
            if not snaps:
                base["notes"].append("No active facilities in this jurisdiction.")
            return base

        if rtype == "HEALTH_ALERTS":
            stmt = j.filter(select(GovernanceAlert).where(_in_period(GovernanceAlert.created_at, start, end)),
                            GovernanceAlert.state, GovernanceAlert.district if j.scope != ScopeLevel.STATE else None)
            alerts = (await self.session.execute(stmt.order_by(GovernanceAlert.created_at.desc()))).scalars().all()
            base["source"] = "governance_alerts"
            base["columns"] = ["reference", "district", "category", "severity", "status", "origin", "title"]
            base["rows"] = [{"reference": a.reference, "district": a.district, "category": a.category,
                             "severity": a.severity.value if a.severity else "UNASSIGNED", "status": a.status.value,
                             "origin": a.origin.value, "title": a.title} for a in alerts]
            base["summary"] = {"total": len(alerts), "by_status": _count(a.status.value for a in alerts),
                               "by_category": _count(a.category for a in alerts)}
            return base

        if rtype == "SHORTAGE_IMPACT":
            ids = [f.id for f in facilities]
            names = {f.id: (f.name, f.district) for f in facilities}
            rows = (await self.session.execute(
                select(ShortageIncident, Medication.name)
                .join(Medication, ShortageIncident.medication_id == Medication.id)
                .where(ShortageIncident.facility_id.in_(ids), _in_period(ShortageIncident.created_at, start, end))
            )).all() if ids else []
            impacts_stmt = j.filter(select(SupplyHealthImpact).where(_in_period(SupplyHealthImpact.created_at, start, end)),
                                    SupplyHealthImpact.state, SupplyHealthImpact.district if j.scope != ScopeLevel.STATE else None)
            impacts = (await self.session.execute(impacts_stmt)).scalars().all()
            base["source"] = "shortage_incidents, supply_health_impacts"
            base["columns"] = ["incident_number", "facility", "district", "medicine", "severity", "status",
                               "estimated_impact_patients"]
            base["rows"] = [{"incident_number": s.incident_number, "facility": names[s.facility_id][0],
                             "district": names[s.facility_id][1], "medicine": med, "severity": s.severity.value,
                             "status": s.status.value, "estimated_impact_patients": s.estimated_impact_patients}
                            for s, med in rows]
            base["summary"] = {"shortage_incidents": len(rows), "by_severity": _count(s.severity.value for s, _ in rows),
                               "impact_notices_shared_with_dho": len(impacts)}
            return base

        if rtype == "EMERGENCY_IMPACT":
            stmt = j.filter(select(EmergencyIncident).options(selectinload(EmergencyIncident.affected_facilities),
                                                              selectinload(EmergencyIncident.tasks),
                                                              selectinload(EmergencyIncident.escalations))
                            .where(_in_period(EmergencyIncident.started_at, start, end)),
                            EmergencyIncident.state, EmergencyIncident.district if j.scope != ScopeLevel.STATE else None)
            incidents = (await self.session.execute(stmt)).scalars().all()
            base["source"] = "emergency_incidents, emergency_tasks, emergency_escalations"
            base["columns"] = ["reference", "district", "emergency_type", "priority", "status", "affected_facilities",
                               "open_tasks", "escalations"]
            base["rows"] = [{"reference": e.reference, "district": e.district, "emergency_type": e.emergency_type.value,
                             "priority": e.priority.value, "status": e.status.value,
                             "affected_facilities": len(e.affected_facilities),
                             "open_tasks": sum(1 for t in e.tasks if t.status.value not in ("COMPLETED", "CANCELLED")),
                             "escalations": len(e.escalations)} for e in incidents]
            base["summary"] = {"emergencies": len(incidents), "by_status": _count(e.status.value for e in incidents)}
            return base

        if rtype == "SCHEME_PROGRESS":
            stmt = j.filter(select(SchemeTarget, HealthScheme).join(HealthScheme, SchemeTarget.scheme_id == HealthScheme.id)
                            .where(SchemeTarget.period_start <= end, SchemeTarget.period_end >= start),
                            HealthScheme.state, None)
            rows = (await self.session.execute(stmt)).all()
            base["source"] = "health_schemes, scheme_targets (values entered by authorized district users)"
            base["columns"] = ["scheme", "district", "period", "target", "reported", "progress_pct", "reporting_status"]
            base["rows"] = [{"scheme": s.name, "district": t.district, "period": f"{t.period_start}..{t.period_end}",
                             "target": float(t.target_value),
                             "reported": float(t.reported_value) if t.reported_value is not None else None,
                             **_progress(t)} for t, s in rows]
            base["summary"] = {"targets": len(rows),
                               "by_reporting_status": _count(r["reporting_status"] for r in base["rows"])}
            if not rows:
                base["notes"].append("No scheme targets are configured for this period.")
            return base

        if rtype == "DATA_QUALITY":
            stmt = j.filter(select(DataQualityIssue), DataQualityIssue.state,
                            DataQualityIssue.district if j.scope != ScopeLevel.STATE else None)
            issues = (await self.session.execute(stmt.where(_in_period(DataQualityIssue.created_at, start, end)))).scalars().all()
            base["source"] = "data_quality_issues, health_indicator_aggregates"
            base["columns"] = ["issue_type", "district", "reporting_period", "status", "description"]
            base["rows"] = [{"issue_type": i.issue_type.value, "district": i.district, "reporting_period": i.reporting_period,
                             "status": i.status.value, "description": i.description} for i in issues]
            base["summary"] = {"issues": len(issues), "by_type": _count(i.issue_type.value for i in issues)}
            return base

        if rtype == "PUBLIC_HEALTH_TRENDS":
            stmt = j.filter(
                select(PublicHealthIndicator.code, PublicHealthIndicator.name, HealthIndicatorAggregate.district,
                       func.sum(HealthIndicatorAggregate.value), func.count(HealthIndicatorAggregate.id))
                .join(PublicHealthIndicator, HealthIndicatorAggregate.indicator_id == PublicHealthIndicator.id)
                .where(HealthIndicatorAggregate.period_start >= start, HealthIndicatorAggregate.period_end <= end)
                .group_by(PublicHealthIndicator.code, PublicHealthIndicator.name, HealthIndicatorAggregate.district),
                HealthIndicatorAggregate.state, HealthIndicatorAggregate.district if j.scope != ScopeLevel.STATE else None,
            )
            rows = (await self.session.execute(stmt)).all()
            base["source"] = "health_indicator_aggregates (submitted aggregate values)"
            base["columns"] = ["indicator_code", "indicator", "district", "total_value", "submissions"]
            base["rows"] = [{"indicator_code": c, "indicator": n, "district": d, "total_value": float(v or 0),
                             "submissions": k} for c, n, d, v, k in rows]
            base["summary"] = {"indicator_rows": len(rows)}
            return base
        raise BadRequestException(f"Report type {rtype} has no builder.")

    # ------------------------------------------------------------------ listing / review
    def _visible(self, stmt, j: Jurisdiction, actor_id: uuid.UUID):
        stmt = j.filter(stmt, GovernanceReport.state, GovernanceReport.district if j.scope == ScopeLevel.DISTRICT else None)
        my_level = level_for(j)
        return stmt.where(or_(GovernanceReport.level == my_level,
                              GovernanceReport.review_status != ReportReviewStatus.DRAFT,
                              GovernanceReport.generated_by == actor_id))

    async def list_reports(self, j: Jurisdiction, actor_id: uuid.UUID, report_type: Optional[str],
                           review_status: Optional[ReportReviewStatus], level: Optional[GovernanceLevel],
                           district: Optional[str], page: int, page_size: int):
        stmt = self._visible(select(GovernanceReport), j, actor_id)
        if report_type:
            stmt = stmt.where(GovernanceReport.report_type == report_type)
        if review_status:
            stmt = stmt.where(GovernanceReport.review_status == review_status)
        if level:
            stmt = stmt.where(GovernanceReport.level == level)
        if district:
            stmt = stmt.where(GovernanceReport.district == district)
        return await paginate(self.session, stmt, GovernanceReport.created_at.desc(), page, page_size)

    async def get_report(self, report_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID) -> GovernanceReport:
        stmt = self._visible(select(GovernanceReport).where(GovernanceReport.id == report_id), j, actor_id)
        report = (await self.session.execute(stmt)).scalar_one_or_none()
        if not report:
            raise ResourceNotFoundException("GovernanceReport", str(report_id))
        return report

    async def submit(self, report_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> GovernanceReport:
        report = await self.get_report(report_id, j, actor_id)
        if report.review_status not in (ReportReviewStatus.DRAFT, ReportReviewStatus.CLARIFICATION_REQUESTED):
            raise ConflictException(f"Report is {report.review_status.value}; it cannot be submitted again.")
        if report.level != level_for(j):
            raise PermissionDeniedException("Only the owning level can submit this report.")
        nxt = NEXT_LEVEL.get(report.level)
        if nxt is None:
            raise BadRequestException("National reports are not submitted to a higher authority.")
        if report.review_status == ReportReviewStatus.CLARIFICATION_REQUESTED:
            report.version += 1
        report.review_status = ReportReviewStatus.SUBMITTED
        report.submitted_to_level = nxt
        report.submitted_at = utcnow()
        await self.session.flush()
        await self._audit("GOVERNANCE_REPORT_SUBMITTED", "governance_report", report.id, actor_id, ctx,
                          new_state={"to_level": nxt.value, "version": report.version})
        return report

    async def review(self, report_id: uuid.UUID, data: ReportReview, j: Jurisdiction, actor_id: uuid.UUID,
                     ctx: AuditCtx) -> GovernanceReport:
        report = await self.get_report(report_id, j, actor_id)
        if report.review_status not in (ReportReviewStatus.SUBMITTED, ReportReviewStatus.UNDER_REVIEW):
            raise ConflictException(f"Report is {report.review_status.value}; only submitted reports can be reviewed.")
        if report.submitted_to_level != level_for(j):
            raise PermissionDeniedException(f"This report is routed to {report.submitted_to_level.value}-level review.")
        if report.generated_by == actor_id:
            raise BadRequestException("Segregation of duties: you cannot review your own report.")
        old = report.review_status
        report.review_status = {"ACCEPT": ReportReviewStatus.ACCEPTED, "REJECT": ReportReviewStatus.REJECTED,
                                "REQUEST_CLARIFICATION": ReportReviewStatus.CLARIFICATION_REQUESTED}[data.decision]
        report.reviewed_by = actor_id
        report.reviewed_at = utcnow()
        report.review_notes = data.notes
        await self.session.flush()
        await self._audit(f"GOVERNANCE_REPORT_{data.decision}", "governance_report", report.id, actor_id, ctx,
                          old_state={"status": old.value}, new_state={"status": report.review_status.value})
        return report

    @staticmethod
    def to_csv(report: GovernanceReport) -> str:
        content = report.content or {}
        buf = io.StringIO()
        buf.write(f"# {report.title} ({report.reference})\n# Jurisdiction: {content.get('jurisdiction')}\n")
        buf.write(f"# Period: {report.period_start} to {report.period_end}\n# Generated: {content.get('generated_at')}\n")
        buf.write(f"# Source: {content.get('source')}\n# Review status: {report.review_status.value}\n")
        cols = content.get("columns") or []
        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in content.get("rows") or []:
            writer.writerow(row)
        return buf.getvalue()

    # ------------------------------------------------------------------ schemes
    async def create_scheme(self, data: SchemeCreate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> HealthScheme:
        state = data.target_state if j.scope == ScopeLevel.GLOBAL else j.state
        if not state:
            raise BadRequestException("target_state is required for national users.")
        if j.scope not in (ScopeLevel.GLOBAL, ScopeLevel.STATE):
            raise PermissionDeniedException("Schemes are configured at state level.")
        if (await self.session.execute(select(HealthScheme).where(HealthScheme.code == data.code))).scalar_one_or_none():
            raise ConflictException(f"Scheme code '{data.code}' already exists.")
        scheme = HealthScheme(code=data.code, name=data.name, state=state, description=data.description,
                              unit=data.unit, created_by=actor_id, is_active=True)
        self.session.add(scheme)
        await self.session.flush()
        await self._audit("HEALTH_SCHEME_CREATED", "health_scheme", scheme.id, actor_id, ctx,
                          new_state={"code": scheme.code, "state": state})
        return scheme

    async def list_schemes(self, j: Jurisdiction) -> List[HealthScheme]:
        stmt = j.filter(select(HealthScheme).options(selectinload(HealthScheme.targets)), HealthScheme.state, None)
        return list((await self.session.execute(stmt.order_by(HealthScheme.name))).scalars().all())

    async def get_scheme(self, scheme_id: uuid.UUID, j: Jurisdiction) -> HealthScheme:
        stmt = j.filter(select(HealthScheme).where(HealthScheme.id == scheme_id)
                        .options(selectinload(HealthScheme.targets))
                        .execution_options(populate_existing=True), HealthScheme.state, None)
        scheme = (await self.session.execute(stmt)).scalar_one_or_none()
        if not scheme:
            raise ResourceNotFoundException("HealthScheme", str(scheme_id))
        return scheme

    async def set_target(self, scheme_id: uuid.UUID, data: SchemeTargetSet, j: Jurisdiction, actor_id: uuid.UUID,
                         ctx: AuditCtx) -> SchemeTarget:
        scheme = await self.get_scheme(scheme_id, j)
        districts = (await self.session.execute(
            select(func.lower(Facility.district)).where(func.lower(Facility.state) == scheme.state.lower()).distinct()
        )).scalars().all()
        if data.district.lower() not in districts:
            raise BadRequestException(f"District '{data.district}' has no registered facilities in {scheme.state}.")
        existing = (await self.session.execute(select(SchemeTarget).where(
            SchemeTarget.scheme_id == scheme.id, func.lower(SchemeTarget.district) == data.district.lower(),
            SchemeTarget.period_start == data.period_start, SchemeTarget.period_end == data.period_end,
        ))).scalar_one_or_none()
        if existing:
            old = float(existing.target_value)
            existing.target_value = data.target_value
            target = existing
        else:
            old = None
            target = SchemeTarget(scheme_id=scheme.id, district=data.district, period_start=data.period_start,
                                  period_end=data.period_end, target_value=data.target_value)
            self.session.add(target)
        await self.session.flush()
        await self._audit("SCHEME_TARGET_SET", "scheme_target", target.id, actor_id, ctx,
                          old_state={"target_value": old} if old is not None else None,
                          new_state={"district": data.district, "target_value": data.target_value})
        return target

    async def _get_target(self, target_id: uuid.UUID, j: Jurisdiction) -> Tuple[SchemeTarget, HealthScheme]:
        row = (await self.session.execute(
            select(SchemeTarget, HealthScheme).join(HealthScheme, SchemeTarget.scheme_id == HealthScheme.id)
            .where(SchemeTarget.id == target_id)
        )).first()
        if not row or not j.covers(row[1].state, row[0].district if j.scope == ScopeLevel.DISTRICT else None):
            raise ResourceNotFoundException("SchemeTarget", str(target_id))
        return row[0], row[1]

    async def report_progress(self, target_id: uuid.UUID, data: SchemeProgressReport, j: Jurisdiction,
                              actor_id: uuid.UUID, ctx: AuditCtx) -> SchemeTarget:
        target, _ = await self._get_target(target_id, j)
        old = target.reported_value
        target.reported_value = data.reported_value
        target.reported_by = actor_id
        target.reported_at = utcnow()
        if data.remarks:
            target.remarks = data.remarks
        await self.session.flush()
        await self._audit("SCHEME_PROGRESS_REPORTED", "scheme_target", target.id, actor_id, ctx,
                          old_state={"reported_value": float(old) if old is not None else None},
                          new_state={"reported_value": data.reported_value})
        return target

    async def add_remark(self, target_id: uuid.UUID, data: SchemeRemark, j: Jurisdiction, actor_id: uuid.UUID,
                         ctx: AuditCtx) -> SchemeTarget:
        target, _ = await self._get_target(target_id, j)
        target.remarks = f"{target.remarks}\n{data.remarks}" if target.remarks else data.remarks
        await self.session.flush()
        await self._audit("SCHEME_REMARK_ADDED", "scheme_target", target.id, actor_id, ctx,
                          new_state={"remarks": data.remarks})
        return target


def _progress(t: SchemeTarget) -> dict:
    if t.reported_value is not None:
        pct = round(100 * float(t.reported_value) / float(t.target_value), 1) if t.target_value else None
        return {"progress_pct": pct, "reporting_status": "REPORTED"}
    status = "OVERDUE" if date.today() > t.period_end else "PENDING"
    return {"progress_pct": None, "reporting_status": status}


def target_view(t: SchemeTarget) -> dict:
    return {
        "id": t.id, "scheme_id": t.scheme_id, "district": t.district, "period_start": t.period_start,
        "period_end": t.period_end, "target_value": float(t.target_value),
        "reported_value": float(t.reported_value) if t.reported_value is not None else None,
        "reported_by": t.reported_by, "reported_at": t.reported_at, "remarks": t.remarks, **_progress(t),
    }


def _count(values) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return out
