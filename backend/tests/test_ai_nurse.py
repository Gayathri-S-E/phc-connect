"""Nurse AI Assistant: role isolation, facility scope, confirm-gated vitals recording, no clinical-decision tools.

The provider is a scripted client (no real Gemini traffic), as in test_ai_foundation.py."""
import copy
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.ai import safety
from app.ai.llm import FunctionCall, LLMResult, get_llm_client
from app.core.permissions import SystemPermissions as P
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.audit import AuditLog
from app.models.facility import Facility, FacilityType
from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    Consultation,
    ConsultationStatus,
    Patient,
    Vitals,
)
from app.models.identity import Role, RolePermission, ScopeLevel, User, UserRole
from app.repositories.role_repository import RoleRepository


class ScriptedLLM:
    def __init__(self, *steps):
        self.steps = list(steps)
        self.calls = []

    async def generate(self, system, contents, tools):
        self.calls.append({"system": system, "contents": copy.deepcopy(contents), "tools": [t["name"] for t in tools]})
        step = self.steps.pop(0) if self.steps else say("Okay.")
        if isinstance(step, Exception):
            raise step
        return step(self.calls[-1]) if callable(step) else step

    def last_tool_response(self):
        return self.calls[-1]["contents"][-1]["parts"][0]["functionResponse"]["response"]


def say(text):
    return LLMResult(text=text)


def call(name, **args):
    return LLMResult(text="", function_calls=[FunctionCall(name, args)])


def use(llm):
    app.dependency_overrides[get_llm_client] = lambda: llm
    return llm


@pytest.fixture(autouse=True)
def _fresh_limiter():
    safety.rate_limiter.reset()
    yield
    safety.rate_limiter.reset()


def _tok(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, extra_claims={'email': user.email})}"}


@pytest_asyncio.fixture
async def world(db_session, seeded_data):
    org, fac, doctor = seeded_data["org"], seeded_data["facility"], seeded_data["doctor_user"]
    perms = {p.code: p for p in await RoleRepository(db_session).list_permissions()}
    fac2 = Facility(id=uuid.uuid4(), organization_id=org.id, name="Other PHC Anna Nagar", code="TEST-PHC-002",
                    facility_type=FacilityType.PHC, state="Tamil Nadu", district="Chennai", is_active=True)
    db_session.add(fac2)

    nurse_role = Role(id=uuid.uuid4(), name="Nurse", code="NURSE", is_system=True, is_active=True)
    patient_role = Role(id=uuid.uuid4(), name="Patient", code="PATIENT", is_system=True, is_active=True)
    db_session.add_all([nurse_role, patient_role])
    await db_session.flush()
    for c in (P.CLINICAL_AI_ADVISORY, P.APPOINTMENTS_VIEW, P.PATIENTS_PROFILE_READ, P.PATIENTS_VITALS_RECORD):
        db_session.add(RolePermission(role_id=nurse_role.id, permission_id=perms[c].id))
    for c in (P.PATIENTS_PROFILE_READ, P.APPOINTMENTS_VIEW, P.PATIENTS_AI_WELLNESS_CHAT):
        db_session.add(RolePermission(role_id=patient_role.id, permission_id=perms[c].id))
    doctor_role = (await db_session.execute(select(Role).where(Role.code == "DOCTOR"))).scalar_one()
    db_session.add(RolePermission(role_id=doctor_role.id, permission_id=perms[P.CLINICAL_AI_ADVISORY].id))
    await db_session.flush()

    def user(email, name, facility):
        u = User(id=uuid.uuid4(), email=email, hashed_password=get_password_hash("Pass12345!"), full_name=name,
                 organization_id=org.id, facility_id=facility.id, is_active=True, is_verified=True)
        db_session.add(u)
        return u

    nurse, pa_user = user("nurse@test.in", "Nurse Meena", fac), user("pa@test.in", "Asha Devi", fac)
    await db_session.flush()
    db_session.add(UserRole(user_id=nurse.id, role_id=nurse_role.id, organization_id=org.id, facility_id=fac.id,
                            scope_level=ScopeLevel.FACILITY))
    db_session.add(UserRole(user_id=pa_user.id, role_id=patient_role.id, organization_id=org.id, facility_id=fac.id,
                            scope_level=ScopeLevel.SELF))

    def patient(idx, u, f, first):
        p = Patient(id=uuid.uuid4(), user_id=u.id if u else None, primary_facility_id=f.id, patient_identifier=f"UHID-{idx}",
                    first_name=first, last_name="Test", date_of_birth=date(1990, 1, 1), gender="FEMALE",
                    phone_number=f"+91900000000{idx}", address=f"Secret Street {idx}",
                    allergies="Penicillin" if idx == 1 else None, is_active=True)
        db_session.add(p)
        return p

    pa, pc = patient(1, pa_user, fac, "Asha"), patient(3, None, fac2, "Chitra")
    await db_session.flush()
    now = datetime.now(timezone.utc)
    appt_a = Appointment(id=uuid.uuid4(), patient_id=pa.id, facility_id=fac.id, token_number=503, priority="ROUTINE",
                         appointment_date=now, status=AppointmentStatus.SCHEDULED, reason="Cough")
    appt_c = Appointment(id=uuid.uuid4(), patient_id=pc.id, facility_id=fac2.id, token_number=9, priority="ROUTINE",
                         appointment_date=now, status=AppointmentStatus.SCHEDULED, reason="SECRET-C-REASON")
    db_session.add_all([appt_a, appt_c])
    await db_session.commit()
    return {"fac": fac, "pa": pa, "pc": pc, "appt_a": appt_a, "appt_c": appt_c, "nurse": nurse,
            "H": {"nurse": _tok(nurse), "doctor": _tok(doctor), "patient": _tok(pa_user)}}


