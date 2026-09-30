"""Doctor / Medical Officer AI Assistant configuration.

Clinical workflow assistant only. There is deliberately NO tool to prescribe, choose medicines or doses, diagnose,
or approve anything. Patient data access is checked against the doctor's facility scope on every call, and every
write is a doctor-confirmed action executed through the existing clinical services (which keep their own audit)."""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.base import AssistantConfig, ToolContext, ToolError, ToolSpec, obj, parse_uuid
from app.ai.common_tools import navigation_tool
from app.ai.records import aware, consultation_view, iso
from app.core.authorization import check_scope_access
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import SystemPermissions as P
from app.models.healthcare import (
    Consultation,
    ConsultationStatus,
    LabOrder,
    LabOrderStatus,
    Patient,
    Referral,
    ReferralStatus,
)
from app.schemas.healthcare import (
    ConsultationFinalizeRequest,
    DiagnosisCreate,
    LabOrderCreate,
    ReferralCreate,
)
from app.services.healthcare_service import HealthcareService

KEY = "DOCTOR"

ROLE_PROMPT = """\
ROLE: Clinical workflow assistant for the signed-in DOCTOR / MEDICAL OFFICER at a PHC. You assist; the doctor decides. Audience: a physician - be concise and professional, plain clinical wording, no lecturing.

YOU MAY
- Show today's consultation queue and the doctor's pending work; retrieve and summarise records of patients this doctor is authorised to see (history, allergies, previous consultations, vitals, labs, prescriptions, referrals) and point out MISSING information.
- Explain medical terms and general clinical concepts when asked, clearly marked as general information, not as a finding about this patient.
- Organise what the doctor tells you (symptoms, findings, assessment, plan) into structured notes and patient-friendly summaries. Drafts are text for the doctor to review; nothing is saved until the doctor confirms a prepared request.
- Prepare, for doctor confirmation: finalising a consultation with the doctor's own notes/findings/diagnoses, a lab order, or a referral - using ONLY details the doctor gave you.
- Help navigate Med2Us (use get_app_navigation; never name a screen it did not return).

YOU MUST NOT
- Diagnose, confirm a diagnosis, choose or suggest medicines, doses, durations, substitutions, or modify treatment; approve prescriptions, investigations or referrals; decide who to refer or what to order. If asked, say those are the doctor's decisions and offer to document what the doctor decides.
- Invent symptoms, findings, results, history, diagnoses or ICD codes. If the doctor did not provide it and no tool returned it, leave it out and list it as missing. Never present an unconfirmed condition as a confirmed diagnosis.
- Assume a patient recovered, took medicine or followed advice unless a record says so.
- Do PHC-in-charge, district, supply-chain, pharmacy-inventory or other roles' work, or manage stock/procurement.
- Access any patient the tools refuse. If a tool says access is denied, tell the doctor plainly and do not try to work around it.

CLINICAL SAFETY: Keep verified records apart from your own explanations ("Recorded:" vs "General note:"). State uncertainty and gaps. If a described situation sounds like an emergency, say first that standard emergency escalation at the facility should not wait for this chat. Anything shared with patients needs the doctor's review first.

NOT AVAILABLE IN THIS BUILD (say so honestly)
- There is no follow-up scheduling/tracking record in the backend, so you cannot list patients due for follow-up or store a follow-up date as structured data; you can include a follow-up instruction in the consultation notes the doctor approves.
- No tool to create prescriptions, view pharmacy stock, or message patients.
- Investigation "results awaiting review" are limited to the lab orders and results the tools return.

WORKFLOW: identify the task -> fetch only the data needed -> if information is missing, ask one concise question -> present records vs. drafts separately -> for anything that changes data, prepare the request and tell the doctor to review the summary and press Confirm. Before preparing a finalisation, show the drafted note so the doctor can correct it.
"""


async def _facility_scope(ctx: ToolContext) -> uuid.UUID:
    if ctx.user.facility_id is None:
        raise ToolError("Your account isn't linked to a facility, so I can't determine your queue or patient scope.")
    return ctx.user.facility_id


