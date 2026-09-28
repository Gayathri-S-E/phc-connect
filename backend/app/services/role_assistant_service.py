"""Role-specific AI assistants for Roles 06–12.

Each assistant answers only from live data inside the caller's jurisdiction,
states the data period it used, lists its sources, and returns suggestions
that require human confirmation. Requests for clinical decisions, patient
identities or autonomous administrative actions are refused.

The answer text is produced by deterministic, grounded templates
(method GROUNDED_RULE_BASED_SUMMARY). No external LLM is connected; if one is
added later it must sit behind `compose()` and receive only these grounded facts.
"""
import re
import uuid
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jurisdiction import Jurisdiction
from app.models.emergency import EmergencyAffectedFacility, EmergencyIncident, EmergencyTask
from app.models.facility import Facility
from app.models.governance import (
    ActionStatus,
    AIInsight,
    AIInteraction,
    ApprovalRequest,
    ApprovalStatus,
    GovernanceAction,
    GovernanceAlert,
    GovernanceAlertStatus,
    GovernanceReport,
    InsightReviewStatus,
    ReportReviewStatus,
)
from app.models.healthcare import Medication
from app.models.identity import ScopeLevel
from app.models.pharmacy import BatchStatus, InventoryBatch, InventoryItem, StockTransfer, StockTransferStatus
from app.models.public_health import DataQualityIssue, DataQualityStatus
from app.models.supply_chain import SupplyHealthImpact, SupplyRequest
from app.services.common import utcnow
from app.services.emergency_service import OPEN_TASKS
from app.services.health_aggregation_service import ACTIVE_EMERGENCY_STATES, HealthAggregationService
from app.services.supply_request_service import DELAY_THRESHOLD_DAYS, OPEN_REQUEST_STATES

METHOD = "GROUNDED_RULE_BASED_SUMMARY v1"
DISCLAIMER = ("AI-generated decision support from authorized platform data. It does not diagnose, prescribe, "
              "set emergency severity, or take actions; an authorized person must confirm any decision.")

REFUSALS: List[Tuple[str, str]] = [
    (r"\b(diagnos\w*|prescri\w*|dosage|dose|treat(ment)?|which (medicine|drug)|triage)\b|நோயறிதல்|மருந்து பரிந்துரை",
     "I can't give clinical advice (diagnosis, prescribing, dosing or triage). Please consult the responsible Medical Officer."),
    (r"\b(patient'?s? (name|phone|address|record)|aadhaar|who is the patient|identify (the )?patient)\b",
     "I only work with aggregated information and can't reveal patient identities or individual records."),
    (r"\b(approve|reject|allocate|dispatch|close|resolve|assign|declare|set (the )?severity|deduct|order|purchase)\b.*\b(for me|automatically|now|yourself)\b",
     "I can't take actions or make decisions. I can summarise the information so an authorized person can decide."),
    (r"\b(declare|announce)\b.*\boutbreak\b",
     "I can't declare outbreaks or issue official alerts. I can summarise trends for review by authorized officials."),
]

GENERIC_REFUSAL_EN = "This assistant is limited to {topic}. Please rephrase your question within that scope."


def _match(question: str, *patterns: str) -> bool:
    q = question.lower()
    return any(re.search(p, q) for p in patterns)


