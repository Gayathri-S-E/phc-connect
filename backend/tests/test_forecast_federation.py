"""Emergency-surge early warning, cross-district redistribution, federated modelling, Gemini explanation, Vertex hook.

The Gemini client is replaced by a scripted stub (no network). Everything else runs against the real service code.
"""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.ai.llm import LLMNotConfigured, LLMResult, get_llm_client
from app.core.config import settings
from app.core.permissions import SystemPermissions as P
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.emergency import (EmergencyAffectedFacility, EmergencyIncident, EmergencyPriority, EmergencyStatus,
                                  EmergencyType)
from app.models.facility import Facility, FacilityType
from app.models.federation import FederatedLocalUpdate, FederatedNationalPrior
from app.models.healthcare import Medication
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.models.pharmacy import InventoryItem, StockMovement, StockMovementType
from app.services.forecast_federation_service import (FederationConfig, combine_updates, haversine_km, load_surge_config,
                                                      scrub_for_llm)

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class ScriptedLLM:
    def __init__(self, *steps):
        self.steps, self.calls = list(steps), []

    async def generate(self, system, contents, tools):
        self.calls.append({"system": system, "contents": contents, "tools": tools})
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def use(llm):
    app.dependency_overrides[get_llm_client] = lambda: llm
    return llm


def hdr(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, extra_claims={'email': user.email})}"}


def days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)


@pytest_asyncio.fixture
async def world(db_session, seeded_data):
    org, chg, admin = seeded_data["org"], seeded_data["facility"], seeded_data["admin_user"]  # chg: Tamil Nadu / Chengalpattu

    def fac(name, code, state, district, lat=None, lon=None):
        f = Facility(id=uuid.uuid4(), organization_id=org.id, name=name, code=code, facility_type=FacilityType.PHC,
                     state=state, district=district, is_active=True, latitude=lat, longitude=lon)
        db_session.add(f)
        return f

    chg.latitude, chg.longitude = 12.6819, 79.9888
    chn = fac("PHC Chennai", "F-CHN", "Tamil Nadu", "Chennai", 13.0827, 80.2707)
    mdu = fac("PHC Madurai", "F-MDU", "Tamil Nadu", "Madurai", 9.9252, 78.1198)
    cbe = fac("PHC Coimbatore Sparse", "F-CBE", "Tamil Nadu", "Coimbatore")
    koc = fac("PHC Kochi", "F-KOC", "Kerala", "Ernakulam", 9.9312, 76.2673)
    tvm = fac("PHC Trivandrum", "F-TVM", "Kerala", "Thiruvananthapuram")
    koz = fac("PHC Kozhikode", "F-KOZ", "Kerala", "Kozhikode")
    med = Medication(id=uuid.uuid4(), name="Paracetamol 500mg", code="MED-PCM", strength="500mg", dosage_form="Tablet")
    med2 = Medication(id=uuid.uuid4(), name="Rare Antivenom", code="MED-AV", strength="10ml", dosage_form="Vial")
    db_session.add_all([med, med2])
    await db_session.flush()

    items = {}

    def stock(f, m, on_hand, reorder, dispenses=()):
        it = InventoryItem(id=uuid.uuid4(), facility_id=f.id, medication_id=m.id, quantity_on_hand=on_hand,
                           quantity_reserved=0, reorder_level=reorder, critical_level=5, minimum_stock_level=20)
        db_session.add(it)
        items[(f.code if hasattr(f, "code") else f, m.code)] = it
        for d, q in dispenses:
            db_session.add(StockMovement(id=uuid.uuid4(), facility_id=f.id, inventory_item_id=it.id,
                                         movement_type=StockMovementType.DISPENSE, quantity=-q, balance_after=on_hand,
                                         actor_id=admin.id, created_at=days_ago(d)))

    # recipient: 90 units in trailing 30d => 3.0/day, 10 on hand
    stock(chg, med, 10, 50, [(1, 30), (3, 30), (5, 30), (100, 10)])
    stock(chn, med, 100, 40, [(10, 60)])
    stock(mdu, med, 300, 40, [(20, 30)])
    stock(cbe, med, 500, 40)                                   # sparse: no dispensing
    stock(koc, med, 500, 40, [(2, 200)])
    stock(tvm, med, 400, 40, [(4, 100)])
    stock(koz, med, 300, 40, [(6, 50)])
    stock(chg, med2, 20, 10, [(2, 10)])                        # only 2 TN facilities hold med2 -> suppressed
    stock(chn, med2, 20, 10, [(3, 10)])
    await db_session.flush()

    perms = {p.code: p for p in (await db_session.execute(select(Permission))).scalars().all()}
    role = Role(id=uuid.uuid4(), name="Supply Analyst", code="SUPPLY_ANALYST", is_system=False, is_active=True)
    db_session.add(role)
    await db_session.flush()
    for c in (P.AI_RISK_ANALYZE, P.AI_FORECAST_VIEW):
        db_session.add(RolePermission(role_id=role.id, permission_id=perms[c].id))

    def user(email, f, scope):
        u = User(id=uuid.uuid4(), email=email, hashed_password=get_password_hash("Pass12345!"), full_name=email,
                 organization_id=org.id, facility_id=f.id, is_active=True, is_verified=True)
        db_session.add(u)
        return u, scope

    made = {"district": user("district@t.in", chg, ScopeLevel.DISTRICT), "state_tn": user("tn@t.in", chg, ScopeLevel.STATE),
            "state_kl": user("kl@t.in", koc, ScopeLevel.STATE), "facility": user("fac@t.in", cbe, ScopeLevel.FACILITY)}
    await db_session.flush()
    for u, scope in made.values():
        db_session.add(UserRole(user_id=u.id, role_id=role.id, organization_id=org.id, facility_id=u.facility_id,
                                scope_level=scope))
    await db_session.commit()
    return {"chg": chg, "chn": chn, "mdu": mdu, "cbe": cbe, "koc": koc, "tvm": tvm, "koz": koz, "med": med, "med2": med2,
            "items": items, "admin": admin, **{k: v[0] for k, v in made.items()}, "org": org}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.delenv("SURGE_MULTIPLIER_CONFIG", raising=False)
    monkeypatch.setattr(FederationConfig, "min_facilities", 3)
    monkeypatch.setattr(FederationConfig, "min_states", 2)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    yield
    app.dependency_overrides.pop(get_llm_client, None)