async def chat(client, who, assistant, message, conv=None, expect=200):
    body = {"message": message}
    if conv:
        body["conversation_id"] = str(conv)
    r = await client.post(f"/api/v1/ai/{assistant}/chat", json=body, headers=who)
    assert r.status_code == expect, r.text
    return r.json().get("data") if expect == 200 else r.json()


def _vitals_count(db_session, appt_id=None):
    return db_session.execute(select(func.count()).select_from(Vitals))


# =========================================================================== isolation
@pytest.mark.asyncio
async def test_nurse_assistant_is_isolated_by_role(async_client, world):
    use(ScriptedLLM())
    H = world["H"]
    await chat(async_client, H["doctor"], "NURSE", "hello", expect=403)
    await chat(async_client, H["patient"], "NURSE", "hello", expect=403)
    await chat(async_client, H["nurse"], "DOCTOR", "hello", expect=403)
    await chat(async_client, H["nurse"], "PATIENT", "hello", expect=403)
    assert [a["key"] for a in (await async_client.get("/api/v1/ai/assistants", headers=H["nurse"])).json()["data"]] == ["NURSE"]
    assert "NURSE" not in [a["key"] for a in (await async_client.get("/api/v1/ai/assistants", headers=H["doctor"])).json()["data"]]
    await chat(async_client, H["nurse"], "NURSE", "hello")