class RoleAssistantService:
    ASSISTANTS = {
        "DHO": "district health monitoring and administration",
        "DSCO": "district medicine supply-chain operations",
        "EMERGENCY": "district emergency coordination",
        "STATE_ADMIN": "state health administration",
        "STATE_SUPPLY": "state warehouse and supply-chain operations",
        "ANALYST": "state public-health analytics",
        "NATIONAL": "national health and supply-chain oversight",
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.agg = HealthAggregationService(session)

    async def ask(self, assistant: str, question: str, j: Jurisdiction, user_id: uuid.UUID,
                  context_reference: Optional[str], language: str) -> dict:
        refusal = next((msg for pattern, msg in REFUSALS if re.search(pattern, question.lower())), None)
        if refusal:
            result = {"intent": "REFUSED", "answer": refusal, "refused": True, "sources": [], "suggestions": [],
                      "data_period": None, "answer_ta": None}
        else:
            handler, intent = self._route(assistant, question)
            result = await handler(j, question)
            result.update(intent=intent, refused=False)
            result.setdefault("answer_ta", None)
        self.session.add(AIInteraction(
            user_id=user_id, assistant=assistant, scope_reference=j.label, context_reference=context_reference,
            question=question[:1000], intent=result["intent"], method=METHOD, refused=result["refused"],
        ))
        await self.session.flush()
        if language != "ta":
            result["answer_ta"] = None
        return {**result, "assistant": assistant, "scope": j.label, "method": METHOD, "disclaimer": DISCLAIMER,
                "generated_at": utcnow()}

    def _route(self, assistant: str, q: str) -> Tuple[Callable, str]:
        routes: Dict[str, List[Tuple[Tuple[str, ...], Callable, str]]] = {
            "DHO": [
                ((r"trend", r"footfall", r"volume", r"week"), self._district_trend, "DISTRICT_TRENDS"),
                ((r"attention", r"problem", r"disrupt", r"which phc", r"concern"), self._phc_attention, "PHC_SITUATION"),
                ((r"alert",), self._alert_summary, "ALERT_SUMMARY"),
                ((r"action", r"pending", r"remind", r"follow"), self._pending_actions, "PENDING_ACTIONS"),
                ((r"supply", r"shortage", r"medicine", r"stock"), self._supply_impact, "SUPPLY_IMPACT"),
            ],
            "DSCO": [
                ((r"redistribut", r"surplus", r"transfer", r"move"), self._redistribution, "REDISTRIBUTION"),
                ((r"expir",), self._expiry, "EXPIRY"),
                ((r"delay", r"transit", r"late"), self._delays, "DELAYS"),
                ((r"request", r"pending", r"emergency"), self._request_summary, "REQUESTS"),
            ],
            "EMERGENCY": [
                ((r"gap", r"staff", r"resource", r"need"), self._emergency_gaps, "RESOURCE_STAFF_GAPS"),
                ((r"escalat",), self._emergency_escalation, "ESCALATION_SUGGESTION"),
            ],
            "STATE_ADMIN": [
                ((r"district", r"risk", r"attention", r"compare"), self._district_risk, "DISTRICT_RISK"),
                ((r"alert", r"escalat"), self._alert_summary, "ALERT_SUMMARY"),
                ((r"approv", r"pending"), self._approvals, "APPROVALS"),
                ((r"supply", r"shortage", r"medicine"), self._supply_impact, "SUPPLY_IMPACT"),
            ],
            "STATE_SUPPLY": [
                ((r"expir",), self._expiry, "EXPIRY"),
                ((r"request", r"allocat", r"pending", r"emergency"), self._request_summary, "REQUESTS"),
                ((r"delay", r"transit", r"dispatch"), self._delays, "DELAYS"),
                ((r"redistribut", r"surplus"), self._redistribution, "REDISTRIBUTION"),
            ],
            "ANALYST": [
                ((r"quality", r"missing", r"complete"), self._data_quality, "DATA_QUALITY"),
                ((r"insight", r"trend", r"anomal", r"rising", r"increase"), self._insights, "INSIGHTS"),
            ],
            "NATIONAL": [
                ((r"state", r"compare", r"risk"), self._state_comparison, "STATE_COMPARISON"),
                ((r"report", r"review"), self._reports_pending, "REPORTS"),
                ((r"alert",), self._alert_summary, "ALERT_SUMMARY"),
                ((r"supply", r"shortage", r"medicine", r"stock"), self._supply_impact, "SUPPLY_IMPACT"),
            ],
        }
        defaults = {
            "DHO": (self._district_summary, "DAILY_SUMMARY"), "DSCO": (self._stock_risk, "STOCK_RISK"),
            "EMERGENCY": (self._emergency_summary, "EMERGENCY_SUMMARY"),
            "STATE_ADMIN": (self._district_summary, "STATE_SUMMARY"), "STATE_SUPPLY": (self._stock_risk, "STOCK_RISK"),
            "ANALYST": (self._insights, "INSIGHTS"), "NATIONAL": (self._district_summary, "NATIONAL_SUMMARY"),
        }
        for patterns, handler, intent in routes.get(assistant, []):
            if _match(q, *patterns):
                return handler, intent
        return defaults[assistant]

    # ------------------------------------------------------------------ shared facts
    async def _snapshots(self, j: Jurisdiction, days: int = 1):
        end = date.today()
        start = end - timedelta(days=days - 1)
        facilities = await self.agg.facilities(j)
        return await self.agg.facility_snapshots(facilities, start, end), start, end

    def _geo(self, j: Jurisdiction, stmt, model, district: bool = True):
        return j.filter(stmt, model.state, model.district if district and j.scope != ScopeLevel.STATE else None)

    async def _count(self, stmt) -> int:
        return (await self.session.execute(stmt)).scalar_one() or 0

    # ------------------------------------------------------------------ governance handlers
    async def _district_summary(self, j: Jurisdiction, q: str) -> dict:
        snaps, start, end = await self._snapshots(j)
        t = self.agg.totals(snaps)
        attention = [s for s in snaps if s["operational_status"] in ("NEEDS_ATTENTION", "DISRUPTED")]
        emergencies = await self.agg.active_emergency_count(j)
        alerts = await self._count(self._geo(j, select(func.count(GovernanceAlert.id)).where(
            GovernanceAlert.status.in_([GovernanceAlertStatus.OPEN, GovernanceAlertStatus.ACKNOWLEDGED])), GovernanceAlert))
        actions = await self._count(self._geo(j, select(func.count(GovernanceAction.id)).where(
            GovernanceAction.status.not_in([ActionStatus.RESOLVED, ActionStatus.CLOSED, ActionStatus.ESCALATED])), GovernanceAction))
        staff = f"{t['staff_availability_pct']}%" if t["staff_availability_pct"] is not None else "not recorded"
        lines = [
            f"Today {t['facilities']} active facilities are in scope; {len(attention)} need attention "
            f"and {t['facilities_by_status'].get('DISRUPTED', 0)} are disrupted.",
            f"Patient appointments today: {t['patient_volume']}; consultations: {t['consultations']}; referrals: {t['referrals']}.",
            f"Staff availability (attendance vs assigned): {staff}.",
            f"Medicines out of stock across facilities: {t['stockout_items']}; open shortage incidents: {t['open_shortages']}.",
            f"Open health alerts: {alerts}; pending administrative actions: {actions}; active emergencies: {emergencies}.",
        ]
        if attention:
            lines.append("Facilities needing attention: " + "; ".join(
                f"{s['facility_name']} ({' '.join(s['status_reasons'])})" for s in attention[:5]))
        ta = (f"இன்று {t['facilities']} சுகாதார நிலையங்கள் கண்காணிப்பில் உள்ளன; {len(attention)} நிலையங்களுக்கு கவனம் தேவை. "
              f"இன்றைய நோயாளர் வருகை: {t['patient_volume']}. மருந்து இருப்பு இல்லாதவை: {t['stockout_items']}. "
              f"திறந்த எச்சரிக்கைகள்: {alerts}; நிலுவையிலுள்ள நடவடிக்கைகள்: {actions}.")
        return {"answer": "\n".join(lines), "answer_ta": ta, "data_period": f"{start}..{end}",
                "sources": ["appointments", "consultations", "referrals", "staff_attendance", "inventory_items",
                            "shortage_incidents", "governance_alerts", "governance_actions", "emergency_incidents"],
                "suggestions": ["Review the facilities listed as needing attention."] if attention else []}

    async def _phc_attention(self, j: Jurisdiction, q: str) -> dict:
        snaps, start, end = await self._snapshots(j, 7)
        flagged = sorted((s for s in snaps if s["operational_status"] != "OPERATIONAL"),
                         key=lambda s: (s["operational_status"] != "DISRUPTED", -len(s["status_reasons"])))
        if not flagged:
            answer = "No facility currently triggers an attention rule (staff, stock-outs, cold chain, shortages, emergencies)."
        else:
            answer = "\n".join(f"- {s['facility_name']}: {s['operational_status']} — {' '.join(s['status_reasons'])}"
                               for s in flagged[:10])
        return {"answer": answer, "data_period": f"{start}..{end}",
                "sources": ["staff_attendance", "inventory_items", "cold_chain_equipment", "shortage_incidents",
                            "emergency_affected_facilities"],
                "suggestions": ["Consider creating a pending action for facilities marked DISRUPTED."] if flagged else []}

    async def _district_trend(self, j: Jurisdiction, q: str) -> dict:
        end = date.today()
        start = end - timedelta(days=13)
        facilities = await self.agg.facilities(j)
        series = await self.agg.daily_series([f.id for f in facilities], start, end)
        first, second = series[:7], series[7:]
        a = sum(d["appointments"] for d in first)
        b = sum(d["appointments"] for d in second)
        change = f"{round(100 * (b - a) / a, 1)}%" if a else "not computable (no appointments in the earlier week)"
        answer = (f"Appointments: {a} in {first[0]['date']}..{first[-1]['date']} vs {b} in "
                  f"{second[0]['date']}..{second[-1]['date']} (change {change}). "
                  f"Consultations: {sum(d['consultations'] for d in first)} vs {sum(d['consultations'] for d in second)}. "
                  f"Referrals: {sum(d['referrals'] for d in first)} vs {sum(d['referrals'] for d in second)}.")
        return {"answer": answer, "data_period": f"{start}..{end}",
                "sources": ["appointments", "consultations", "referrals"], "suggestions": []}

    async def _alert_summary(self, j: Jurisdiction, q: str) -> dict:
        rows = (await self.session.execute(self._geo(j, select(
            GovernanceAlert.category, GovernanceAlert.severity, func.count()).where(
            GovernanceAlert.status.in_([GovernanceAlertStatus.OPEN, GovernanceAlertStatus.ACKNOWLEDGED,
                                        GovernanceAlertStatus.UNDER_REVIEW]))
            .group_by(GovernanceAlert.category, GovernanceAlert.severity), GovernanceAlert))).all()
        if not rows:
            answer = "There are no open health alerts in your jurisdiction."
        else:
            answer = "Open health alerts by category: " + "; ".join(
                f"{c} ({s.value if s else 'severity not yet assigned'}): {n}" for c, s, n in rows)
        return {"answer": answer, "data_period": f"as of {date.today()}", "sources": ["governance_alerts"],
                "suggestions": ["Alerts without an assigned severity need review by an authorized officer."]
                if any(s is None for _, s, _ in rows) else []}

    async def _pending_actions(self, j: Jurisdiction, q: str) -> dict:
        now = utcnow()
        rows = (await self.session.execute(self._geo(j, select(GovernanceAction).where(
            GovernanceAction.status.not_in([ActionStatus.RESOLVED, ActionStatus.CLOSED, ActionStatus.ESCALATED]))
            .order_by(GovernanceAction.due_at.is_(None), GovernanceAction.due_at).limit(10), GovernanceAction))).scalars().all()
        if not rows:
            return {"answer": "No pending administrative actions.", "data_period": f"as of {date.today()}",
                    "sources": ["governance_actions"], "suggestions": []}
        lines = []
        for a in rows:
            due = a.due_at.replace(tzinfo=a.due_at.tzinfo or now.tzinfo) if a.due_at else None
            flag = " — OVERDUE" if due and due < now else ""
            lines.append(f"- {a.reference} [{a.priority.value}] {a.title} ({a.status.value}){flag}")
        return {"answer": "\n".join(lines), "data_period": f"as of {date.today()}", "sources": ["governance_actions"],
                "suggestions": ["Follow up on overdue items with the responsible role."]}

    async def _supply_impact(self, j: Jurisdiction, q: str) -> dict:
        snaps, start, end = await self._snapshots(j)
        affected = [s for s in snaps if s["stockout_items"] or s["open_shortages"]]
        impacts = (await self.session.execute(self._geo(j, select(SupplyHealthImpact).where(
            SupplyHealthImpact.acknowledged_by.is_(None)).order_by(SupplyHealthImpact.created_at.desc()).limit(5),
            SupplyHealthImpact))).scalars().all()
        lines = [f"{len(affected)} facilities report stock-outs or open shortages."]
        lines += [f"- {s['facility_name']}: {s['stockout_items']} out of stock, {s['open_shortages']} open incident(s)"
                  for s in affected[:8]]
        if impacts:
            lines.append(f"{len(impacts)} unacknowledged supply-impact notice(s) from the supply officer:")
            lines += [f"- [{i.severity}] {i.impact_summary[:160]}" for i in impacts]
        return {"answer": "\n".join(lines), "data_period": f"{start}..{end}",
                "sources": ["inventory_items", "shortage_incidents", "supply_health_impacts"],
                "suggestions": ["Coordinate with the District Supply Chain Officer; supply actions remain with that role."]
                if affected else []}

    async def _district_risk(self, j: Jurisdiction, q: str) -> dict:
        snaps, start, end = await self._snapshots(j)
        rows = await self.agg.group_by_region(snaps, "district")
        ranked = sorted(rows, key=lambda r: -(r["facilities_by_status"].get("DISRUPTED", 0) * 5
                                              + r["facilities_by_status"].get("NEEDS_ATTENTION", 0) * 2
                                              + r["stockout_items"]))
        if not ranked:
            return {"answer": "No districts with active facilities in scope.", "data_period": f"{start}..{end}",
                    "sources": [], "suggestions": []}
        lines = [f"- {r['district']}: {r['facilities_by_status'].get('DISRUPTED', 0)} disrupted, "
                 f"{r['facilities_by_status'].get('NEEDS_ATTENTION', 0)} need attention, {r['stockout_items']} stock-outs, "
                 f"staff availability {r['staff_availability_pct'] if r['staff_availability_pct'] is not None else 'n/a'}%"
                 for r in ranked[:10]]
        return {"answer": "Districts ranked by operational risk (rule: disrupted×5 + attention×2 + stock-outs):\n" + "\n".join(lines),
                "data_period": f"{start}..{end}", "sources": ["facility operational snapshots"],
                "suggestions": ["Review the top-ranked districts with their DHOs."]}

    async def _approvals(self, j: Jurisdiction, q: str) -> dict:
        n = await self._count(j.filter(select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.status == ApprovalStatus.PENDING), ApprovalRequest.state, None))
        c = await self._count(j.filter(select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.status == ApprovalStatus.CLARIFICATION_REQUESTED), ApprovalRequest.state, None))
        return {"answer": f"{n} approval request(s) are pending your decision and {c} await clarification from requesters.",
                "data_period": f"as of {date.today()}", "sources": ["approval_requests"], "suggestions": []}

    async def _state_comparison(self, j: Jurisdiction, q: str) -> dict:
        snaps, start, end = await self._snapshots(j)
        rows = await self.agg.group_by_region(snaps, "state")
        lines = [f"- {r['state']}: {r['facilities']} facilities, {r['patient_volume']} appointments today, "
                 f"{r['stockout_items']} stock-outs, {r['open_shortages']} open shortages" for r in rows]
        return {"answer": "State comparison:\n" + ("\n".join(lines) or "No state data."), "data_period": f"{start}..{end}",
                "sources": ["facility operational snapshots"], "suggestions": []}

    async def _reports_pending(self, j: Jurisdiction, q: str) -> dict:
        n = await self._count(j.filter(select(func.count(GovernanceReport.id)).where(
            GovernanceReport.review_status.in_([ReportReviewStatus.SUBMITTED, ReportReviewStatus.UNDER_REVIEW])),
            GovernanceReport.state, None))
        return {"answer": f"{n} submitted report(s) are awaiting review in your scope.",
                "data_period": f"as of {date.today()}", "sources": ["governance_reports"], "suggestions": []}

    # ------------------------------------------------------------------ supply handlers
    async def _items(self, j: Jurisdiction):
        facilities = await self.agg.facilities(j)
        ids = [f.id for f in facilities]
        names = {f.id: f.name for f in facilities}
        if not ids:
            return [], names
        avail = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
        rows = (await self.session.execute(
            select(InventoryItem.facility_id, InventoryItem.medication_id, Medication.generic_name, avail, InventoryItem.reorder_level)
            .join(Medication, InventoryItem.medication_id == Medication.id).where(InventoryItem.facility_id.in_(ids))
        )).all()
        return rows, names

    async def _stock_risk(self, j: Jurisdiction, q: str) -> dict:
        rows, names = await self._items(j)
        out = [r for r in rows if r[3] <= 0]
        low = [r for r in rows if 0 < r[3] <= r[4]]
        lines = [f"{len(out)} stock-out(s) and {len(low)} low-stock item(s) across {len(names)} facilities."]
        lines += [f"- OUT: {m} at {names[f]}" for f, _, m, _, _ in out[:8]]
        lines += [f"- LOW: {m} at {names[f]} ({a} available, reorder level {r})" for f, _, m, a, r in low[:8]]
        return {"answer": "\n".join(lines), "data_period": f"as of {date.today()}", "sources": ["inventory_items"],
                "suggestions": ["Check redistribution options before escalating to the state."] if out or low else []}

    async def _redistribution(self, j: Jurisdiction, q: str) -> dict:
        rows, names = await self._items(j)
        by_med: Dict[uuid.UUID, list] = {}
        for r in rows:
            by_med.setdefault(r[1], []).append(r)
        suggestions = []
        for med_rows in by_med.values():
            short = [r for r in med_rows if r[3] <= r[4]]
            surplus = sorted([r for r in med_rows if r[3] >= 2 * max(r[4], 1)], key=lambda r: -r[3])
            for s in short:
                for p in surplus:
                    if p[0] == s[0]:
                        continue
                    qty = min(p[3] - p[4], max(s[4] - s[3], 1))
                    if qty > 0:
                        suggestions.append(f"{s[2]}: move up to {qty} from {names[p[0]]} ({p[3]} available) to "
                                           f"{names[s[0]]} ({s[3]} available)")
                        break
        answer = ("Possible redistributions (rule: source keeps ≥ its reorder level; target below reorder level):\n"
                  + "\n".join(f"- {s}" for s in suggestions[:10])) if suggestions else \
            "No redistribution candidates: no facility has surplus (≥ 2× reorder level) of a medicine another facility is short of."
        return {"answer": answer, "data_period": f"as of {date.today()}", "sources": ["inventory_items"],
                "suggestions": ["Create an authorized supply request/allocation to act on a suggestion."] if suggestions else []}

    async def _expiry(self, j: Jurisdiction, q: str) -> dict:
        facilities = await self.agg.facilities(j)
        ids = [f.id for f in facilities]
        names = {f.id: f.name for f in facilities}
        horizon = date.today() + timedelta(days=60)
        rows = (await self.session.execute(
            select(InventoryItem.facility_id, Medication.generic_name, InventoryBatch.batch_number, InventoryBatch.expiry_date,
                   InventoryBatch.current_quantity)
            .join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
            .join(Medication, InventoryItem.medication_id == Medication.id)
            .where(InventoryItem.facility_id.in_(ids), InventoryBatch.status == BatchStatus.AVAILABLE,
                   InventoryBatch.current_quantity > 0, InventoryBatch.expiry_date <= horizon)
            .order_by(InventoryBatch.expiry_date)
        )).all() if ids else []
        answer = (f"{len(rows)} batch(es) expire within 60 days:\n" + "\n".join(
            f"- {m} batch {b} at {names[f]}: {qty} units, expires {e}" for f, m, b, e, qty in rows[:10])) if rows \
            else "No batches expire within the next 60 days."
        return {"answer": answer, "data_period": f"{date.today()}..{horizon}", "sources": ["inventory_batches"],
                "suggestions": ["Prioritise FEFO dispensing or redistribute near-expiry stock."] if rows else []}

    async def _delays(self, j: Jurisdiction, q: str) -> dict:
        facilities = await self.agg.facilities(j)
        ids = [f.id for f in facilities]
        cutoff = utcnow() - timedelta(days=DELAY_THRESHOLD_DAYS)
        rows = (await self.session.execute(select(StockTransfer).where(
            StockTransfer.status == StockTransferStatus.IN_TRANSIT,
            (StockTransfer.source_facility_id.in_(ids)) | (StockTransfer.destination_facility_id.in_(ids)),
        ))).scalars().all() if ids else []
        late = [t for t in rows if t.dispatched_at and t.dispatched_at.replace(tzinfo=t.dispatched_at.tzinfo or cutoff.tzinfo) < cutoff]
        answer = (f"{len(rows)} transfer(s) in transit; {len(late)} exceed {DELAY_THRESHOLD_DAYS} days without verified receipt."
                  + ("\n" + "\n".join(f"- {t.transfer_number} dispatched {t.dispatched_at:%Y-%m-%d}" for t in late[:10]) if late else ""))
        return {"answer": answer, "data_period": f"as of {date.today()}", "sources": ["stock_transfers"],
                "suggestions": ["Contact the receiving facility to confirm receipt."] if late else []}

    async def _request_summary(self, j: Jurisdiction, q: str) -> dict:
        stmt = self._geo(j, select(SupplyRequest.level, SupplyRequest.priority, SupplyRequest.status, func.count())
                         .where(SupplyRequest.status.in_(OPEN_REQUEST_STATES))
                         .group_by(SupplyRequest.level, SupplyRequest.priority, SupplyRequest.status), SupplyRequest)
        rows = (await self.session.execute(stmt)).all()
        if not rows:
            return {"answer": "No open supply requests.", "data_period": f"as of {date.today()}",
                    "sources": ["supply_requests"], "suggestions": []}
        lines = [f"- {lvl.value} / {pr.value} / {st.value}: {n}" for lvl, pr, st, n in rows]
        emergency = sum(n for _, pr, _, n in rows if pr.value == "EMERGENCY")
        return {"answer": "Open supply requests (level / priority / status):\n" + "\n".join(lines),
                "data_period": f"as of {date.today()}", "sources": ["supply_requests"],
                "suggestions": [f"{emergency} emergency request(s) are open; configured rules prioritise them."] if emergency else []}

    # ------------------------------------------------------------------ emergency handlers
    async def _active_emergencies(self, j: Jurisdiction):
        return (await self.session.execute(self._geo(j, select(EmergencyIncident).where(
            EmergencyIncident.status.in_(ACTIVE_EMERGENCY_STATES)), EmergencyIncident))).scalars().all()

    async def _emergency_summary(self, j: Jurisdiction, q: str) -> dict:
        incidents = await self._active_emergencies(j)
        if not incidents:
            return {"answer": "There are no active emergencies in your district.", "data_period": f"as of {date.today()}",
                    "sources": ["emergency_incidents"], "suggestions": []}
        lines = [f"{len(incidents)} active emergency(ies):"]
        for e in incidents:
            open_tasks = await self._count(select(func.count(EmergencyTask.id)).where(
                EmergencyTask.incident_id == e.id, EmergencyTask.status.in_(OPEN_TASKS)))
            lines.append(f"- {e.reference} {e.emergency_type.value} in {e.affected_area}: status {e.status.value}, "
                         f"priority {e.priority.value} (human-assigned), {open_tasks} open task(s)")
        return {"answer": "\n".join(lines), "data_period": f"as of {date.today()}",
                "sources": ["emergency_incidents", "emergency_tasks"], "suggestions": []}

    async def _emergency_gaps(self, j: Jurisdiction, q: str) -> dict:
        incidents = await self._active_emergencies(j)
        ids = [e.id for e in incidents]
        fac_ids = list((await self.session.execute(select(EmergencyAffectedFacility.facility_id).where(
            EmergencyAffectedFacility.incident_id.in_(ids)))).scalars().all()) if ids else []
        if not fac_ids:
            return {"answer": "No affected facilities are recorded for active emergencies.",
                    "data_period": f"as of {date.today()}", "sources": ["emergency_affected_facilities"], "suggestions": []}
        facilities = list((await self.session.execute(select(Facility).where(Facility.id.in_(fac_ids)))).scalars().all())
        snaps = await self.agg.facility_snapshots(facilities, date.today(), date.today())
        lines = [f"- {s['facility_name']}: {s['staff_present_today']}/{s['staff_assigned']} staff present, "
                 f"{s['stockout_items']} medicine(s) out of stock, {s['low_stock_items']} low" for s in snaps]
        gaps = [s for s in snaps if s["stockout_items"] or (s["staff_assigned"] and s["staff_present_today"] == 0)]
        return {"answer": "Affected facility gaps:\n" + "\n".join(lines), "data_period": f"{date.today()}",
                "sources": ["staff_attendance", "inventory_items"],
                "suggestions": ["Raise an emergency supply request to the DSCO for stock-outs."] if gaps else []}

    async def _emergency_escalation(self, j: Jurisdiction, q: str) -> dict:
        incidents = await self._active_emergencies(j)
        suggestions = []
        for e in incidents:
            affected = await self._count(select(func.count(EmergencyAffectedFacility.id)).where(
                EmergencyAffectedFacility.incident_id == e.id))
            severe = await self._count(select(func.count(EmergencyAffectedFacility.id)).where(
                EmergencyAffectedFacility.incident_id == e.id,
                EmergencyAffectedFacility.service_disruption.in_(["SEVERE", "CLOSED"])))
            age_h = (utcnow() - e.started_at.replace(tzinfo=e.started_at.tzinfo or utcnow().tzinfo)).total_seconds() / 3600
            reasons = []
            if affected >= 3:
                reasons.append(f"{affected} facilities affected (rule: ≥3)")
            if severe:
                reasons.append(f"{severe} facility(ies) severely disrupted")
            if age_h >= 48 and e.status.value != "ESCALATED":
                reasons.append(f"unresolved for {int(age_h)}h (rule: ≥48h)")
            if reasons:
                suggestions.append(f"{e.reference}: consider escalating to the DHO — " + "; ".join(reasons))
        answer = "\n".join(suggestions) if suggestions else "No active emergency meets the configured escalation rules."
        return {"answer": answer, "data_period": f"as of {date.today()}",
                "sources": ["emergency_incidents", "emergency_affected_facilities"],
                "suggestions": ["Escalation is a human decision; use the Escalate action if you agree."] if suggestions else []}

    # ------------------------------------------------------------------ analyst handlers
    async def _insights(self, j: Jurisdiction, q: str) -> dict:
        rows = (await self.session.execute(self._geo(j, select(AIInsight).where(
            AIInsight.review_status == InsightReviewStatus.PENDING_REVIEW).order_by(AIInsight.created_at.desc()).limit(8),
            AIInsight))).scalars().all()
        answer = ("Insights awaiting your review:\n" + "\n".join(f"- [{i.insight_type}] {i.observation}" for i in rows)) \
            if rows else "No insights are awaiting review. Run an analysis to check the latest period."
        return {"answer": answer, "data_period": rows[0].reporting_period if rows else None, "sources": ["ai_insights"],
                "suggestions": ["Review each insight's limitations before accepting it."] if rows else []}

    async def _data_quality(self, j: Jurisdiction, q: str) -> dict:
        rows = (await self.session.execute(self._geo(j, select(DataQualityIssue.issue_type, func.count()).where(
            DataQualityIssue.status.in_([DataQualityStatus.OPEN, DataQualityStatus.VERIFICATION_REQUESTED]))
            .group_by(DataQualityIssue.issue_type), DataQualityIssue))).all()
        answer = ("Open data-quality issues: " + "; ".join(f"{t.value}: {n}" for t, n in rows)) if rows \
            else "No open data-quality issues."
        return {"answer": answer, "data_period": f"as of {date.today()}", "sources": ["data_quality_issues"],
                "suggestions": ["Request verification from districts; do not edit source records."] if rows else []}