# ----------------------------------------------------------------------------- pure maths
def test_haversine_chennai_madurai():
    assert 420 < haversine_km(13.0827, 80.2707, 9.9252, 78.1198) < 440
    assert haversine_km(10, 10, 10, 10) == 0


def test_fedavg_is_sample_weighted_and_pooled_variance_exact():
    a = {"n_samples": 100, "mean_daily_rate": 2.0, "variance": 1.0, "seasonality": {"1": {"factor": 1.2, "n": 30}}}
    b = {"n_samples": 300, "mean_daily_rate": 4.0, "variance": 2.0, "seasonality": {"1": {"factor": 0.8, "n": 10}}}
    r = combine_updates([a, b])
    assert r["mean_daily_rate"] == pytest.approx(3.5)  # (100*2 + 300*4)/400
    assert r["variance"] == pytest.approx((100 * (1 + 2.25) + 300 * (2 + 0.25)) / 400)
    assert r["seasonality"]["1"]["factor"] == pytest.approx((30 * 1.2 + 10 * 0.8) / 40, abs=1e-3)


def test_scrub_drops_ids_and_unknown_fields():
    out = scrub_for_llm({"items": [{"facility_id": str(uuid.uuid4()), "facility_name": "PHC", "email": "a@b.c",
                                    "risk_tier": "HIGH", "secret": "x"}]})
    assert out == {"items": [{"facility_name": "PHC", "risk_tier": "HIGH"}]}


# ----------------------------------------------------------------------------- 1. surge
async def _incident(db, world, priority=EmergencyPriority.HIGH, etype=EmergencyType.DISEASE_CLUSTER, affected=True):
    inc = EmergencyIncident(id=uuid.uuid4(), reference="EMG-1", state="Tamil Nadu", district="Chengalpattu",
                            emergency_type=etype, title="Outbreak", description="d", affected_area="block",
                            source="test", priority=priority, status=EmergencyStatus.IN_PROGRESS,
                            reported_by=world["admin"].id)
    db.add(inc)
    await db.flush()
    if affected:
        db.add(EmergencyAffectedFacility(incident_id=inc.id, facility_id=world["chg"].id))
    await db.commit()


async def _restock_chg(db, world, qty=100):
    it = await db.get(InventoryItem, world["items"][(world["chg"].code, "MED-PCM")].id)
    it.quantity_on_hand = qty
    await db.commit()


