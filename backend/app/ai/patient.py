"""Patient AI Assistant configuration. Every tool resolves the patient from the authenticated user, never from
an identifier the model or the user supplies, so one patient can never reach another patient's data."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import or_, select

from app.ai.base import IST, AssistantConfig, ToolContext, ToolError, ToolSpec, now_ist, obj, parse_uuid
from app.ai.common_tools import navigation_tool
from app.ai.records import aware, consultation_view, iso
from app.core.permissions import SystemPermissions as P
from app.integrations.google.errors import GoogleError
from app.integrations.google.maps import FacilityPoint, get_maps_client, rank_nearest
from app.models.facility import Facility, FacilityType
from app.models.healthcare import Appointment, AppointmentStatus, Patient
from app.schemas.healthcare import AppointmentCreate, AppointmentStatusUpdate
from app.services.healthcare_service import HealthcareService

KEY = "PATIENT"
ACTIVE_STATES = (AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN, AppointmentStatus.IN_CONSULTATION)
CANCELLABLE = (AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN)
PATIENT_FACILITY_TYPES = (FacilityType.PHC, FacilityType.CHC, FacilityType.DISTRICT_HOSPITAL)
MAX_BOOKING_DAYS_AHEAD = 90

ROLE_PROMPT = """\
ROLE: Personal healthcare information and help companion for the signed-in PATIENT. Audience: people with no medical background.

YOU MAY
- Give safe health education in simple words: nutrition, hydration, sleep, hygiene, activity, prevention, common symptoms and warning signs, how to prepare for a visit. Say when to see a health professional.
- Explain the patient's OWN records (history, reports, lab values with the reference ranges the lab supplied, prescriptions as recorded) using the tools. Separate "what your record says" from "general information".
- Help with appointments: view, track status, book and cancel (through confirmed requests), and with finding PHCs/facilities.
- Help use the Med2Us app (use get_app_navigation; never name a screen it did not return).

YOU MUST NOT
- Diagnose, name a disease from symptoms or lab values, prescribe, change dose/frequency/duration, suggest substitutions, or decide treatment. For medicine doubts, overdose, side effects or conflicting instructions: give cautious guidance and send them to their doctor/pharmacist, or to emergency care if severe.
- Say a medicine is "available"; you only know the fulfilment status the prescriptions tool returns.
- Pressure anyone into tests, medicines or services.
- Show anything about other patients, staff, stock, supply chain, or any admin/doctor/nurse/pharmacist function.

EMERGENCIES: for anything that sounds life-threatening (chest pain, trouble breathing, stroke signs, heavy bleeding, unconsciousness, seizure, poisoning, thoughts of self-harm) put emergency guidance first: call 108 or go to the nearest emergency department now. Do not continue with routine booking. Do not claim you contacted anyone.

NOT AVAILABLE IN THIS BUILD (say so honestly instead of pretending)
- Live free-slot lists: the system takes a preferred date/time and assigns a token number when booking is confirmed.
- One-step rescheduling: offer to book the new appointment first, then cancel the old one; each needs its own Confirm.
- Facility phone numbers and opening hours (not stored) and vaccination-record screens (only what appears in records).
- Editing profile or clinical records in chat: profile changes go through the profile page; clinical corrections go through the facility.