@pytest.mark.asyncio
async def test_nurse_assistant_declares_no_clinical_decision_or_admin_tools(async_client, world):
    llm = use(ScriptedLLM(say("That's for the doctor.")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "what should I give this patient for fever?")
    names = set(llm.calls[0]["tools"])
    assert not any(k in n for n in names for k in ("prescri", "diagnos", "dose", "inventory", "stock", "approve",
                                                   "finalize", "referral", "lab_order", "medic"))
    assert "propose_record_vitals" in names
    system = llm.calls[0]["system"]
    assert "NOT AVAILABLE" in system and "task" in system.lower() and "follow-up" in system.lower()


# =========================================================================== reads and scope
@pytest.mark.asyncio
async def test_queue_shows_pending_preparation_only_for_own_facility(async_client, world):
    llm = use(ScriptedLLM(call("get_nursing_queue"), say("One patient waiting.")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "who is waiting?")
    res = llm.last_tool_response()["result"]
    assert [q["uhid"] for q in res["queue_in_priority_order"]] == ["UHID-1"]
    row = res["queue_in_priority_order"][0]
    assert row["nursing_preparation"] == "VITALS_PENDING" and "spo2_percent" in row["required_vitals_missing"]
    assert "SECRET-C-REASON" not in str(llm.calls) and "Secret Street" not in str(llm.calls)


@pytest.mark.asyncio
async def test_nurse_cannot_reach_patient_or_appointment_of_other_facility(async_client, world, db_session):
    llm = use(ScriptedLLM(call("get_patient_preparation", patient_id=str(world["pc"].id)), say("No access.")))
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "open Chitra")
    assert "error" in llm.last_tool_response() and d["tools_used"] == []
    assert "UHID-3" not in str(llm.last_tool_response())
    denied = (await db_session.execute(select(AuditLog).where(AuditLog.action == "AI_TOOL_DENIED"))).scalars().all()
    assert len(denied) == 1

    llm = use(ScriptedLLM(call("propose_record_vitals", appointment_id=str(world["appt_c"].id), pulse_rate=80), say("No.")))
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "record pulse 80 for Chitra")
    assert d["pending_action"] is None and "error" in llm.last_tool_response()

    llm = use(ScriptedLLM(call("find_patient", query="Test"), say("found")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "find Test")
    assert {m["uhid"] for m in llm.last_tool_response()["result"]["matches"]} == {"UHID-1"}


@pytest.mark.asyncio
async def test_patient_preparation_reports_recorded_data_and_gaps(async_client, world):
    llm = use(ScriptedLLM(call("get_patient_preparation", patient_id=str(world["pa"].id)), say("ok")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "prepare Asha")
    res = llm.last_tool_response()["result"]
    assert res["allergies_recorded"] == "Penicillin" and res["previously_recorded_vitals_newest_first"] == []
    assert len(res["required_vitals_missing_in_latest_record"]) == 5
    assert "Secret Street" not in str(res) and "+91900000000" not in str(res)


# =========================================================================== vitals action
@pytest.mark.asyncio
async def test_vitals_need_confirm_then_store_exact_values_once(async_client, world, db_session):
    args = dict(appointment_id=str(world["appt_a"].id), temperature_celsius=37.4, systolic_bp=118, diastolic_bp=76,
                pulse_rate=82, respiratory_rate=18, spo2_percent=98, height_cm=160.5, weight_kg=54.2)
    use(ScriptedLLM(call("propose_record_vitals", **args), say("I have saved the vitals!")))  # lying model
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "temp 37.4, BP 118/76, pulse 82, RR 18, SpO2 98, 160.5 cm, 54.2 kg")
    p = d["pending_action"]
    for shown in ("37.4", "118", "76", "82", "18", "98", "160.5", "54.2"):
        assert shown in p["summary"]
    assert "Nothing has been changed yet" in d["answer"]
    assert (await db_session.execute(select(func.count()).select_from(Vitals))).scalar_one() == 0   # nothing before confirm

    r1 = await async_client.post(f"/api/v1/ai/actions/{p['id']}/confirm", headers=world["H"]["nurse"])
    assert r1.status_code == 200 and r1.json()["data"]["status"] == "EXECUTED", r1.text
    r2 = await async_client.post(f"/api/v1/ai/actions/{p['id']}/confirm", headers=world["H"]["nurse"])  # double click
    assert r2.status_code == 200 and r2.json()["data"]["already_completed"] is True

    db_session.expunge_all()
    rows = (await db_session.execute(select(Vitals))).scalars().all()
    assert len(rows) == 1                                                                   # idempotent
    v = rows[0]
    assert (v.temperature_celsius, v.systolic_bp, v.diastolic_bp, v.pulse_rate, v.respiratory_rate, v.spo2_percent,
            v.height_cm, v.weight_kg) == (37.4, 118, 76, 82, 18, 98, 160.5, 54.2)
    assert v.recorded_by_id == world["nurse"].id
    audit = (await db_session.execute(select(AuditLog).where(AuditLog.action == "NURSE_TRIAGE_VITALS_RECORDED"))).scalars().all()
    assert len(audit) == 1


@pytest.mark.asyncio
async def test_partial_vitals_leave_other_fields_empty(async_client, world, db_session):
    use(ScriptedLLM(call("propose_record_vitals", appointment_id=str(world["appt_a"].id), pulse_rate=76), say("Confirm?")))
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "pulse 76")
    assert "Not provided" in d["pending_action"]["summary"]
    r = await async_client.post(f"/api/v1/ai/actions/{d['pending_action']['id']}/confirm", headers=world["H"]["nurse"])
    assert r.json()["data"]["status"] == "EXECUTED"
    db_session.expunge_all()
    v = (await db_session.execute(select(Vitals))).scalar_one()
    assert v.pulse_rate == 76 and v.temperature_celsius is None and v.systolic_bp is None and v.spo2_percent is None