@pytest.mark.asyncio
async def test_surge_multiplier_raises_tier_with_explained_maths(async_client, db_session, world):
    await _restock_chg(db_session, world, 100)
    url = f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}"
    r = await async_client.get(url, headers=hdr(world["admin"]))
    assert r.status_code == 200
    assert r.json()["data"]["items"] == [], r.json()["data"]["items"]  # 100 units / 3 per day = 33 days -> LOW, hidden at min_tier=MEDIUM

    await _incident(db_session, world)  # DISEASE_CLUSTER 1.5 x HIGH 1.0 x affected facility 1.0 => x2.5
    r = await async_client.get(url, headers=hdr(world["admin"]))
    data = r.json()["data"]
    assert data["count"] == 1
    it = data["items"][0]
    assert it["risk_tier"] == "HIGH" and it["baseline_risk_tier"] == "LOW" and it["escalated_by_emergency"] is True
    assert it["days_of_supply_baseline"] == 33.3 and it["days_of_supply_surge"] == 13.3
    ev = it["evidence"]
    assert ev["surge_multiplier"] == 2.5 and ev["baseline_daily_rate"] == 3.0 and ev["surge_daily_rate"] == 7.5
    assert ev["incident"]["reference"] == "EMG-1" and ev["incident"]["formula"].startswith("1 + 1.5 x 1.0 x 1.0")
    assert ev["projected_shortfall_in_horizon"] == 125.0  # 7.5 * 30 - 100
    assert it["confidence"] == pytest.approx(0.75 * 0.85, abs=0.01)  # 3 events, x0.85 for assumed multiplier
    assert it["predicted_stockout_date"]
    assert "surge multiplier" in it["explanation"]
    assert data["methodology"]["multiplier_config"]["max_multiplier"] == 4.0
    assert data["ai_explanation"] is None and data["ai_explanation_reason"] == "NOT_REQUESTED"


@pytest.mark.asyncio
async def test_surge_multiplier_is_configurable_and_capped(monkeypatch, async_client, db_session, world):
    await _restock_chg(db_session, world, 100)
    await _incident(db_session, world, priority=EmergencyPriority.CRITICAL)
    monkeypatch.setenv("SURGE_MULTIPLIER_CONFIG", json.dumps({"type_uplift": {"DISEASE_CLUSTER": 0.5}}))
    assert load_surge_config()["type_uplift"]["DISEASE_CLUSTER"] == 0.5
    r = await async_client.get(f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}&min_tier=LOW",
                               headers=hdr(world["admin"]))
    assert r.json()["data"]["items"][0]["evidence"]["surge_multiplier"] == 1.75  # 1 + 0.5 x 1.5 x 1.0
    monkeypatch.setenv("SURGE_MULTIPLIER_CONFIG", json.dumps({"max_multiplier": 2.0}))
    r = await async_client.get(f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}&min_tier=LOW",
                               headers=hdr(world["admin"]))
    assert r.json()["data"]["items"][0]["evidence"]["surge_multiplier"] == 2.0


@pytest.mark.asyncio
async def test_surge_scope_is_enforced(async_client, db_session, world):
    await _restock_chg(db_session, world, 100)
    await _incident(db_session, world)
    # facility-scope user cannot ask about another facility
    r = await async_client.get(f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}", headers=hdr(world["facility"]))
    assert r.status_code == 403
    # a TN state officer cannot request Kerala
    r = await async_client.get("/api/v1/analytics/surge-risk?state=Kerala", headers=hdr(world["state_tn"]))
    assert r.status_code == 403
    # a district officer sees only their district
    r = await async_client.get("/api/v1/analytics/surge-risk?min_tier=LOW", headers=hdr(world["district"]))
    names = {i["facility_name"] for i in r.json()["data"]["items"]}
    assert names == {world["chg"].name}


# ----------------------------------------------------------------------------- 2. redistribution
@pytest.mark.asyncio
async def test_redistribution_distance_aware_keeps_reorder_and_is_advisory(async_client, world):
    r = await async_client.get(f"/api/v1/analytics/redistribution?medication_id={world['med'].id}", headers=hdr(world["admin"]))
    assert r.status_code == 200
    d = r.json()["data"]
    recs = [x for x in d["recommendations"] if x["destination_facility_id"] == str(world["chg"].id)]
    first = recs[0]
    assert first["source_facility_name"] == "PHC Chennai" and first["level"] == "CROSS_DISTRICT"
    assert 45 < first["distance_km"] < 70  # Chengalpattu -> Chennai (haversine)
    assert first["recommended_quantity"] == 60  # 100 available - keeps reorder 40
    assert first["evidence"]["source_retained_level"] >= first["evidence"]["source_reorder_level"] == 40
    assert first["advisory"] is True and first["requires_human_approval"] is True and "approv" in first["next_step"]
    total = sum(x["recommended_quantity"] for x in recs)
    assert total == 80  # need = max(50, 3 x 30) - 10; fully met by nearest donors
    for x in d["recommendations"]:
        assert x["evidence"]["source_available"] - x["recommended_quantity"] >= x["evidence"]["source_reorder_level"]
    assert d["advisory_notice"]
    # nothing was actually moved
    assert first["destination_facility_id"] == str(world["chg"].id)


