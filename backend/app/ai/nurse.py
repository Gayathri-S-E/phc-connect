"""Nurse / Healthcare Staff AI Assistant configuration.

Workflow assistant only. There is deliberately NO tool to diagnose, assess, prescribe, approve or finalise anything,
and no pharmacy/admin tool. Patient and appointment access is checked against the nurse's facility scope on every call.
The single write is a nurse-confirmed vitals entry executed through the existing triage service (which keeps its audit)."""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.base import AssistantConfig, ToolContext, ToolError, ToolSpec, obj, parse_uuid
from app.ai.common_tools import navigation_tool
from app.ai.records import iso
from app.core.authorization import check_scope_access
from app.core.permissions import SystemPermissions as P
from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    Consultation,
    ConsultationStatus,
    Patient,
    Vitals,
)
from app.schemas.healthcare import VitalsCreate
from app.services.healthcare_service import HealthcareService

KEY = "NURSE"

ROLE_PROMPT = """\
ROLE: Workflow assistant for the signed-in NURSE / healthcare staff member at a PHC. You help with preparation, recording and documentation; the nurse and doctor make every clinical judgement. Audience: a nurse - short, practical, plain wording.

YOU MAY
- Show the OPD queue for the nurse's own facility (get_nursing_queue) with, per patient, whether vitals are already recorded and which are still missing; retrieve authorised patient information needed for preparation (allergies and chronic conditions as recorded, previously recorded vitals) and list what is MISSING.
- Prepare, for nurse confirmation, recording the vital signs the nurse tells you (temperature, blood pressure, pulse, respiratory rate, SpO2, height, weight) for a queued appointment, using propose_record_vitals.
- Draft nursing notes and handover summaries as plain text from what the nurse told you and what tools returned. A draft is text for the nurse to review and copy; nothing is saved by drafting.
- Show which patients have vitals recorded but the doctor's consultation still open (list_awaiting_doctor_review) - this is coordination information only.
- Help navigate Med2Us (use get_app_navigation; never name a screen it did not return).

YOU MUST NOT
- Diagnose, interpret vitals as a condition, decide urgency or triage level, suggest or comment on medicines/doses/treatment, or approve, sign off or finalise any clinical record. Never say a value is "normal", "abnormal" or "safe". If asked, say this is for the nurse's own protocol and the doctor, and offer to record or hand over the values exactly as given.
- Record any vital sign the nurse did not state. Never estimate, round, convert, correct, average or "fill in" a value. Use the exact numbers given. If a value looks impossible, ask the nurse to re-check it; the system also rejects out-of-range values.
- Invent patient details, history, appointments, tasks or results. If no tool returned it, say it is not available.
- Do doctor, pharmacy, lab-technician, supply-chain, PHC-in-charge or district work.
- Access any patient or appointment the tools refuse. If access is denied, tell the nurse plainly and do not work around it.

WHEN A VITAL SIGN SOUNDS ALARMING OR THE PATIENT SEEMS UNWELL: say first that the nurse should follow the facility's emergency escalation and alert the doctor immediately; it should not wait for this chat.

VITALS RECORDING: only after the nurse has given the values. Call propose_record_vitals with exactly those values and the appointment_id from the queue. Then show the values back and say NOTHING is saved until the nurse presses Confirm. Note that when vitals are saved, the existing system applies its own automatic triage rules, which can raise the appointment priority and mark a scheduled patient as checked in; do not predict or explain the outcome as a clinical decision.

NOT AVAILABLE IN THIS BUILD (say so honestly)
- There is no nursing task list, task assignment or shift-handover record in the backend. Do not invent tasks or claim to track them; you can only draft handover text for the nurse to keep elsewhere.
- There is no follow-up scheduling or monitoring record. You can only show vitals that were actually recorded; you cannot list patients due for follow-up or store a follow-up date.
- Nursing notes cannot be saved through this assistant; drafts are text only.
- No tool to prescribe, view pharmacy stock, message patients, or approve doctor records.

WORKFLOW: identify the task -> fetch only the data needed -> ask one concise question if something essential is missing -> keep recorded facts apart from your drafts ("Recorded:" vs "Draft:").
"""