@pytest.mark.asyncio
async def test_out_of_range_or_inconsistent_vitals_are_rejected_not_altered(async_client, world, db_session):
    aid = str(world["appt_a"].id)
    cases = [
        dict(temperature_celsius=99.0), dict(pulse_rate=500), dict(spo2_percent=150), dict(systolic_bp=20, diastolic_bp=10),
        dict(respiratory_rate=2), dict(weight_kg=-4), dict(pulse_rate=80.5),   # non-integer pulse is refused, not rounded
        dict(systolic_bp=120), dict(systolic_bp=90, diastolic_bp=120), {},
    ]
    for extra in cases:
        llm = use(ScriptedLLM(call("propose_record_vitals", appointment_id=aid, **extra), say("Please re-check that value.")))
        d = await chat(async_client, world["H"]["nurse"], "NURSE", "record these")
        assert d["pending_action"] is None, extra
        assert "error" in llm.last_tool_response(), extra
    assert (await db_session.execute(select(func.count()).select_from(Vitals))).scalar_one() == 0


@pytest.mark.asyncio
async def test_vitals_refused_for_closed_appointment(async_client, world, db_session):
    appt = await db_session.get(Appointment, world["appt_a"].id)
    appt.status = AppointmentStatus.COMPLETED
    await db_session.commit()
    llm = use(ScriptedLLM(call("propose_record_vitals", appointment_id=str(world["appt_a"].id), pulse_rate=80), say("No.")))
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "pulse 80")
    assert d["pending_action"] is None and "COMPLETED" in llm.last_tool_response()["error"]


# =========================================================================== doctor-review coordination
@pytest.mark.asyncio
async def test_awaiting_doctor_review_uses_real_data_only(async_client, world, db_session):
    llm = use(ScriptedLLM(call("list_awaiting_doctor_review"), say("None.")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "who is waiting for the doctor?")
    assert llm.last_tool_response()["result"]["count"] == 0

    use(ScriptedLLM(call("propose_record_vitals", appointment_id=str(world["appt_a"].id), pulse_rate=90), say("Confirm?")))
    d = await chat(async_client, world["H"]["nurse"], "NURSE", "pulse 90")
    await async_client.post(f"/api/v1/ai/actions/{d['pending_action']['id']}/confirm", headers=world["H"]["nurse"])
    llm = use(ScriptedLLM(call("list_awaiting_doctor_review"), say("One.")))
    await chat(async_client, world["H"]["nurse"], "NURSE", "who is waiting for the doctor?")
    res = llm.last_tool_response()["result"]
    assert res["count"] == 1 and res["vitals_recorded_doctor_consultation_still_open"][0]["uhid"] == "UHID-1"
    assert res["vitals_recorded_doctor_consultation_still_open"][0]["doctor_consultation_status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_triage_vitals_endpoint_enforces_facility_scope(async_client, world):
    """Regression: the REST endpoint used to accept any appointment id, including another facility's."""
    body = {"systolic_bp": 120, "diastolic_bp": 80, "pulse_rate": 72, "temperature_celsius": 36.8,
            "respiratory_rate": 16, "spo2_percent": 98}
    other = await async_client.post(f"/api/v1/nurse/triage/vitals?appointment_id={world['appt_c'].id}",
                                    json=body, headers=world["H"]["nurse"])
    assert other.status_code == 403, other.text
    missing = await async_client.post(f"/api/v1/nurse/triage/vitals?appointment_id={uuid.uuid4()}",
                                      json=body, headers=world["H"]["nurse"])
    assert missing.status_code == 404
    own = await async_client.post(f"/api/v1/nurse/triage/vitals?appointment_id={world['appt_a'].id}",
                                  json=body, headers=world["H"]["nurse"])
    assert own.status_code == 201, own.text
