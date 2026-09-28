"""State public-health analytics (Role 11): indicators, aggregate submissions, trends, automatic analysis.

Analysis is deterministic and explainable (period-over-period change, rolling
z-score, reporting completeness). Every output is an AIInsight or
DataQualityIssue awaiting human review — nothing here declares an outbreak,
assigns official severity, or edits source records.
"""
import statistics
import uuid
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.models.facility import Facility
from app.models.governance import (
    ActionPriority,
    ActionStatus,
    ActionUpdateType,
    AIInsight,
    GovernanceAction,
    GovernanceActionUpdate,
    GovernanceAlert,
    GovernanceAlertStatus,
    GovernanceLevel,
    InsightReviewStatus,
)
from app.models.identity import ScopeLevel, User
from app.models.pharmacy import ShortageIncident
from app.models.public_health import (
    AIAnalysisJob,
    AnalysisJobStatus,
    DataQualityIssue,
    DataQualityIssueType,
    DataQualityStatus,
    HealthIndicatorAggregate,
    PublicHealthIndicator,
    ValidationStatus,
)
from app.schemas.public_health import AggregateSubmit, AggregateValidate, DataQualityAction, IndicatorCreate
from app.services.common import AuditCtx, AuditMixin, make_reference, paginate, utcnow
from app.services.health_aggregation_service import OPEN_SHORTAGE_STATES, HealthAggregationService

METHOD = "RULE_BASED_TREND_ANALYSIS"
METHOD_VERSION = "1.0"
CHANGE_THRESHOLD_PCT = 30.0
MIN_BASELINE = 5.0
Z_THRESHOLD = 2.0
RATE_UNITS = {"%", "percent", "rate", "ratio", "per_1000", "per_100000", "days"}

# Indicators the platform can compute itself from operational data (no manual entry).
OPERATIONAL_INDICATORS = {
    "OPD_VISITS": ("Outpatient appointments", "SERVICE_UTILISATION", "count", False, "patient_volume"),
    "CONSULTATIONS": ("Doctor consultations", "SERVICE_UTILISATION", "count", False, "consultations"),
    "REFERRALS": ("Referrals to higher facilities", "SERVICE_UTILISATION", "count", True, "referrals"),
    "MEDICINE_STOCKOUTS": ("Medicine stock-out items", "SUPPLY", "count", True, "stockout_items"),
}


def combine(unit: str, values: List[float]) -> Optional[float]:
    if not values:
        return None
    total = sum(values)
    return round(total / len(values), 4) if unit.lower() in RATE_UNITS else round(total, 4)


def pct_change(cur: Optional[float], prev: Optional[float]) -> Optional[float]:
    if cur is None or prev in (None, 0):
        return None
    return round(100 * (cur - prev) / prev, 1)