@pytest.mark.asyncio
async def test_redistribution_respects_scope_and_cross_state(async_client, db_session, world):
    # shrink in-state donors so a Kerala donor is needed to cover the gap
    for key, qty in ((("F-CHN"), 45), ("F-MDU", 45), ("F-CBE", 45)):
        it = await db_session.get(InventoryItem, world["items"][(key, "MED-PCM")].id)
        it.quantity_on_hand = qty
    await db_session.commit()
    url = f"/api/v1/analytics/redistribution?medication_id={world['med'].id}"

    g = (await async_client.get(url, headers=hdr(world["admin"]))).json()["data"]
    assert {x["level"] for x in g["recommendations"]} >= {"CROSS_DISTRICT", "CROSS_STATE"}
    assert any(x["source_state"] == "Kerala" for x in g["recommendations"])

    s = (await async_client.get(url, headers=hdr(world["state_tn"]))).json()["data"]
    assert s["recommendations"] and all(x["source_state"] == "Tamil Nadu" and x["destination_state"] == "Tamil Nadu"
                                        for x in s["recommendations"])
    assert s["unmet_needs"]  # shortfall is reported, not silently filled from out-of-scope stock

    dist = (await async_client.get(url, headers=hdr(world["district"]))).json()["data"]
    assert dist["recommendations"] == []  # no donors inside Chengalpattu
    assert dist["unmet_needs"][0]["facility_name"] == world["chg"].name

    nocross = (await async_client.get(url + "&allow_cross_state=false", headers=hdr(world["admin"]))).json()["data"]
    assert all(x["level"] != "CROSS_STATE" for x in nocross["recommendations"])
    far = (await async_client.get(url + "&max_distance_km=100", headers=hdr(world["admin"]))).json()["data"]
    assert all(x["distance_km"] is None or x["distance_km"] <= 100 for x in far["recommendations"])


# ----------------------------------------------------------------------------- 3. federation
async def _run_round(client, world):
    a = await client.post("/api/v1/analytics/federation/local-update", headers=hdr(world["state_tn"]))
    b = await client.post("/api/v1/analytics/federation/local-update", headers=hdr(world["state_kl"]))
    assert a.status_code == 200 and b.status_code == 200, (a.text, b.text)
    return a.json()["data"], b.json()["data"]


@pytest.mark.asyncio
async def test_local_update_stores_only_aggregates_and_suppresses_small_cells(async_client, db_session, world):
    tn, kl = await _run_round(async_client, world)
    assert tn["state"] == "Tamil Nadu" and kl["state"] == "Kerala"
    published = {p["medication_id"]: p for p in tn["published"]}
    p = published[str(world["med"].id)]
    assert p["n_facilities"] == 4 and p["n_samples"] == 4 * FederationConfig.rate_window_days
    assert p["mean_daily_rate"] == pytest.approx((90 + 60 + 30) / p["n_samples"], abs=1e-3)  # trailing-90d totals
    # med2 sits in only 2 TN facilities -> not published
    assert str(world["med2"].id) not in published
    assert any(s["medication_id"] == str(world["med2"].id) for s in tn["suppressed"])
    # no identifiers in the response, and the tables carry no facility/patient/transaction columns
    assert not UUID_RE.findall(json.dumps({"published": [{k: v for k, v in x.items() if k != "medication_id"} for x in tn["published"]]}))
    for model in (FederatedLocalUpdate, FederatedNationalPrior):
        cols = {c.name for c in model.__table__.columns}
        assert not {"facility_id", "patient_id", "user_id", "quantity", "movement_id"} & cols
    rows = (await db_session.execute(select(FederatedLocalUpdate))).scalars().all()
    assert {r.state_key for r in rows} == {"tamil nadu", "kerala"}
    assert all(r.n_facilities >= 3 for r in rows)
    # seasonality is only produced from real history (>= 60 days observed), never from unobserved months
    tn_row = next(r for r in rows if r.state_key == "tamil nadu" and r.medication_id == world["med"].id)
    assert tn_row.seasonality and all(v["n"] > 0 for v in tn_row.seasonality.values())