async def _authorised_patient(ctx: ToolContext, raw_id: Any) -> Patient:
    """Same rule as the clinical-history API: the patient's home facility must be inside the doctor's scope."""
    pid = parse_uuid(raw_id, "patient_id")
    patient = await HealthcareService(ctx.session).repo.get_patient_by_id(pid)
    if patient is None:
        raise ToolError("I couldn't find that patient.")
    await check_scope_access(ctx.user, patient.primary_facility_id, P.PATIENTS_RECORDS_READ, ctx.session)
    return patient


def _age(p: Patient) -> int:
    today = datetime.now(timezone.utc).date()
    d = p.date_of_birth
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


def _person(p: Patient) -> Dict[str, Any]:
    return {"patient_id": str(p.id), "name": f"{p.first_name} {p.last_name}", "uhid": p.patient_identifier,
            "age_years": _age(p), "gender": p.gender}


# ------------------------------------------------------------------ read tools
async def _queue(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    try:
        day = date.fromisoformat(str(args["date"])) if args.get("date") else datetime.now(timezone.utc).date()
    except ValueError:
        raise ToolError("Please give the date as YYYY-MM-DD.")
    items = await HealthcareService(ctx.session).get_doctor_opd_queue(facility_id=fid, doctor_id=ctx.user.id, target_date=day)
    return {"date": day.isoformat(), "patients_in_queue": len(items),
            "queue_in_priority_order": [{
                "patient_id": str(i.patient_id), "name": i.patient_name, "uhid": i.uhid, "age_years": i.age_years,
                "gender": i.gender, "token": i.token_number, "priority": i.priority, "status": i.status.value,
                "reason": i.reason, "time_slot": i.time_slot,
                "latest_vitals": i.latest_vitals.model_dump(mode="json") if i.latest_vitals else None,
            } for i in items[:25]],
            "note": "Order is EMERGENCY, PRIORITY, then token number, as set by the system's triage rules."}


async def _find_patient(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    q = str(args.get("query", "")).strip()[:80]
    if len(q) < 2:
        raise ToolError("Please give at least part of the patient's name or UHID.")
    fid = await _facility_scope(ctx)
    rows, total = await HealthcareService(ctx.session).search_patients(facility_id=fid, query=q, page_size=10)
    return {"matches": [_person(p) for p in rows], "total_matches": total,
            "note": "Searched only patients registered at your facility."}


async def _overview(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _authorised_patient(ctx, args.get("patient_id"))
    consultations = list(await HealthcareService(ctx.session).repo.list_consultations_by_patient(p.id))
    return {"patient": {**_person(p), "blood_group": p.blood_group, "allergies_recorded": p.allergies,
                        "chronic_conditions_recorded": p.chronic_conditions},
            "allergies_documented": bool(p.allergies), "total_consultations": len(consultations),
            "consultations_newest_first": [consultation_view(c, with_gaps=True) for c in consultations[:5]]}


async def _open_documentation(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    since = datetime.now(timezone.utc) - timedelta(days=30)
    rows = (await ctx.session.execute(
        select(Consultation).where(Consultation.doctor_id == ctx.user.id, Consultation.facility_id == fid,
                                   Consultation.started_at >= since)
        .options(selectinload(Consultation.diagnoses), selectinload(Consultation.vitals_records))
        .order_by(Consultation.started_at.desc()).limit(40))).scalars().all()
    patients = {p.id: p for p in (await ctx.session.execute(
        select(Patient).where(Patient.id.in_({c.patient_id for c in rows})))).scalars().all()} if rows else {}
    out: List[Dict[str, Any]] = []
    for c in rows:
        gaps = [g for g, missing in (("clinical_notes", not c.clinical_notes), ("examination_findings", not c.examination_findings),
                                     ("diagnoses", not c.diagnoses)) if missing]
        if c.status == ConsultationStatus.IN_PROGRESS or (c.status == ConsultationStatus.FINALIZED and gaps):
            p = patients.get(c.patient_id)
            out.append({"consultation_id": str(c.id), "patient": f"{p.first_name} {p.last_name}" if p else None,
                        "uhid": p.patient_identifier if p else None, "status": c.status.value, "started": iso(c.started_at),
                        "chief_complaint": c.chief_complaint, "missing_fields": gaps})
    return {"needing_attention": out, "period": "last 30 days"}


async def _my_labs(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    orders = (await ctx.session.execute(
        select(LabOrder).where(LabOrder.ordered_by_doctor_id == ctx.user.id, LabOrder.facility_id == fid)
        .options(selectinload(LabOrder.results), selectinload(LabOrder.patient))
        .order_by(LabOrder.ordered_at.desc()).limit(40))).scalars().all()
    def row(o: LabOrder) -> Dict[str, Any]:
        return {"lab_order_id": str(o.id), "patient": f"{o.patient.first_name} {o.patient.last_name}", "uhid": o.patient.patient_identifier,
                "test": o.test_category, "status": o.status.value, "ordered_at": iso(o.ordered_at),
                "results": [{"test": r.test_name, "value": r.result_value, "unit": r.unit, "reference_range": r.reference_range,
                             "flagged_abnormal_by_lab": r.is_abnormal, "critical_alert": r.critical_alert,
                             "verified": r.verified_by_id is not None} for r in o.results]}
    open_states = (LabOrderStatus.ORDERED, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_ANALYSIS)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    return {"pending_orders": [row(o) for o in orders if o.status in open_states],
            "completed_last_14_days": [row(o) for o in orders if o.status == LabOrderStatus.COMPLETED
                                       and o.completed_at and aware(o.completed_at) >= cutoff]}


async def _my_referrals(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    refs = (await ctx.session.execute(
        select(Referral).where(Referral.referred_by_doctor_id == ctx.user.id, Referral.from_facility_id == fid)
        .order_by(Referral.created_at.desc()).limit(30))).scalars().all()
    patients = {p.id: p for p in (await ctx.session.execute(
        select(Patient).where(Patient.id.in_({r.patient_id for r in refs})))).scalars().all()} if refs else {}
    return {"referrals": [{
        "referral_id": str(r.id), "patient": (f"{patients[r.patient_id].first_name} {patients[r.patient_id].last_name}"
                                             if r.patient_id in patients else None),
        "to": r.to_facility_name, "reason": r.referral_reason, "urgency": r.urgency.value, "status": r.status.value,
        "created_at": iso(r.created_at), "awaiting_outcome": r.status in (ReferralStatus.PENDING, ReferralStatus.ACCEPTED),
    } for r in refs]}


# ------------------------------------------------------------------ action tools (prepare / execute)
async def _own_consultation(ctx: ToolContext, raw_id: Any) -> Consultation:
    c = await HealthcareService(ctx.session).repo.get_consultation_by_id(parse_uuid(raw_id, "consultation_id"))
    if c is None or c.doctor_id != ctx.user.id:
        raise PermissionDeniedException("You can only change consultations that you conducted.")
    await check_scope_access(ctx.user, c.facility_id, P.CONSULTATIONS_CONDUCT, ctx.session)
    return c


def _clean(value: Any, limit: int = 4000) -> Any:
    return str(value).strip()[:limit] if value not in (None, "") else None


def _parse_diagnoses(raw: Any) -> List[DiagnosisCreate]:
    out: List[DiagnosisCreate] = []
    for d in (raw if isinstance(raw, list) else []):
        try:
            out.append(DiagnosisCreate(**d))
        except Exception:
            raise ToolError("Each diagnosis needs an ICD-10 code and a condition name that you (the doctor) have stated. "
                            "I can't fill these in for you.")
    return out


async def _prepare_finalize(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args.get("consultation_id"))
    if c.status != ConsultationStatus.IN_PROGRESS:
        raise ToolError(f"This consultation is {c.status.value}; finalised records can't be changed through this assistant.")
    notes, findings = _clean(args.get("clinical_notes")), _clean(args.get("examination_findings"))
    diagnoses = _parse_diagnoses(args.get("diagnoses"))
    if not (notes or findings or diagnoses):
        raise ToolError("There's nothing to save yet. Tell me the notes, examination findings or diagnoses you want recorded.")
    lines = ["FINALISE this consultation with the following doctor-provided content (it cannot be edited afterwards here):"]
    lines.append(f"Clinical notes: {notes or '(none provided)'}")
    lines.append(f"Examination findings: {findings or '(none provided)'}")
    lines.append("Diagnoses: " + ("; ".join(f"{d.condition_name} [{d.icd10_code}] ({d.diagnosis_type.value})" for d in diagnoses)
                                  or "(none provided)"))
    return {"summary": "\n".join(lines), "args": {
        "consultation_id": str(c.id), "clinical_notes": notes, "examination_findings": findings,
        "diagnoses": [d.model_dump(mode="json") for d in diagnoses]}}


async def _execute_finalize(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args["consultation_id"])
    payload = ConsultationFinalizeRequest(clinical_notes=args.get("clinical_notes"),
                                          examination_findings=args.get("examination_findings"),
                                          diagnoses=_parse_diagnoses(args.get("diagnoses")) or None)
    done = await HealthcareService(ctx.session).finalize_consultation(
        c.id, payload, doctor_id=ctx.user.id, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"consultation_id": str(done.id), "status": done.status.value,
            "message": f"The consultation is now {done.status.value} in the system."}


async def _prepare_lab(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args.get("consultation_id"))
    test = _clean(args.get("test_category"), 100)
    if not test or len(test) < 2:
        raise ToolError("Which test do you want to order? I only record the test you name; I don't choose investigations.")
    notes = _clean(args.get("clinical_notes"), 1000)
    return {"summary": f"Order lab test '{test}' for this consultation." + (f" Clinical notes for the lab: {notes}" if notes else ""),
            "args": {"consultation_id": str(c.id), "test_category": test, "clinical_notes": notes}}


async def _execute_lab(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args["consultation_id"])
    order = await HealthcareService(ctx.session).create_lab_order(
        LabOrderCreate(consultation_id=c.id, test_category=args["test_category"], clinical_notes=args.get("clinical_notes")),
        doctor_id=ctx.user.id, facility_id=c.facility_id, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"lab_order_id": str(order.id), "status": order.status.value,
            "message": f"Lab order '{order.test_category}' was created with status {order.status.value}."}


async def _prepare_referral(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args.get("consultation_id"))
    to = _clean(args.get("to_facility_name"), 255)
    reason = _clean(args.get("referral_reason"), 1500)
    if not to or not reason:
        raise ToolError("I need the receiving facility and your referral reason. I don't decide where to refer.")
    urgency = str(args.get("urgency", "ROUTINE")).upper()
    if urgency not in ("ROUTINE", "URGENT", "EMERGENCY"):
        raise ToolError("Urgency must be ROUTINE, URGENT or EMERGENCY, as you decide.")
    summary = _clean(args.get("clinical_summary"), 2000)
    return {"summary": f"Create a {urgency} referral to {to}. Reason: {reason}." + (f" Clinical summary: {summary}" if summary else ""),
            "args": {"consultation_id": str(c.id), "to_facility_name": to, "referral_reason": reason,
                     "urgency": urgency, "clinical_summary": summary}}


async def _execute_referral(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    c = await _own_consultation(ctx, args["consultation_id"])
    ref = await HealthcareService(ctx.session).create_referral(
        ReferralCreate(**{k: v for k, v in args.items() if v is not None}), doctor_id=ctx.user.id,
        from_facility_id=c.facility_id, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"referral_id": str(ref.id), "status": ref.status.value,
            "message": f"Referral to {ref.to_facility_name} was created with status {ref.status.value}. "
                       "Acceptance by the receiving facility has not been confirmed."}


async def _context(ctx: ToolContext) -> str:
    return (f"- Doctor: {ctx.user.user.full_name}\n- Facility scope: "
            + (f"facility_id {ctx.user.facility_id}" if ctx.user.facility_id else "none linked"))


def _tools() -> Dict[str, ToolSpec]:
    specs = [
        ToolSpec("get_my_consultation_queue", "Today's (or a given date's) OPD queue for this doctor's facility, in system triage order.",
                 obj({"date": {"type": "string", "description": "YYYY-MM-DD, default today"}}), _queue,
                 "OPD consultation queue", P.APPOINTMENTS_VIEW),
        ToolSpec("find_patient", "Find patients registered at the doctor's facility by name or UHID. Returns patient_id values.",
                 obj({"query": {"type": "string"}}, ["query"]), _find_patient, "Patient register (your facility)", P.PATIENTS_PROFILE_READ),
        ToolSpec("get_patient_overview", "Record summary for ONE patient the doctor is authorised to see: allergies, conditions, "
                 "recent consultations with vitals, labs, prescriptions, referrals and missing fields.",
                 obj({"patient_id": {"type": "string"}}, ["patient_id"]), _overview, "Patient clinical record", P.PATIENTS_RECORDS_READ),
        ToolSpec("list_open_documentation", "This doctor's consultations from the last 30 days that are still in progress or finalised "
                 "with missing fields.", obj(), _open_documentation, "Your consultations", P.CONSULTATIONS_CONDUCT),
        ToolSpec("list_my_lab_orders", "Lab orders placed by this doctor: pending ones and those completed in the last 14 days, "
                 "with results and lab flags.", obj(), _my_labs, "Lab orders and results", P.LABS_ORDER_READ),
        ToolSpec("list_my_referrals", "Referrals created by this doctor with their actual status.", obj(), _my_referrals,
                 "Referral records", P.REFERRALS_READ),
        navigation_tool(frozenset({"clinical"})),
        ToolSpec("propose_finalize_consultation", "Prepare (NOT perform) finalising one of the doctor's IN_PROGRESS consultations "
                 "using ONLY notes, findings and diagnoses the doctor has stated. The doctor must press Confirm.",
                 obj({"consultation_id": {"type": "string"}, "clinical_notes": {"type": "string"},
                      "examination_findings": {"type": "string"},
                      "diagnoses": {"type": "array", "items": obj({
                          "icd10_code": {"type": "string"}, "condition_name": {"type": "string"},
                          "diagnosis_type": {"type": "string", "description": "PRIMARY, SECONDARY or PROVISIONAL"},
                          "notes": {"type": "string"}}, ["icd10_code", "condition_name"])}}, ["consultation_id"]),
                 _prepare_finalize, "Consultation record", P.CONSULTATIONS_CONDUCT, kind="action", execute=_execute_finalize),
        ToolSpec("propose_lab_order", "Prepare (NOT perform) a lab order for a test the doctor named. The doctor must press Confirm.",
                 obj({"consultation_id": {"type": "string"}, "test_category": {"type": "string"}, "clinical_notes": {"type": "string"}},
                     ["consultation_id", "test_category"]),
                 _prepare_lab, "Lab order", P.LABS_ORDER_CREATE, kind="action", execute=_execute_lab),
        ToolSpec("propose_referral", "Prepare (NOT perform) a referral using the facility, reason and urgency the doctor decided. "
                 "The doctor must press Confirm.",
                 obj({"consultation_id": {"type": "string"}, "to_facility_name": {"type": "string"},
                      "referral_reason": {"type": "string"}, "urgency": {"type": "string", "description": "ROUTINE, URGENT or EMERGENCY"},
                      "clinical_summary": {"type": "string"}}, ["consultation_id", "to_facility_name", "referral_reason"]),
                 _prepare_referral, "Referral", P.REFERRALS_CREATE, kind="action", execute=_execute_referral),
    ]
    return {s.name: s for s in specs}


DOCTOR_ASSISTANT = AssistantConfig(
    key=KEY, title="Doctor AI Assistant", role_codes=frozenset({"DOCTOR"}), permission=P.CLINICAL_AI_ADVISORY,
    role_prompt=ROLE_PROMPT, tools=_tools(), context_loader=_context,
    starters={
        "en": ["Who is waiting for consultation today?", "Which of my consultations are incomplete?",
               "Any lab results or referrals I should check?", "Summarise this patient's previous visits"],
        "ta": ["இன்று ஆலோசனைக்காக காத்திருப்பவர்கள் யார்?", "என் முடிக்கப்படாத ஆலோசனைகள் எவை?",
               "நான் பார்க்க வேண்டிய ஆய்வக முடிவுகள் அல்லது பரிந்துரைகள் உள்ளனவா?", "இந்த நோயாளியின் முந்தைய வருகைகளைச் சுருக்கவும்"],
        "hi": ["आज परामर्श के लिए कौन प्रतीक्षा में है?", "मेरे कौन से परामर्श अधूरे हैं?", "कोई लैब रिज़ल्ट या रेफ़रल देखने हैं?",
               "इस मरीज़ की पिछली विज़िट का सार बताइए"],
    },
)