class PublicHealthService(AuditMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ indicators
    async def list_indicators(self, active_only: bool = True) -> List[PublicHealthIndicator]:
        stmt = select(PublicHealthIndicator)
        if active_only:
            stmt = stmt.where(PublicHealthIndicator.is_active.is_(True))
        return list((await self.session.execute(stmt.order_by(PublicHealthIndicator.category, PublicHealthIndicator.name))).scalars().all())

    async def get_indicator(self, indicator_id: uuid.UUID) -> PublicHealthIndicator:
        ind = await self.session.get(PublicHealthIndicator, indicator_id)
        if not ind:
            raise ResourceNotFoundException("PublicHealthIndicator", str(indicator_id))
        return ind

    async def create_indicator(self, data: IndicatorCreate, actor_id: uuid.UUID, ctx: AuditCtx) -> PublicHealthIndicator:
        if (await self.session.execute(select(PublicHealthIndicator).where(PublicHealthIndicator.code == data.code))).scalar_one_or_none():
            raise ConflictException(f"Indicator '{data.code}' already exists.")
        ind = PublicHealthIndicator(**data.model_dump())
        ind.category = data.category.upper()
        self.session.add(ind)
        await self.session.flush()
        await self._audit("PUBLIC_HEALTH_INDICATOR_CREATED", "public_health_indicator", ind.id, actor_id, ctx,
                          new_state={"code": ind.code, "unit": ind.unit})
        return ind

    async def _ensure_operational_indicators(self) -> Dict[str, PublicHealthIndicator]:
        out = {}
        for code, (name, cat, unit, worse, _) in OPERATIONAL_INDICATORS.items():
            ind = (await self.session.execute(select(PublicHealthIndicator).where(PublicHealthIndicator.code == code))).scalar_one_or_none()
            if not ind:
                ind = PublicHealthIndicator(code=code, name=name, category=cat, unit=unit, higher_is_worse=worse,
                                            definition=f"{name}, counted from platform operational records per district.")
                self.session.add(ind)
                await self.session.flush()
            out[code] = ind
        return out

    # ------------------------------------------------------------------ aggregates
    async def submit_aggregate(self, data: AggregateSubmit, j: Jurisdiction, actor_id: uuid.UUID, source_role: str,
                               ctx: AuditCtx) -> HealthIndicatorAggregate:
        ind = await self.get_indicator(data.indicator_id)
        if not ind.is_active:
            raise BadRequestException("Indicator is inactive.")
        if data.facility_id:
            f = await self.session.get(Facility, data.facility_id)
            if not f:
                raise ResourceNotFoundException("Facility", str(data.facility_id))
            state, district = f.state, f.district
        elif j.scope == ScopeLevel.DISTRICT or j.is_facility_bound:
            state, district = j.state, j.district
        else:
            if not data.district:
                raise BadRequestException("district is required for state-level submissions.")
            state, district = j.state, data.district
        if j.scope == ScopeLevel.GLOBAL:
            raise PermissionDeniedException("National users consume state aggregates; they do not submit them.")
        j.ensure_covers(state, district if j.scope != ScopeLevel.STATE else None)
        dup = (await self.session.execute(select(HealthIndicatorAggregate.id).where(
            HealthIndicatorAggregate.indicator_id == ind.id, func.lower(HealthIndicatorAggregate.state) == state.lower(),
            func.lower(HealthIndicatorAggregate.district) == district.lower(),
            HealthIndicatorAggregate.facility_id.is_(None) if not data.facility_id else HealthIndicatorAggregate.facility_id == data.facility_id,
            HealthIndicatorAggregate.period_start == data.period_start, HealthIndicatorAggregate.period_end == data.period_end,
        ))).first()
        if dup:
            raise ConflictException("An aggregate for this indicator, geography and period already exists.")
        agg = HealthIndicatorAggregate(
            indicator_id=ind.id, state=state, district=district, facility_id=data.facility_id,
            period_start=data.period_start, period_end=data.period_end, value=data.value,
            numerator=data.numerator, denominator=data.denominator, source_reference=data.source_reference,
            source_role=source_role, validation_status=ValidationStatus.PENDING, submitted_by=actor_id,
        )
        self.session.add(agg)
        await self.session.flush()
        if data.numerator is not None and ind.unit.lower() in ("%", "percent") and data.numerator > data.denominator:
            await self._issue(f"inconsistent:{agg.id}", DataQualityIssueType.INCONSISTENT_VALUE, state, district,
                              f"{data.period_start}..{data.period_end}",
                              f"{ind.code}: numerator {data.numerator} exceeds denominator {data.denominator}.",
                              ind.id, agg.id)
        await self._audit("INDICATOR_AGGREGATE_SUBMITTED", "health_indicator_aggregate", agg.id, actor_id, ctx,
                          new_state={"indicator": ind.code, "district": district, "value": data.value})
        return agg

    async def validate_aggregate(self, aggregate_id: uuid.UUID, data: AggregateValidate, j: Jurisdiction,
                                 actor_id: uuid.UUID, ctx: AuditCtx) -> HealthIndicatorAggregate:
        agg = await self.session.get(HealthIndicatorAggregate, aggregate_id)
        if not agg or not j.covers(agg.state):
            raise ResourceNotFoundException("HealthIndicatorAggregate", str(aggregate_id))
        if agg.submitted_by == actor_id:
            raise BadRequestException("Segregation of duties: you cannot validate your own submission.")
        old = agg.validation_status
        agg.validation_status = data.validation_status
        await self.session.flush()
        await self._audit("INDICATOR_AGGREGATE_VALIDATED", "health_indicator_aggregate", agg.id, actor_id, ctx,
                          old_state={"status": old.value}, new_state={"status": data.validation_status.value, "note": data.note})
        return agg

    async def list_aggregates(self, j: Jurisdiction, indicator_id: Optional[uuid.UUID], district: Optional[str],
                              start: Optional[date], end: Optional[date], page: int, page_size: int):
        stmt = j.filter(select(HealthIndicatorAggregate), HealthIndicatorAggregate.state,
                        HealthIndicatorAggregate.district if j.scope != ScopeLevel.STATE else None)
        if indicator_id:
            stmt = stmt.where(HealthIndicatorAggregate.indicator_id == indicator_id)
        if district:
            stmt = stmt.where(func.lower(HealthIndicatorAggregate.district) == district.lower())
        if start:
            stmt = stmt.where(HealthIndicatorAggregate.period_start >= start)
        if end:
            stmt = stmt.where(HealthIndicatorAggregate.period_end <= end)
        return await paginate(self.session, stmt, HealthIndicatorAggregate.period_start.desc(), page, page_size)

    async def sync_operational_indicators(self, j: Jurisdiction, start: date, end: date, actor_id: Optional[uuid.UUID]) -> int:
        """Idempotently (re)compute platform-derived district aggregates for [start, end]."""
        indicators = await self._ensure_operational_indicators()
        agg_service = HealthAggregationService(self.session)
        snapshots = await agg_service.facility_snapshots(await agg_service.facilities(j), start, end)
        by_district = await agg_service.group_by_region(snapshots, "district")
        written = 0
        for row in by_district:
            for code, ind in indicators.items():
                value = float(row[OPERATIONAL_INDICATORS[code][4]])
                existing = (await self.session.execute(select(HealthIndicatorAggregate).where(
                    HealthIndicatorAggregate.indicator_id == ind.id, HealthIndicatorAggregate.state == row["state"],
                    HealthIndicatorAggregate.district == row["district"], HealthIndicatorAggregate.facility_id.is_(None),
                    HealthIndicatorAggregate.period_start == start, HealthIndicatorAggregate.period_end == end,
                ))).scalar_one_or_none()
                if existing:
                    existing.value = value
                else:
                    self.session.add(HealthIndicatorAggregate(
                        indicator_id=ind.id, state=row["state"], district=row["district"], period_start=start,
                        period_end=end, value=value, source_reference=f"platform:operational:{start}..{end}",
                        source_role="PLATFORM_OPERATIONAL", validation_status=ValidationStatus.VALIDATED,
                        submitted_by=actor_id or await self._system_actor(),
                    ))
                written += 1
        await self.session.flush()
        return written

    async def _system_actor(self) -> uuid.UUID:
        uid = (await self.session.execute(select(User.id).order_by(User.created_at).limit(1))).scalar_one_or_none()
        if uid is None:
            raise BadRequestException("No user exists to attribute system-computed aggregates to.")
        return uid

    # ------------------------------------------------------------------ trends
    async def _window_values(self, ind: PublicHealthIndicator, j: Jurisdiction, start: date, end: date,
                             district: Optional[str] = None) -> Dict[str, Tuple[List[float], Dict[str, int]]]:
        stmt = j.filter(select(HealthIndicatorAggregate).where(
            HealthIndicatorAggregate.indicator_id == ind.id, HealthIndicatorAggregate.period_start >= start,
            HealthIndicatorAggregate.period_start <= end,
            HealthIndicatorAggregate.validation_status != ValidationStatus.REJECTED,
        ), HealthIndicatorAggregate.state, HealthIndicatorAggregate.district if j.scope != ScopeLevel.STATE else None)
        if district:
            stmt = stmt.where(func.lower(HealthIndicatorAggregate.district) == district.lower())
        out: Dict[str, Tuple[List[float], Dict[str, int]]] = {}
        for a in (await self.session.execute(stmt)).scalars().all():
            vals, val = out.setdefault(a.district, ([], {}))
            vals.append(float(a.value))
            val[a.validation_status.value] = val.get(a.validation_status.value, 0) + 1
        return out

    async def _districts(self, j: Jurisdiction) -> List[str]:
        stmt = j.filter(select(Facility.district).where(Facility.is_active.is_(True)).distinct(),
                        Facility.state, Facility.district if j.scope != ScopeLevel.STATE else None)
        return sorted({d for d in (await self.session.execute(stmt)).scalars().all()})

    async def trends(self, indicator_id: uuid.UUID, j: Jurisdiction, district: Optional[str], end: Optional[date],
                     window_days: int) -> dict:
        ind = await self.get_indicator(indicator_id)
        end = end or date.today()
        start = end - timedelta(days=window_days - 1)
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=window_days - 1)
        cur = await self._window_values(ind, j, start, end, district)
        prev = await self._window_values(ind, j, prev_start, prev_end, district)
        all_districts = [district] if district else await self._districts(j)
        points = []
        for d in sorted(set(all_districts) | set(cur) | set(prev)):
            c = combine(ind.unit, cur.get(d, ([], {}))[0])
            p = combine(ind.unit, prev.get(d, ([], {}))[0])
            points.append({"district": d, "current_value": c, "previous_value": p,
                           "change": round(c - p, 4) if c is not None and p is not None else None,
                           "change_pct": pct_change(c, p), "submissions_current": len(cur.get(d, ([], {}))[0]),
                           "validation": cur.get(d, ([], {}))[1]})
        state_cur = combine(ind.unit, [v for vals, _ in cur.values() for v in vals])
        state_prev = combine(ind.unit, [v for vals, _ in prev.values() for v in vals])
        reporting = sum(1 for p in points if p["submissions_current"])
        return {
            "indicator": ind, "scope": j.label,
            "current_period": {"start": start.isoformat(), "end": end.isoformat()},
            "previous_period": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
            "state_current": state_cur, "state_previous": state_prev, "state_change_pct": pct_change(state_cur, state_prev),
            "reporting_coverage": {"districts_expected": len(all_districts), "districts_reporting": reporting,
                                   "coverage_pct": round(100 * reporting / len(all_districts), 1) if all_districts else None},
            "districts": points,
            "sources": ["health_indicator_aggregates"],
        }

    # ------------------------------------------------------------------ automatic analysis
    async def _issue(self, key: str, itype: DataQualityIssueType, state: str, district: Optional[str], period: str,
                     description: str, indicator_id=None, aggregate_id=None) -> bool:
        if (await self.session.execute(select(DataQualityIssue.id).where(DataQualityIssue.dedupe_key == key))).first():
            return False
        self.session.add(DataQualityIssue(dedupe_key=key, issue_type=itype, state=state, district=district,
                                          indicator_id=indicator_id, aggregate_id=aggregate_id,
                                          reporting_period=period, description=description))
        return True

    async def _insight(self, key: str, **fields) -> bool:
        if (await self.session.execute(select(AIInsight.id).where(AIInsight.dedupe_key == key))).first():
            return False
        self.session.add(AIInsight(dedupe_key=key, method=f"{METHOD} v{METHOD_VERSION}", **fields))
        return True

    async def run_analysis(self, j: Jurisdiction, end: Optional[date], window_days: int,
                           actor_id: Optional[uuid.UUID]) -> AIAnalysisJob:
        if j.scope not in (ScopeLevel.STATE, ScopeLevel.GLOBAL):
            raise PermissionDeniedException("Automatic public-health analysis runs at state or national scope.")
        end = end or date.today()
        start = end - timedelta(days=window_days - 1)
        period_label = f"{start.isoformat()}..{end.isoformat()}"
        job = AIAnalysisJob(job_type="PUBLIC_HEALTH_ANALYSIS", scope_reference=j.label, reporting_period=period_label,
                            method=METHOD, method_version=METHOD_VERSION, status=AnalysisJobStatus.RUNNING,
                            triggered_by=actor_id)
        self.session.add(job)
        await self.session.flush()
        try:
            async with self.session.begin_nested():
                await self.sync_operational_indicators(j, start, end, actor_id)
                insights, issues = await self._analyse(j, start, end, window_days, period_label)
            job.status = AnalysisJobStatus.COMPLETED
            job.insights_created, job.issues_created = insights, issues
        except Exception as exc:  # recorded, never silently swallowed: surfaced via job status
            job.status = AnalysisJobStatus.FAILED
            job.error_reference = f"{type(exc).__name__}: {exc}"[:1000]
        job.completed_at = utcnow()
        await self.session.flush()
        await self._audit("PUBLIC_HEALTH_ANALYSIS_RUN", "ai_analysis_job", job.id, actor_id, (None, None),
                          new_state={"status": job.status.value, "insights": job.insights_created,
                                     "issues": job.issues_created, "scope": j.label})
        return job

    async def _analyse(self, j: Jurisdiction, start: date, end: date, window: int, period_label: str) -> Tuple[int, int]:
        insights = issues = 0
        state_districts = await self._districts(j)
        facilities = list((await self.session.execute(
            j.filter(select(Facility).where(Facility.is_active.is_(True)), Facility.state,
                     Facility.district if j.scope != ScopeLevel.STATE else None)
        )).scalars().all())
        district_state = {f.district: f.state for f in facilities}
        shortage_rows = dict((await self.session.execute(
            select(Facility.district, func.count(ShortageIncident.id))
            .join(Facility, ShortageIncident.facility_id == Facility.id)
            .where(ShortageIncident.facility_id.in_([f.id for f in facilities]),
                   ShortageIncident.status.in_(OPEN_SHORTAGE_STATES)).group_by(Facility.district)
        )).all()) if facilities else {}

        for ind in await self.list_indicators():
            cur = await self._window_values(ind, j, start, end)
            history = [await self._window_values(ind, j, start - timedelta(days=window * k),
                                                 end - timedelta(days=window * k)) for k in range(1, 5)]
            manual = ind.code not in OPERATIONAL_INDICATORS
            for d in state_districts:
                state = district_state.get(d, j.state or "")
                if d not in cur:
                    if manual and any(d in h for h in history):
                        ok = await self._issue(f"missing:{ind.code}:{state}:{d}:{period_label}",
                                               DataQualityIssueType.MISSING_REPORT, state, d, period_label,
                                               f"No {ind.code} submission from {d} for {period_label}, although earlier periods were reported.",
                                               ind.id)
                        issues += ok
                    continue
                c = combine(ind.unit, cur[d][0])
                prev_vals = [combine(ind.unit, h[d][0]) for h in history if d in h]
                p = prev_vals[0] if prev_vals else None
                change = pct_change(c, p)
                direction_bad = (change or 0) > 0 if ind.higher_is_worse else (change or 0) < 0
                if change is not None and abs(change) >= CHANGE_THRESHOLD_PCT and max(c or 0, p or 0) >= MIN_BASELINE:
                    ok = await self._insight(
                        f"trend:{ind.code}:{state}:{d}:{period_label}",
                        level=GovernanceLevel.STATE, insight_type="HEALTH_TREND", state=state, district=d,
                        indicator_id=ind.id, reporting_period=period_label,
                        observation=f"{ind.name} in {d} {'rose' if change > 0 else 'fell'} {abs(change)}% "
                                    f"({p} → {c} {ind.unit}) versus the previous {window}-day period.",
                        explanation=f"Period-over-period comparison of submitted aggregates; threshold ±{CHANGE_THRESHOLD_PCT}% "
                                    f"with a minimum baseline of {MIN_BASELINE}. "
                                    f"{'This direction is unfavourable for this indicator.' if direction_bad else 'This direction is favourable.'}",
                        limitations="Based only on submitted/computed aggregates; reporting delays, small numbers and "
                                    "changes in facility coverage can produce apparent trends. Not an outbreak declaration.",
                        suggested_follow_up="Verify with the district and review alongside service and supply context."
                        if direction_bad else "Note for context; no action implied.",
                        source_references={"indicator": ind.code, "district": d, "current": c, "previous": p},
                        confidence=0.6 if len(cur[d][0]) > 1 else 0.4,
                    )
                    insights += ok
                if len(prev_vals) >= 3 and c is not None:
                    mean = statistics.mean(prev_vals)
                    sd = statistics.pstdev(prev_vals)
                    if sd > 0 and (c - mean) / sd >= Z_THRESHOLD and ind.higher_is_worse:
                        ok = await self._insight(
                            f"anomaly:{ind.code}:{state}:{d}:{period_label}",
                            level=GovernanceLevel.STATE, insight_type="ANOMALY", state=state, district=d,
                            indicator_id=ind.id, reporting_period=period_label,
                            observation=f"{ind.name} in {d} ({c}) is {round((c - mean) / sd, 1)} standard deviations "
                                        f"above its recent average ({round(mean, 2)}).",
                            explanation=f"Rolling z-score against the previous {len(prev_vals)} periods; threshold {Z_THRESHOLD}.",
                            limitations="Few historical periods make the baseline unstable; requires analyst review.",
                            suggested_follow_up="Request data verification from the district before drawing conclusions.",
                            source_references={"indicator": ind.code, "history": prev_vals, "current": c},
                            confidence=0.5,
                        )
                        insights += ok
                if ind.higher_is_worse and change is not None and change >= CHANGE_THRESHOLD_PCT and shortage_rows.get(d):
                    ok = await self._insight(
                        f"supply:{ind.code}:{state}:{d}:{period_label}",
                        level=GovernanceLevel.STATE, insight_type="HEALTH_SUPPLY_CORRELATION", state=state, district=d,
                        indicator_id=ind.id, reporting_period=period_label,
                        observation=f"{d} shows a {change}% rise in {ind.name} while {shortage_rows[d]} medicine shortage "
                                    f"incident(s) remain open.",
                        explanation="Co-occurrence of an unfavourable indicator trend and open shortages in the same district.",
                        limitations="Co-occurrence only — this does not establish that the shortage caused the trend.",
                        suggested_follow_up="Share with the State Supply Chain Manager for supply review.",
                        source_references={"indicator": ind.code, "open_shortages": shortage_rows[d]},
                        confidence=0.4,
                    )
                    insights += ok
        await self.session.flush()
        return insights, issues

    async def list_jobs(self, page: int, page_size: int):
        return await paginate(self.session, select(AIAnalysisJob), AIAnalysisJob.started_at.desc(), page, page_size)

    # ------------------------------------------------------------------ data quality
    async def list_issues(self, j: Jurisdiction, status: Optional[DataQualityStatus], page: int, page_size: int):
        stmt = j.filter(select(DataQualityIssue), DataQualityIssue.state,
                        DataQualityIssue.district if j.scope != ScopeLevel.STATE else None)
        if status:
            stmt = stmt.where(DataQualityIssue.status == status)
        return await paginate(self.session, stmt, DataQualityIssue.created_at.desc(), page, page_size)

    async def _get_issue(self, issue_id: uuid.UUID, j: Jurisdiction) -> DataQualityIssue:
        issue = await self.session.get(DataQualityIssue, issue_id)
        if not issue or not j.covers(issue.state, issue.district if j.scope == ScopeLevel.DISTRICT else None):
            raise ResourceNotFoundException("DataQualityIssue", str(issue_id))
        return issue

    async def request_verification(self, issue_id: uuid.UUID, data: DataQualityAction, j: Jurisdiction,
                                   actor_id: uuid.UUID, ctx: AuditCtx) -> DataQualityIssue:
        """The analyst asks the district to verify; the analyst never edits the source record."""
        issue = await self._get_issue(issue_id, j)
        if issue.status != DataQualityStatus.OPEN:
            raise ConflictException(f"Issue is {issue.status.value}.")
        issue.status = DataQualityStatus.VERIFICATION_REQUESTED
        issue.verification_note = data.note
        issue.requested_by = actor_id
        if issue.district:
            action = GovernanceAction(
                reference=make_reference("ACT"), level=GovernanceLevel.DISTRICT, state=issue.state, district=issue.district,
                category="DATA_VERIFICATION", title=f"Verify data: {issue.issue_type.value}",
                description=f"{issue.description}\n\nAnalyst note: {data.note}", priority=ActionPriority.MEDIUM,
                status=ActionStatus.PENDING, created_by=actor_id, source_reference=f"dq:{issue.id}",
            )
            self.session.add(action)
            await self.session.flush()
            self.session.add(GovernanceActionUpdate(action_id=action.id, actor_id=actor_id,
                                                    update_type=ActionUpdateType.STATUS_CHANGE,
                                                    to_status=ActionStatus.PENDING.value, note="Verification requested by analyst."))
        await self.session.flush()
        await self._audit("DATA_QUALITY_VERIFICATION_REQUESTED", "data_quality_issue", issue.id, actor_id, ctx,
                          new_state={"note": data.note})
        return issue

    async def close_issue(self, issue_id: uuid.UUID, resolve: bool, data: DataQualityAction, j: Jurisdiction,
                          actor_id: uuid.UUID, ctx: AuditCtx) -> DataQualityIssue:
        issue = await self._get_issue(issue_id, j)
        if issue.status in (DataQualityStatus.RESOLVED, DataQualityStatus.DISMISSED):
            raise ConflictException(f"Issue is already {issue.status.value}.")
        if resolve and not data.resolution_reference:
            raise BadRequestException("resolution_reference is required to resolve an issue.")
        issue.status = DataQualityStatus.RESOLVED if resolve else DataQualityStatus.DISMISSED
        issue.resolution_reference = data.resolution_reference or data.note
        await self.session.flush()
        await self._audit("DATA_QUALITY_" + issue.status.value, "data_quality_issue", issue.id, actor_id, ctx,
                          new_state={"note": data.note})
        return issue

    # ------------------------------------------------------------------ dashboard
    async def dashboard(self, j: Jurisdiction) -> dict:
        async def count(stmt) -> int:
            return (await self.session.execute(stmt)).scalar_one() or 0

        dist_col = lambda m: m.district if j.scope != ScopeLevel.STATE else None
        districts = await self._districts(j)
        since = date.today() - timedelta(days=30)
        reporting = (await self.session.execute(j.filter(
            select(func.count(func.distinct(HealthIndicatorAggregate.district))).where(
                HealthIndicatorAggregate.period_start >= since, HealthIndicatorAggregate.source_role != "PLATFORM_OPERATIONAL"),
            HealthIndicatorAggregate.state, dist_col(HealthIndicatorAggregate)))).scalar_one() or 0
        last_job = (await self.session.execute(select(AIAnalysisJob).order_by(AIAnalysisJob.started_at.desc()).limit(1))).scalar_one_or_none()
        return {
            "as_of": utcnow(), "scope": j.label,
            "indicators_active": await count(select(func.count(PublicHealthIndicator.id)).where(PublicHealthIndicator.is_active.is_(True))),
            "districts_in_scope": len(districts),
            "districts_reporting_30d": reporting,
            "reporting_coverage_pct": round(100 * reporting / len(districts), 1) if districts else None,
            "insights_pending_review": await count(j.filter(select(func.count(AIInsight.id)).where(
                AIInsight.review_status == InsightReviewStatus.PENDING_REVIEW), AIInsight.state, dist_col(AIInsight))),
            "open_public_health_alerts": await count(j.filter(select(func.count(GovernanceAlert.id)).where(
                GovernanceAlert.status.in_([GovernanceAlertStatus.OPEN, GovernanceAlertStatus.ACKNOWLEDGED,
                                            GovernanceAlertStatus.UNDER_REVIEW])),
                GovernanceAlert.state, dist_col(GovernanceAlert))),
            "open_data_quality_issues": await count(j.filter(select(func.count(DataQualityIssue.id)).where(
                DataQualityIssue.status.in_([DataQualityStatus.OPEN, DataQualityStatus.VERIFICATION_REQUESTED])),
                DataQualityIssue.state, dist_col(DataQualityIssue))),
            "last_analysis": {"status": last_job.status.value, "completed_at": last_job.completed_at,
                              "period": last_job.reporting_period, "error": last_job.error_reference} if last_job else None,
        }