@pytest.mark.asyncio
async def test_state_cannot_read_or_compute_another_states_params(async_client, world):
    await _run_round(async_client, world)
    own = await async_client.get("/api/v1/analytics/federation/local-params", headers=hdr(world["state_tn"]))
    assert own.status_code == 200 and {x["state"] for x in own.json()["data"]} == {"Tamil Nadu"}
    other = await async_client.get("/api/v1/analytics/federation/local-params?state=Kerala", headers=hdr(world["state_tn"]))
    assert other.status_code == 403
    assert (await async_client.post("/api/v1/analytics/federation/local-update?state=Kerala", headers=hdr(world["state_tn"]))).status_code == 403
    # district / facility authority is not enough for model parameters
    assert (await async_client.get("/api/v1/analytics/federation/local-params", headers=hdr(world["district"]))).status_code == 403
    assert (await async_client.post("/api/v1/analytics/federation/local-update", headers=hdr(world["facility"]))).status_code == 403
    # national authority may see both
    both = await async_client.get("/api/v1/analytics/federation/local-params", headers=hdr(world["admin"]))
    assert {x["state"] for x in both.json()["data"]} == {"Tamil Nadu", "Kerala"}


@pytest.mark.asyncio
async def test_national_aggregate_is_weighted_average_and_global_only(async_client, world):
    await _run_round(async_client, world)
    assert (await async_client.post("/api/v1/analytics/federation/aggregate", headers=hdr(world["state_tn"]))).status_code == 403
    locals_ = [x for x in (await async_client.get("/api/v1/analytics/federation/local-params", headers=hdr(world["admin"]))).json()["data"]
               if x["medication_id"] == str(world["med"].id)]
    assert len(locals_) == 2
    r = await async_client.post("/api/v1/analytics/federation/aggregate", headers=hdr(world["admin"]))
    assert r.status_code == 200
    prior = (await async_client.get(f"/api/v1/analytics/federation/prior?medication_id={world['med'].id}",
                                    headers=hdr(world["facility"]))).json()["data"][0]
    n = sum(x["n_samples"] for x in locals_)
    assert prior["n_samples"] == n and prior["n_states"] == 2
    assert prior["mean_daily_rate"] == pytest.approx(sum(x["n_samples"] * x["mean_daily_rate"] for x in locals_) / n)
    assert sorted(prior["contributing_states"]) == ["Kerala", "Tamil Nadu"]
    assert set(prior) == {"medication_id", "medication_name", "round_no", "n_states", "n_samples", "mean_daily_rate",
                          "variance", "seasonality", "contributing_states", "aggregated_at"}
    # med2 had no publishable local update, so no prior for it
    assert (await async_client.get(f"/api/v1/analytics/federation/prior?medication_id={world['med2'].id}",
                                   headers=hdr(world["facility"]))).json()["data"] == []


@pytest.mark.asyncio
async def test_sparse_facility_forecast_uses_shared_prior(async_client, world):
    url = f"/api/v1/analytics/federation/forecast?facility_id={world['cbe'].id}&medication_id={world['med'].id}"
    before = (await async_client.get(url, headers=hdr(world["facility"]))).json()["data"]["items"][0]
    assert before["national_prior_used"] is False and before["forecast_daily_rate"] == 0.0

    await _run_round(async_client, world)
    await async_client.post("/api/v1/analytics/federation/aggregate", headers=hdr(world["admin"]))
    it = (await async_client.get(url, headers=hdr(world["facility"]))).json()["data"]["items"][0]
    assert it["sparse_data"] is True and it["national_prior_used"] is True
    assert it["national_prior_weight"] == 1.0  # zero local events -> fully the prior
    assert it["forecast_daily_rate"] == pytest.approx(it["national_prior_rate"] * it["seasonal_adjustment"], abs=0.002)
    assert it["forecast_daily_rate"] > 0 and it["days_of_supply"] is not None
    assert it["confidence"] == 0.5
    # a facility-scope user still cannot forecast another facility
    other = await async_client.get(f"/api/v1/analytics/federation/forecast?facility_id={world['chg'].id}", headers=hdr(world["facility"]))
    assert other.status_code == 403
    # data-rich facility leans mostly on its own history
    rich = (await async_client.get(f"/api/v1/analytics/federation/forecast?facility_id={world['chg'].id}&medication_id={world['med'].id}",
                                   headers=hdr(world["admin"]))).json()["data"]["items"][0]
    assert rich["national_prior_weight"] == pytest.approx(10 / 13, abs=0.001)  # 3 events: w=3/13