REQUIRED_VITALS = ("temperature_celsius", "blood_pressure", "pulse_rate", "respiratory_rate", "spo2_percent")
_VALUE_FIELDS = ("temperature_celsius", "systolic_bp", "diastolic_bp", "pulse_rate", "respiratory_rate",
                 "spo2_percent", "height_cm", "weight_kg")
_LABELS = {"temperature_celsius": "Temperature", "systolic_bp": "Systolic BP", "diastolic_bp": "Diastolic BP",
           "pulse_rate": "Pulse", "respiratory_rate": "Respiratory rate", "spo2_percent": "SpO2",
           "height_cm": "Height", "weight_kg": "Weight"}
_UNITS = {"temperature_celsius": " C", "systolic_bp": " mmHg", "diastolic_bp": " mmHg", "pulse_rate": " /min",
          "respiratory_rate": " /min", "spo2_percent": " %", "height_cm": " cm", "weight_kg": " kg"}
_CLOSED = (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


async def _facility_scope(ctx: ToolContext) -> uuid.UUID:
    if ctx.user.facility_id is None:
        raise ToolError("Your account isn't linked to a facility, so I can't determine your queue or patient scope.")
    return ctx.user.facility_id


async def _authorised_patient(ctx: ToolContext, raw_id: Any) -> Patient:
    pid = parse_uuid(raw_id, "patient_id")
    patient = await HealthcareService(ctx.session).repo.get_patient_by_id(pid)
    if patient is None:
        raise ToolError("I couldn't find that patient.")
    await check_scope_access(ctx.user, patient.primary_facility_id, P.PATIENTS_PROFILE_READ, ctx.session)
    return patient


async def _authorised_appointment(ctx: ToolContext, raw_id: Any) -> Appointment:
    appt = await HealthcareService(ctx.session).repo.get_appointment_by_id(parse_uuid(raw_id, "appointment_id"))
    if appt is None:
        raise ToolError("I couldn't find that appointment.")
    await check_scope_access(ctx.user, appt.facility_id, P.PATIENTS_VITALS_RECORD, ctx.session)
    return appt


def _age(p: Patient) -> int:
    today = datetime.now(timezone.utc).date()
    d = p.date_of_birth
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


def _vitals_view(v: Any) -> Dict[str, Any]:
    return {"recorded_at": iso(v.recorded_at), "temperature_c": v.temperature_celsius,
            "bp": f"{v.systolic_bp}/{v.diastolic_bp}" if v.systolic_bp and v.diastolic_bp else None,
            "pulse": v.pulse_rate, "resp_rate": v.respiratory_rate, "spo2_percent": v.spo2_percent,
            "height_cm": v.height_cm, "weight_kg": v.weight_kg, "bmi": v.bmi}


def _missing(v: Any) -> List[str]:
    """Required vitals not present in a recorded vitals row (`v` may be None = nothing recorded)."""
    if v is None:
        return list(REQUIRED_VITALS)
    out = []
    if v.temperature_celsius is None:
        out.append("temperature_celsius")
    if v.systolic_bp is None or v.diastolic_bp is None:
        out.append("blood_pressure")
    for f in ("pulse_rate", "respiratory_rate", "spo2_percent"):
        if getattr(v, f) is None:
            out.append(f)
    return out


# ------------------------------------------------------------------ read tools
async def _queue(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    try:
        day = date.fromisoformat(str(args["date"])) if args.get("date") else datetime.now(timezone.utc).date()
    except ValueError:
        raise ToolError("Please give the date as YYYY-MM-DD.")
    items = await HealthcareService(ctx.session).get_doctor_opd_queue(facility_id=fid, doctor_id=None, target_date=day)
    rows = []
    for i in items[:30]:
        v = i.latest_vitals
        rows.append({
            "appointment_id": str(i.appointment_id), "patient_id": str(i.patient_id), "name": i.patient_name,
            "uhid": i.uhid, "age_years": i.age_years, "gender": i.gender, "token": i.token_number,
            "priority": i.priority, "status": i.status.value, "reason": i.reason, "time_slot": i.time_slot,
            "nursing_preparation": "VITALS_RECORDED" if v else "VITALS_PENDING",
            "latest_vitals": v.model_dump(mode="json", include=set(_VALUE_FIELDS) | {"bmi", "recorded_at"}) if v else None,
            "required_vitals_missing": _missing(v),
        })
    done = sum(1 for r in rows if r["nursing_preparation"] == "VITALS_RECORDED")
    return {"date": day.isoformat(), "patients_in_queue": len(items), "preparation_done": done,
            "preparation_pending": len(rows) - done, "queue_in_priority_order": rows,
            "note": "Order and priority come from the system's triage rules. Height and weight are optional and not counted as missing."}


async def _find_patient(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    q = str(args.get("query", "")).strip()[:80]
    if len(q) < 2:
        raise ToolError("Please give at least part of the patient's name or UHID.")
    fid = await _facility_scope(ctx)
    rows, total = await HealthcareService(ctx.session).search_patients(facility_id=fid, query=q, page_size=10)
    return {"matches": [{"patient_id": str(p.id), "name": f"{p.first_name} {p.last_name}", "uhid": p.patient_identifier,
                         "age_years": _age(p), "gender": p.gender} for p in rows],
            "total_matches": total, "note": "Searched only patients registered at your facility."}


async def _patient_preparation(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _authorised_patient(ctx, args.get("patient_id"))
    vit = (await ctx.session.execute(
        select(Vitals).join(Consultation, Vitals.consultation_id == Consultation.id)
        .where(Consultation.patient_id == p.id).order_by(Vitals.recorded_at.desc()).limit(5))).scalars().all()
    appts = (await ctx.session.execute(
        select(Appointment).where(Appointment.patient_id == p.id, Appointment.facility_id == p.primary_facility_id,
                                  Appointment.status.in_((AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN,
                                                          AppointmentStatus.IN_CONSULTATION)))
        .order_by(Appointment.appointment_date).limit(5))).scalars().all()
    return {"patient": {"patient_id": str(p.id), "name": f"{p.first_name} {p.last_name}", "uhid": p.patient_identifier,
                        "age_years": _age(p), "gender": p.gender, "blood_group": p.blood_group},
            "allergies_recorded": p.allergies, "chronic_conditions_recorded": p.chronic_conditions,
            "allergies_documented": bool(p.allergies),
            "open_appointments": [{"appointment_id": str(a.id), "date": iso(a.appointment_date), "token": a.token_number,
                                   "status": a.status.value, "priority": a.priority, "reason": a.reason} for a in appts],
            "previously_recorded_vitals_newest_first": [_vitals_view(v) for v in vit],
            "required_vitals_missing_in_latest_record": _missing(vit[0] if vit else None),
            "note": "Recorded values only. Absent values were not recorded; do not estimate them."}


async def _awaiting_doctor_review(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    fid = await _facility_scope(ctx)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    rows = (await ctx.session.execute(
        select(Consultation).where(Consultation.facility_id == fid, Consultation.status == ConsultationStatus.IN_PROGRESS,
                                   Consultation.started_at >= since, Consultation.vitals_records.any())
        .options(selectinload(Consultation.vitals_records), selectinload(Consultation.appointment))
        .order_by(Consultation.started_at.desc()).limit(40))).scalars().all()
    patients = {p.id: p for p in (await ctx.session.execute(
        select(Patient).where(Patient.id.in_({c.patient_id for c in rows})))).scalars().all()} if rows else {}
    out = []
    for c in rows:
        p = patients.get(c.patient_id)
        latest = max(c.vitals_records, key=lambda v: v.recorded_at)
        out.append({"consultation_id": str(c.id), "patient": f"{p.first_name} {p.last_name}" if p else None,
                    "uhid": p.patient_identifier if p else None,
                    "appointment_status": c.appointment.status.value if c.appointment else None,
                    "vitals_recorded_at": iso(latest.recorded_at), "doctor_consultation_status": c.status.value})
    return {"vitals_recorded_doctor_consultation_still_open": out, "period": "last 7 days", "count": len(out),
            "note": "Coordination view only: these consultations have recorded vitals and are not yet finalised by the doctor."}


# ------------------------------------------------------------------ action tool (prepare / execute)
def _validate_vitals(args: Dict[str, Any]) -> Dict[str, Any]:
    given = {k: args[k] for k in _VALUE_FIELDS if args.get(k) is not None}
    if any(isinstance(v, bool) for v in given.values()):
        raise ToolError("Vital sign values must be numbers.")
    if not given:
        raise ToolError("Tell me the vital signs you measured (temperature, BP, pulse, respiratory rate, SpO2, height, weight). "
                        "I only record values you give me.")
    try:
        model = VitalsCreate(**given)
    except ValidationError as exc:
        reasons = "; ".join(f"{_LABELS.get(str(e['loc'][0]), str(e['loc'][0]))}: {e['msg']}" for e in exc.errors())
        raise ToolError(f"These values were not accepted, so nothing was prepared ({reasons}). "
                        "Please re-check the measurement and give me the correct value.")
    if (model.systolic_bp is None) != (model.diastolic_bp is None):
        raise ToolError("Blood pressure needs both the systolic and the diastolic value.")
    if model.systolic_bp is not None and model.diastolic_bp is not None and model.diastolic_bp >= model.systolic_bp:
        raise ToolError("The diastolic BP is not lower than the systolic BP. Please re-check the reading; I did not prepare anything.")
    return {k: getattr(model, k) for k in _VALUE_FIELDS if getattr(model, k) is not None}


async def _prepare_vitals(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    appt = await _authorised_appointment(ctx, args.get("appointment_id"))
    if appt.status in _CLOSED:
        raise ToolError(f"This appointment is {appt.status.value}; vitals can't be recorded against it here.")
    values = _validate_vitals(args)
    patient = await HealthcareService(ctx.session).repo.get_patient_by_id(appt.patient_id)
    who = f"{patient.first_name} {patient.last_name} ({patient.patient_identifier})" if patient else "the patient"
    lines = [f"RECORD these nurse-measured vital signs for {who}, token {appt.token_number}:"]
    lines += [f"- {_LABELS[k]}: {values[k]}{_UNITS[k]}" for k in _VALUE_FIELDS if k in values]
    lines.append("Not provided (left empty): " + (", ".join(_LABELS[k] for k in _VALUE_FIELDS if k not in values) or "none"))
    lines.append("On saving, the existing system applies its own automatic triage rules; this can raise the queue priority "
                 "and mark a scheduled patient as checked in.")
    return {"summary": "\n".join(lines), "args": {"appointment_id": str(appt.id), **values}}


async def _execute_vitals(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    appt = await _authorised_appointment(ctx, args["appointment_id"])
    if appt.status in _CLOSED:
        raise ToolError(f"This appointment is now {appt.status.value}; vitals were not recorded.")
    payload = VitalsCreate(**{k: args[k] for k in _VALUE_FIELDS if args.get(k) is not None})
    vitals, done = await HealthcareService(ctx.session).record_nurse_triage_vitals(
        appointment_id=appt.id, vitals_data=payload, nurse_id=ctx.user.id, actor_id=ctx.user.id,
        ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"vitals_id": str(vitals.id), "appointment_id": str(done.id), "appointment_status": done.status.value,
            "queue_priority": done.priority,
            "message": f"The vital signs were recorded exactly as given. The appointment is now {done.status.value} "
                       f"with queue priority {done.priority} (set by the system's triage rules). "
                       "The doctor has not reviewed them yet."}


async def _context(ctx: ToolContext) -> str:
    return (f"- Nurse: {ctx.user.user.full_name}\n- Facility scope: "
            + (f"facility_id {ctx.user.facility_id}" if ctx.user.facility_id else "none linked"))


def _tools() -> Dict[str, ToolSpec]:
    vital_props = {
        "appointment_id": {"type": "string", "description": "From get_nursing_queue"},
        "temperature_celsius": {"type": "number"}, "systolic_bp": {"type": "integer"}, "diastolic_bp": {"type": "integer"},
        "pulse_rate": {"type": "integer"}, "respiratory_rate": {"type": "integer"}, "spo2_percent": {"type": "integer"},
        "height_cm": {"type": "number"}, "weight_kg": {"type": "number"},
    }
    specs = [
        ToolSpec("get_nursing_queue", "Today's (or a given date's) OPD queue for this nurse's facility in system triage order, "
                 "with each patient's recorded vitals and which required vitals are still missing.",
                 obj({"date": {"type": "string", "description": "YYYY-MM-DD, default today"}}), _queue,
                 "OPD queue (your facility)", P.APPOINTMENTS_VIEW),
        ToolSpec("find_patient", "Find patients registered at the nurse's facility by name or UHID. Returns patient_id values.",
                 obj({"query": {"type": "string"}}, ["query"]), _find_patient, "Patient register (your facility)", P.PATIENTS_PROFILE_READ),
        ToolSpec("get_patient_preparation", "Preparation info for ONE authorised patient: recorded allergies and conditions, open "
                 "appointments, previously recorded vitals and missing required vitals.",
                 obj({"patient_id": {"type": "string"}}, ["patient_id"]), _patient_preparation,
                 "Patient record (nursing view)", P.PATIENTS_PROFILE_READ),
        ToolSpec("list_awaiting_doctor_review", "Consultations in this facility (last 7 days) that have vitals recorded but which "
                 "the doctor has not finalised yet.", obj(), _awaiting_doctor_review, "Consultation status", P.APPOINTMENTS_VIEW),
        navigation_tool(frozenset({"clinical"})),
        ToolSpec("propose_record_vitals", "Prepare (NOT perform) recording vital signs the nurse measured, exactly as given, for a "
                 "queued appointment. Include ONLY values the nurse stated. The nurse must press Confirm.",
                 obj(vital_props, ["appointment_id"]), _prepare_vitals, "Triage vitals record", P.PATIENTS_VITALS_RECORD,
                 kind="action", execute=_execute_vitals),
    ]
    return {s.name: s for s in specs}


NURSE_ASSISTANT = AssistantConfig(
    key=KEY, title="Nurse AI Assistant", role_codes=frozenset({"NURSE"}), permission=P.CLINICAL_AI_ADVISORY,
    role_prompt=ROLE_PROMPT, tools=_tools(), context_loader=_context,
    starters={
        "en": ["Who is waiting for nursing assessment today?", "Which patients still need vitals recorded?",
               "Show this patient's previous vitals", "Draft a handover summary from what I tell you"],
        "ta": ["இன்று செவிலியர் மதிப்பீட்டிற்காக காத்திருப்பவர்கள் யார்?", "யாருக்கு இன்னும் முக்கிய அறிகுறிகள் பதிவாகவில்லை?",
               "இந்த நோயாளியின் முந்தைய அளவீடுகளைக் காட்டுங்கள்", "நான் சொல்வதிலிருந்து ஒப்படைப்புச் சுருக்கம் வரைக"],
        "hi": ["आज नर्सिंग जाँच के लिए कौन प्रतीक्षा में है?", "किन मरीज़ों के वाइटल्स दर्ज होने बाकी हैं?",
               "इस मरीज़ के पिछले वाइटल्स दिखाइए", "मेरे बताए अनुसार हैंडओवर सारांश का मसौदा बनाइए"],
    },
)