BOOKING FLOW: understand the purpose -> pick the facility (their primary facility is in the context; use find_facilities for others) -> ask preferred date/time if missing -> call propose_book_appointment -> tell them the summary and to press Confirm.
For cancelling: list appointments if the user doesn't say which one, then call propose_cancel_appointment.
"""


async def _patient(ctx: ToolContext) -> Patient:
    cached = ctx.state.get("patient")
    if cached is not None:
        return cached
    patient = await HealthcareService(ctx.session).get_patient_by_user_id(ctx.user.id)
    if patient is None:
        raise ToolError("No patient profile is linked to this account, so I can't look up personal records.")
    ctx.state["patient"] = patient
    return patient


async def _facility_names(ctx: ToolContext, ids: List[uuid.UUID]) -> Dict[uuid.UUID, str]:
    if not ids:
        return {}
    rows = (await ctx.session.execute(select(Facility.id, Facility.name).where(Facility.id.in_(set(ids))))).all()
    return {r[0]: r[1] for r in rows}


def _appt_view(a: Appointment, names: Dict[uuid.UUID, str]) -> Dict[str, Any]:
    return {
        "appointment_id": str(a.id), "date_time": iso(a.appointment_date), "time_slot": a.time_slot,
        "facility": names.get(a.facility_id, "Unknown facility"), "facility_id": str(a.facility_id),
        "token_number": a.token_number, "status": a.status.value, "reason": a.reason, "priority": a.priority,
        "cancellation_reason": a.cancellation_reason,
    }


# ------------------------------------------------------------------ read tools
async def _profile(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _patient(ctx)
    today = datetime.now(timezone.utc).date()
    age = today.year - p.date_of_birth.year - ((today.month, today.day) < (p.date_of_birth.month, p.date_of_birth.day))
    names = await _facility_names(ctx, [p.primary_facility_id])
    return {"name": f"{p.first_name} {p.last_name}", "patient_id_number": p.patient_identifier, "age_years": age,
            "gender": p.gender, "blood_group": p.blood_group, "allergies_recorded": p.allergies,
            "chronic_conditions_recorded": p.chronic_conditions, "preferred_language": p.preferred_language,
            "primary_facility": names.get(p.primary_facility_id), "primary_facility_id": str(p.primary_facility_id)}


async def _appointments(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _patient(ctx)
    which = str(args.get("which", "all")).lower()
    rows, _ = await HealthcareService(ctx.session).list_appointments(patient_id=p.id, page_size=100)
    names = await _facility_names(ctx, [a.facility_id for a in rows])
    now = datetime.now(timezone.utc)
    upcoming = sorted([a for a in rows if a.status in ACTIVE_STATES and aware(a.appointment_date) >= now - timedelta(hours=12)],
                      key=lambda a: aware(a.appointment_date))
    upcoming_ids = {a.id for a in upcoming}
    past = sorted([a for a in rows if a.id not in upcoming_ids], key=lambda a: aware(a.appointment_date), reverse=True)
    out: Dict[str, Any] = {}
    if which in ("upcoming", "all"):
        out["upcoming"] = [_appt_view(a, names) for a in upcoming]
    if which in ("past", "all"):
        out["past_or_closed"] = [_appt_view(a, names) for a in past[:10]]
    out["note"] = ("Statuses are exactly as recorded by the system: SCHEDULED, CHECKED_IN, IN_CONSULTATION, COMPLETED, "
                   "CANCELLED, NO_SHOW. There is no separate 'pending/confirmed' state.")
    return out


async def _records(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _patient(ctx)
    consultations = await HealthcareService(ctx.session).repo.list_consultations_by_patient(p.id)
    return {"consultations_newest_first": [consultation_view(c) for c in list(consultations)[:8]],
            "total_consultations": len(consultations),
            "note": "Lab flags and reference ranges come from the lab. Do not interpret them as a diagnosis."}


async def _prescriptions(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _patient(ctx)
    items = await HealthcareService(ctx.session).get_patient_prescriptions_fulfillment(p.id)
    return {"prescriptions_newest_first": [i.model_dump(mode="json") for i in items[:8]],
            "note": "fulfillment_status is the only availability information you have; it is not stock data."}


async def _notifications(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    p = await _patient(ctx)
    rows = await HealthcareService(ctx.session).list_patient_notifications(p.id)
    ta = ctx.language == "ta"
    return {"notifications": [{"title": n.title_ta if ta else n.title_en, "message": n.message_ta if ta else n.message_en,
                               "type": n.notification_type, "read": n.is_read, "created_at": iso(n.created_at)}
                              for n in list(rows)[:10]]}


async def _education(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    category = args.get("category")
    slides = await HealthcareService(ctx.session).list_health_awareness_slides(category=str(category).upper() if category else None)
    ta = ctx.language == "ta"
    return {"verified_awareness_cards": [{"category": s.category, "title": s.title_ta if ta else s.title_en,
                                          "tip": s.tip_ta if ta else s.tip_en, "action": s.action_ta if ta else s.action_en}
                                         for s in list(slides)[:6]]}


async def _facilities(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    stmt = select(Facility).where(Facility.is_active.is_(True), Facility.facility_type.in_(PATIENT_FACILITY_TYPES))
    q = str(args.get("query", "")).strip()[:80]
    if q:
        like = f"%{q.lower()}%"
        from sqlalchemy import func
        stmt = stmt.where(or_(func.lower(Facility.name).like(like), func.lower(Facility.district).like(like),
                              func.lower(Facility.address).like(like)))
    rows = (await ctx.session.execute(stmt.order_by(Facility.name).limit(10))).scalars().all()
    return {"facilities": [{"facility_id": str(f.id), "name": f.name, "type": f.facility_type.value, "district": f.district,
                            "state": f.state, "address": f.address,
                            "latitude": float(f.latitude) if f.latitude is not None else None,
                            "longitude": float(f.longitude) if f.longitude is not None else None} for f in rows],
            "not_recorded_in_system": ["phone number", "opening hours", "services list"]}


async def _nearest_facilities(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """Uses a location only when the patient gave one in this conversation (address or coordinates)."""
    maps = get_maps_client()
    lat, lng, label = args.get("latitude"), args.get("longitude"), None
    if lat is None or lng is None:
        address = str(args.get("address", "")).strip()[:200]
        if not address:
            raise ToolError("Tell me your area, pincode or address (or share your location) and I'll find the nearest centres.")
        if not maps.is_configured():
            raise ToolError("Address search isn't set up on this server. You can search a facility by name or district instead.")
        try:
            hit = await maps.geocode(address)
        except GoogleError:
            raise ToolError("I couldn't look up that address right now. Please try a facility name or district instead.")
        if hit is None:
            raise ToolError("I couldn't find that address. Please give a nearby town, area or pincode.")
        lat, lng, label = hit
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        raise ToolError("Those coordinates don't look valid.")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ToolError("Those coordinates don't look valid.")
    rows = (await ctx.session.execute(select(Facility).where(
        Facility.is_active.is_(True), Facility.facility_type.in_(PATIENT_FACILITY_TYPES),
        Facility.latitude.is_not(None), Facility.longitude.is_not(None)))).scalars().all()
    points = [FacilityPoint(str(f.id), f.name, f.code, f.facility_type.value, f.state, f.district,
                            float(f.latitude), float(f.longitude)) for f in rows]
    method, ranked = await rank_nearest(maps, lat, lng, points, 5)
    return {"searched_near": label or "the location you gave", "ranking_method": method,
            "facilities": [{"facility_id": r["facility"].id, "name": r["facility"].name, "type": r["facility"].facility_type,
                            "district": r["facility"].district, "straight_line_km": r["straight_line_km"],
                            "driving_km": r["driving_distance_km"], "driving_minutes": r["driving_minutes"]}
                           for r in ranked[:5]],
            "note": "haversine_only means straight-line distance, not travel time. Facilities without coordinates are not listed."}


# ------------------------------------------------------------------ action tools (prepare / execute)
def _parse_when(raw: Any) -> datetime:
    try:
        when = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        raise ToolError("I couldn't read that date and time. Please give it like 2026-10-05 10:30.")
    return when if when.tzinfo else when.replace(tzinfo=IST)


async def _check_booking(ctx: ToolContext, patient: Patient, facility_id: uuid.UUID, when: datetime) -> Facility:
    facility = (await ctx.session.execute(select(Facility).where(Facility.id == facility_id))).scalar_one_or_none()
    if facility is None or not facility.is_active or facility.facility_type not in PATIENT_FACILITY_TYPES:
        raise ToolError("That facility isn't available for patient bookings. Please choose one from the facility list.")
    now = datetime.now(timezone.utc)
    if when <= now:
        raise ToolError("That time has already passed. Please choose a future date and time.")
    if when > now + timedelta(days=MAX_BOOKING_DAYS_AHEAD):
        raise ToolError(f"Bookings can be made up to {MAX_BOOKING_DAYS_AHEAD} days ahead. Please choose an earlier date.")
    day = when.astimezone(IST).date()
    rows, _ = await HealthcareService(ctx.session).list_appointments(patient_id=patient.id, facility_id=facility_id, page_size=100)
    for a in rows:
        if a.status in ACTIVE_STATES and aware(a.appointment_date).astimezone(IST).date() == day:
            raise ToolError(f"You already have an appointment at {facility.name} on {day:%d %b %Y} "
                            f"(status {a.status.value}). I won't create a duplicate.")
    return facility


async def _prepare_booking(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    patient = await _patient(ctx)
    fid = parse_uuid(args.get("facility_id"), "facility_id")
    when = _parse_when(args.get("appointment_date"))
    reason = str(args.get("reason", "")).strip()[:300]
    if len(reason) < 2:
        raise ToolError("What is the appointment for? I need a short reason (for example, 'fever for 3 days' or 'BP check').")
    facility = await _check_booking(ctx, patient, fid, when)
    slot = (str(args["time_slot"]).strip()[:50] if args.get("time_slot") else None)
    when_txt = when.astimezone(IST).strftime("%A, %d %B %Y, %I:%M %p")
    return {"summary": f"Book an appointment at {facility.name} on {when_txt} (India time). Reason: {reason}."
                       + (f" Preferred time slot: {slot}." if slot else ""),
            "args": {"facility_id": str(fid), "appointment_date": when.isoformat(), "reason": reason, "time_slot": slot}}


async def _execute_booking(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    patient = await _patient(ctx)
    fid = uuid.UUID(args["facility_id"])
    when = datetime.fromisoformat(args["appointment_date"])
    facility = await _check_booking(ctx, patient, fid, when)  # re-validated: state may have changed since the proposal
    appt = await HealthcareService(ctx.session).create_appointment(
        AppointmentCreate(patient_id=patient.id, facility_id=fid, appointment_date=when, reason=args["reason"],
                          time_slot=args.get("time_slot")),
        actor_id=ctx.user.id, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"appointment_id": str(appt.id), "token_number": appt.token_number, "status": appt.status.value,
            "message": (f"Your appointment request was recorded at {facility.name} for "
                        f"{when.astimezone(IST):%d %b %Y, %I:%M %p}. Token number: {appt.token_number}. "
                        f"Status returned by the system: {appt.status.value}.")}


async def _owned_appointment(ctx: ToolContext, raw_id: Any) -> Appointment:
    patient = await _patient(ctx)
    appt = await HealthcareService(ctx.session).repo.get_appointment_by_id(parse_uuid(raw_id, "appointment_id"))
    if appt is None or appt.patient_id != patient.id:  # same answer for "missing" and "not yours"
        raise ToolError("I couldn't find that appointment in your account.")
    return appt


async def _prepare_cancel(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    appt = await _owned_appointment(ctx, args.get("appointment_id"))
    if appt.status not in CANCELLABLE:
        raise ToolError(f"This appointment is {appt.status.value} and can't be cancelled.")
    names = await _facility_names(ctx, [appt.facility_id])
    reason = str(args.get("reason", "")).strip()[:200] or "Cancelled by patient"
    return {"summary": f"Cancel your appointment at {names.get(appt.facility_id, 'the facility')} on "
                       f"{aware(appt.appointment_date).astimezone(IST):%d %b %Y, %I:%M %p} (token {appt.token_number}). "
                       f"Reason: {reason}.",
            "args": {"appointment_id": str(appt.id), "reason": reason}}


async def _execute_cancel(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    appt = await _owned_appointment(ctx, args["appointment_id"])
    if appt.status not in CANCELLABLE:
        raise ToolError(f"This appointment is already {appt.status.value}.")
    updated = await HealthcareService(ctx.session).update_appointment_status(
        appt.id, AppointmentStatusUpdate(status=AppointmentStatus.CANCELLED, cancellation_reason=args.get("reason")),
        actor_id=ctx.user.id, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"appointment_id": str(updated.id), "status": updated.status.value,
            "message": f"Your appointment (token {updated.token_number}) is now {updated.status.value} in the system."}


async def _context(ctx: ToolContext) -> str:
    patient = await HealthcareService(ctx.session).get_patient_by_user_id(ctx.user.id)
    if patient is None:
        return "- No patient profile is linked to this account; record and booking tools will say so."
    ctx.state["patient"] = patient
    names = await _facility_names(ctx, [patient.primary_facility_id])
    return (f"- Patient's first name: {patient.first_name}\n"
            f"- Primary facility: {names.get(patient.primary_facility_id)} (facility_id {patient.primary_facility_id})")


def _tools() -> Dict[str, ToolSpec]:
    specs = [
        ToolSpec("get_my_profile", "The patient's own registered details (age, gender, blood group, recorded allergies and "
                 "conditions, primary facility). Never returns contact details.", obj(), _profile,
                 "Your profile", P.PATIENTS_PROFILE_READ),
        ToolSpec("list_my_appointments", "The patient's own appointments with facility, date/time, token and the exact system status.",
                 obj({"which": {"type": "string", "description": "upcoming, past or all (default all)"}}), _appointments,
                 "Your appointments", P.APPOINTMENTS_VIEW),
        ToolSpec("get_my_health_records", "The patient's own consultation history: complaints, notes, diagnoses recorded by "
                 "clinicians, vitals, lab orders/results with lab reference ranges, prescriptions, referrals.", obj(), _records,
                 "Your health records", P.PATIENTS_RECORDS_READ),
        ToolSpec("get_my_prescriptions", "The patient's own prescriptions with recorded dosage instructions and collection status.",
                 obj(), _prescriptions, "Your prescriptions", P.PRESCRIPTIONS_READ),
        ToolSpec("get_my_notifications", "The patient's recent in-app notifications and reminders.", obj(), _notifications,
                 "Your notifications", P.PATIENTS_NOTIFICATIONS_READ),
        ToolSpec("get_health_education_cards", "Verified Med2Us health-awareness cards (tips) by optional category: EXERCISE, "
                 "NUTRITION, HYDRATION_SLEEP, MENTAL_WELLNESS, HYGIENE, DISEASE_PREVENTION, VACCINATION, WARNING_SIGNS.",
                 obj({"category": {"type": "string"}}), _education, "Med2Us health awareness cards", P.PATIENTS_AWARENESS_READ),
        ToolSpec("find_facilities", "Search active PHCs/CHCs/hospitals by name, district or address text. Returns facility ids "
                 "needed for booking.", obj({"query": {"type": "string", "description": "name, district or area"}}),
                 _facilities, "Med2Us facility directory"),
        ToolSpec("find_nearest_facilities", "Find the nearest PHCs/CHCs/hospitals to a location the patient provided (address, area, "
                 "pincode or coordinates). Uses Google Maps when configured. Never assume the patient's location.",
                 obj({"address": {"type": "string"}, "latitude": {"type": "number"}, "longitude": {"type": "number"}}),
                 _nearest_facilities, "Google Maps / facility directory"),
        navigation_tool(frozenset({"patient"})),
        ToolSpec("propose_book_appointment", "Prepare (NOT perform) an appointment booking for the patient. The user must press "
                 "Confirm before anything is booked.",
                 obj({"facility_id": {"type": "string"}, "appointment_date": {"type": "string",
                      "description": "ISO 8601 date-time in India time, e.g. 2026-10-05T10:30:00"},
                      "reason": {"type": "string"}, "time_slot": {"type": "string"}},
                     ["facility_id", "appointment_date", "reason"]),
                 _prepare_booking, "Appointment booking", kind="action", execute=_execute_booking),
        ToolSpec("propose_cancel_appointment", "Prepare (NOT perform) cancellation of one of the patient's own appointments. "
                 "The user must press Confirm.", obj({"appointment_id": {"type": "string"}, "reason": {"type": "string"}},
                                                     ["appointment_id"]),
                 _prepare_cancel, "Appointment cancellation", kind="action", execute=_execute_cancel),
    ]
    return {s.name: s for s in specs}


PATIENT_ASSISTANT = AssistantConfig(
    key=KEY, title="Patient AI Assistant", role_codes=frozenset({"PATIENT"}), permission=P.PATIENTS_AI_WELLNESS_CHAT,
    role_prompt=ROLE_PROMPT, tools=_tools(), emergency_guard=True, context_loader=_context,
    starters={
        "en": ["Do I have an upcoming appointment?", "Explain my latest prescription", "Help me book an appointment",
               "How can I stay healthy this monsoon?"],
        "ta": ["என் அடுத்த சந்திப்பு எப்போது?", "என் சமீபத்திய மருந்துச் சீட்டை விளக்கவும்", "சந்திப்பு முன்பதிவு செய்ய உதவுங்கள்",
               "ஆரோக்கியமாக இருக்க என்ன செய்ய வேண்டும்?"],
        "hi": ["क्या मेरी कोई अपॉइंटमेंट है?", "मेरा नवीनतम पर्चा समझाइए", "अपॉइंटमेंट बुक करने में मदद करें",
               "स्वस्थ कैसे रहें?"],
    },
)