# ----------------------------------------------------------------------------- 4. Gemini + Vertex
@pytest.mark.asyncio
async def test_gemini_explains_only_aggregates_multilingual(async_client, db_session, world):
    await _restock_chg(db_session, world, 100)
    await _incident(db_session, world)
    llm = use(ScriptedLLM(LLMResult(text="Paracetamol ka stock 13 din mein khatam ho sakta hai."),
                          LLMResult(text="சுருக்கம்")))
    url = f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}&explain=true"
    d = (await async_client.get(url + "&lang=hi", headers=hdr(world["admin"]))).json()["data"]
    assert d["ai_explanation"].startswith("Paracetamol ka stock") and d["ai_explanation_reason"] is None
    assert d["language"] == "hi" and d["provider"] == "google-gemini"
    assert d["explanation"]  # deterministic text is always present
    call = llm.calls[0]
    assert "Hindi" in call["system"] and call["tools"] == []
    sent = call["contents"][0]["parts"][0]["text"]
    assert not UUID_RE.findall(sent) and "admin@test.gov.in" not in sent
    payload = json.loads(sent)["data"]
    assert payload["items"][0]["risk_tier"] == "HIGH" and payload["items"][0]["evidence"]["surge_multiplier"] == 2.5
    ta = (await async_client.get(url + "&lang=ta", headers=hdr(world["admin"]))).json()["data"]
    assert "Tamil" in llm.calls[1]["system"] and ta["ai_explanation"] == "சுருக்கம்"
    assert (await async_client.get(url + "&lang=fr", headers=hdr(world["admin"]))).status_code == 422


@pytest.mark.asyncio
async def test_gemini_degrades_gracefully_without_key_or_on_failure(async_client, db_session, world):
    await _restock_chg(db_session, world, 100)
    await _incident(db_session, world)
    url = f"/api/v1/analytics/surge-risk?medication_id={world['med'].id}&facility_id={world['chg'].id}&explain=true"
    # real GeminiClient, no key configured (settings.GEMINI_API_KEY patched to "")
    d = (await async_client.get(url, headers=hdr(world["admin"]))).json()["data"]
    assert d["ai_explanation"] is None and d["ai_explanation_reason"] == "AI_NOT_CONFIGURED"
    assert d["explanation"] and d["items"][0]["risk_tier"] == "HIGH"
    # provider failure and empty answers also fall back
    use(ScriptedLLM(RuntimeError("boom")))
    d = (await async_client.get(url, headers=hdr(world["admin"]))).json()["data"]
    assert d["ai_explanation"] is None and d["ai_explanation_reason"] == "AI_UNAVAILABLE" and d["explanation"]
    use(ScriptedLLM(LLMNotConfigured("x")))
    d = (await async_client.get(url, headers=hdr(world["admin"]))).json()["data"]
    assert d["ai_explanation_reason"] == "AI_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_redistribution_and_forecast_can_be_explained(async_client, world):
    llm = use(ScriptedLLM(LLMResult(text="Move 60 units from Chennai."), LLMResult(text="Forecast note.")))
    d = (await async_client.get(f"/api/v1/analytics/redistribution?medication_id={world['med'].id}&explain=true",
                                headers=hdr(world["admin"]))).json()["data"]
    assert d["ai_explanation"] == "Move 60 units from Chennai."
    sent = llm.calls[0]["contents"][0]["parts"][0]["text"]
    assert not UUID_RE.findall(sent) and "recommended_quantity" in sent
    f = (await async_client.get(f"/api/v1/analytics/federation/forecast?facility_id={world['chg'].id}&explain=true",
                                headers=hdr(world["admin"]))).json()["data"]
    assert f["ai_explanation"] == "Forecast note."


@pytest.mark.asyncio
async def test_vertex_backend_is_optional_and_never_fabricates(async_client, world):
    r = await async_client.get(f"/api/v1/analytics/federation/forecast?facility_id={world['chg'].id}&backend=vertex",
                               headers=hdr(world["admin"]))
    assert r.status_code == 501 and r.json()["code"] == "VERTEX_NOT_CONFIGURED"
    ok = await async_client.get(f"/api/v1/analytics/federation/forecast?facility_id={world['chg'].id}", headers=hdr(world["admin"]))
    assert ok.status_code == 200 and ok.json()["data"]["items"][0]["backend"] == "local-statistical"
