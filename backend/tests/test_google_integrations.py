"""Google integrations (Maps, BigQuery, service-account auth). No real Google traffic: httpx.MockTransport / fakes."""
import json
import uuid
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
import pytest_asyncio

from app.ai import safety
from app.core.config import settings
from app.core.permissions import SystemPermissions as P
from app.core.security import create_access_token, get_password_hash
from app.integrations.google import auth as gauth
from app.integrations.google.bigquery import (
    EXPORT_COLUMN_NAMES, BigQueryClient, collect_facility_aggregates, get_bigquery_client,
)
from app.integrations.google.errors import GoogleError, NotConfigured
from app.integrations.google.maps import (
    FacilityPoint, GoogleMapsClient, RouteLeg, get_maps_client, haversine_km, rank_nearest,
)
from app.main import app
from app.models.facility import Facility, FacilityType
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole

SECRET = "SECRET-KEY-VALUE-123"


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    safety.rate_limiter.reset()
    for name in ("GOOGLE_MAPS_API_KEY", "GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS",
                 "BIGQUERY_DATASET", "GOOGLE_CLOUD_PROJECT", "GEMINI_API_KEY", "GOOGLE_CLOUD_API_KEY"):
        monkeypatch.setattr(settings, name, "")
    gauth.clear_cache()
    yield
    safety.rate_limiter.reset()
    app.dependency_overrides.pop(get_maps_client, None)
    app.dependency_overrides.pop(get_bigquery_client, None)


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


# ----------------------------------------------------------------------------- pure logic
def test_haversine_known_distance():
    # Chennai -> Bengaluru is roughly 290 km in a straight line.
    d = haversine_km(13.0827, 80.2707, 12.9716, 77.5946)
    assert 280 < d < 300
    assert haversine_km(10, 10, 10, 10) == 0


def _pts():
    return [
        FacilityPoint("far", "Far", "F", "PHC", "TN", "A", 13.5, 80.5),
        FacilityPoint("near", "Near", "N", "PHC", "TN", "A", 13.01, 80.01),
        FacilityPoint("mid", "Mid", "M", "PHC", "TN", "A", 13.2, 80.2),
    ]


class FakeMaps:
    def __init__(self, configured, legs=None, fail=False):
        self.configured, self.legs, self.fail, self.calls = configured, legs or {}, fail, []

    def is_configured(self):
        return self.configured

    async def geocode(self, address):
        return (13.0, 80.0, "Somewhere")

    async def route_matrix(self, origin, destinations):
        self.calls.append((origin, list(destinations)))
        if self.fail:
            raise GoogleError("boom")
        return self.legs


@pytest.mark.asyncio
async def test_rank_haversine_only_when_not_configured():
    method, rows = await rank_nearest(FakeMaps(False), 13.0, 80.0, _pts(), 3)
    assert method == "haversine_only"
    assert [r["facility"].id for r in rows] == ["near", "mid", "far"]
    assert all(r["driving_minutes"] is None for r in rows)


@pytest.mark.asyncio
async def test_rank_refined_by_routes_reorders_by_driving_time():
    # Shortlist order is straight-line: near(0), mid(1), far(2). Routes says mid is faster than near.
    legs = {0: RouteLeg(30_000, 3000), 1: RouteLeg(9_000, 600), 2: RouteLeg(80_000, 4000)}
    fake = FakeMaps(True, legs)
    method, rows = await rank_nearest(fake, 13.0, 80.0, _pts(), 3)
    assert method == "google_routes"
    assert [r["facility"].id for r in rows] == ["mid", "near", "far"]
    assert rows[0]["driving_minutes"] == 10.0 and rows[0]["driving_distance_km"] == 9.0
    assert len(fake.calls) == 1


@pytest.mark.asyncio
async def test_rank_falls_back_when_routes_fails():
    method, rows = await rank_nearest(FakeMaps(True, fail=True), 13.0, 80.0, _pts(), 2)
    assert method == "haversine_only"
    assert [r["facility"].id for r in rows] == ["near", "mid"]


# ----------------------------------------------------------------------------- maps request shapes
@pytest.mark.asyncio
async def test_maps_client_requires_key_and_uses_header_not_url():
    with pytest.raises(NotConfigured):
        await GoogleMapsClient(api_key="").geocode("x")

    seen = []

    def handler(req: httpx.Request):
        seen.append(req)
        if "geocode" in req.url.path:
            return httpx.Response(200, json={"status": "OK", "results": [
                {"formatted_address": "Kovalam, TN", "geometry": {"location": {"lat": 12.79, "lng": 80.25}}}]})
        return httpx.Response(200, json=[
            {"originIndex": 0, "destinationIndex": 1, "duration": "660s", "distanceMeters": 7000,
             "condition": "ROUTE_EXISTS"},
            {"originIndex": 0, "destinationIndex": 0, "condition": "ROUTE_NOT_FOUND"}])

    client = GoogleMapsClient(api_key=SECRET, transport=httpx.MockTransport(handler))
    assert await client.geocode("Kovalam") == (12.79, 80.25, "Kovalam, TN")
    legs = await client.route_matrix((12.8, 80.2), [(12.9, 80.3), (13.0, 80.4)])
    assert legs == {1: RouteLeg(7000, 660)}
    assert seen[0].url.params["key"] == SECRET            # Geocoding only accepts the key as a query parameter
    assert seen[1].headers["x-goog-api-key"] == SECRET    # Routes takes it in a header and never in the URL
    assert SECRET not in str(seen[1].url)
    assert seen[1].method == "POST"
    body = json.loads(seen[1].content)
    assert body["travelMode"] == "DRIVE" and len(body["destinations"]) == 2
    assert "X-Goog-FieldMask" in seen[1].headers


@pytest.mark.asyncio
async def test_geocode_zero_results_is_none():
    t = httpx.MockTransport(lambda r: httpx.Response(200, json={"status": "ZERO_RESULTS", "results": []}))
    assert await GoogleMapsClient(api_key="k", transport=t).geocode("zzz") is None


# ----------------------------------------------------------------------------- service-account auth
@pytest.mark.asyncio
async def test_auth_not_configured_and_bad_json(monkeypatch):
    with pytest.raises(NotConfigured):
        await gauth.get_access_token(["s"])
    monkeypatch.setattr(settings, "GOOGLE_SERVICE_ACCOUNT_JSON", "{not json")
    with pytest.raises(NotConfigured):
        await gauth.get_access_token(["s"])
    monkeypatch.setattr(settings, "GOOGLE_SERVICE_ACCOUNT_JSON", "")
    monkeypatch.setattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", "/no/such/file.json")
    with pytest.raises(NotConfigured):
        await gauth.get_access_token(["s"])


@pytest.mark.asyncio
async def test_auth_caches_tokens(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_SERVICE_ACCOUNT_JSON", "{}")
    calls = []

    def fake_refresh(scopes):
        calls.append(scopes)
        return f"tok{len(calls)}", datetime.now(timezone.utc) + timedelta(hours=1)

    monkeypatch.setattr(gauth, "_refresh_blocking", fake_refresh)
    assert await gauth.get_access_token(["a"]) == "tok1"
    assert await gauth.get_access_token(["a"]) == "tok1"
    assert await gauth.get_access_token(["b"]) == "tok2"
    assert len(calls) == 2


# ----------------------------------------------------------------------------- BigQuery client
def _bq(handler, monkeypatch):
    async def fake_token(scopes):
        return "BQ-TOKEN"

    monkeypatch.setattr("app.integrations.google.bigquery.get_access_token", fake_token)
    return BigQueryClient(project="proj", dataset="ds", table="tbl", transport=httpx.MockTransport(handler))


def _row(**over):
    row = {n: None for n in EXPORT_COLUMN_NAMES}
    row.update(facility_id="f1", aggregate_date="2026-01-02", appointments=3)
    row.update(over)
    return row


@pytest.mark.asyncio
async def test_bigquery_not_configured_raises():
    with pytest.raises(NotConfigured):
        await BigQueryClient(project="", dataset="").ensure_table()
    with pytest.raises(NotConfigured):
        await BigQueryClient(project="p", dataset="bad name; drop").ensure_table()
    assert BigQueryClient(project="p", dataset="d").is_configured() is False  # no credentials


@pytest.mark.asyncio
async def test_bigquery_creates_dataset_and_table_and_inserts(monkeypatch):
    seen = []

    def handler(req: httpx.Request):
        seen.append((req.method, req.url.path, json.loads(req.content) if req.content else None, req))
        if req.method == "GET":
            return httpx.Response(404, json={"error": {"code": 404}})
        return httpx.Response(200, json={})

    client = _bq(handler, monkeypatch)
    await client.ensure_table()
    n = await client.insert_rows([_row()])
    assert n == 1
    paths = [(m, p) for m, p, _, _ in seen]
    assert ("POST", "/bigquery/v2/projects/proj/datasets") in paths
    assert ("POST", "/bigquery/v2/projects/proj/datasets/ds/tables") in paths
    assert paths[-1] == ("POST", "/bigquery/v2/projects/proj/datasets/ds/tables/tbl/insertAll")
    for _, _, _, req in seen:
        assert req.headers["authorization"] == "Bearer BQ-TOKEN"
        assert "key=" not in str(req.url)
    table_body = [b for m, p, b, _ in seen if p.endswith("/tables") and m == "POST"][0]
    assert [f["name"] for f in table_body["schema"]["fields"]] == EXPORT_COLUMN_NAMES
    insert_body = seen[-1][2]
    assert insert_body["rows"][0]["insertId"] == "f1:2026-01-02"


@pytest.mark.asyncio
async def test_bigquery_insert_errors_and_unapproved_columns(monkeypatch):
    client = _bq(lambda r: httpx.Response(200, json={"insertErrors": [{"index": 0}]}), monkeypatch)
    with pytest.raises(GoogleError):
        await client.insert_rows([_row()])
    with pytest.raises(GoogleError):
        await client.insert_rows([_row(patient_id="p1")])


@pytest.mark.asyncio
async def test_bigquery_summary_query_is_parameterised(monkeypatch):
    captured = {}

    def handler(req):
        captured["body"] = json.loads(req.content)
        return httpx.Response(200, json={"jobComplete": True,
                                         "schema": {"fields": [{"name": "state"}, {"name": "facilities"},
                                                               {"name": "appointments"}]},
                                         "rows": [{"f": [{"v": "Tamil Nadu"}, {"v": "2"}, {"v": "41"}]}]})

    client = _bq(handler, monkeypatch)
    rows = await client.query_national_summary(date(2026, 1, 1), date(2026, 1, 31), "Tamil Nadu'; DROP", None)
    assert rows == [{"state": "Tamil Nadu", "facilities": 2, "appointments": 41}]
    body = captured["body"]
    assert "DROP" not in body["query"] and "@state" in body["query"]
    assert body["useLegacySql"] is False and body["parameterMode"] == "NAMED"
    assert {p["name"] for p in body["queryParameters"]} == {"date_from", "date_to", "state"}


# ----------------------------------------------------------------------------- no PII
def test_export_schema_has_no_patient_or_person_fields():
    banned = ("patient", "name", "phone", "email", "aadhaar", "abha", "dob", "birth", "diagnos", "user_id",
              "doctor", "staff_id", "address")
    for col in EXPORT_COLUMN_NAMES:
        assert not any(b in col for b in banned), col
    assert "facility_id" in EXPORT_COLUMN_NAMES


# ----------------------------------------------------------------------------- endpoints
class FakeBQ:
    def __init__(self):
        self.rows, self.summary_args, self.ensured = [], None, False

    def is_configured(self):
        return True

    async def ensure_table(self):
        self.ensured = True

    async def insert_rows(self, rows):
        self.rows = list(rows)
        return len(rows)

    async def query_national_summary(self, date_from, date_to, state, district):
        self.summary_args = (state, district)
        return [{"state": state or "ALL", "facilities": 1}]


@pytest_asyncio.fixture
async def world(db_session, seeded_data):
    """Second facility in another district and another state, plus a district-scoped governance user."""
    org, fac = seeded_data["org"], seeded_data["facility"]
    fac.latitude, fac.longitude = 12.7900000, 80.2500000
    other_d = Facility(id=uuid.uuid4(), organization_id=org.id, name="Other District PHC", code="OD-1",
                       facility_type=FacilityType.PHC, state="Tamil Nadu", district="Madurai",
                       latitude=9.9252, longitude=78.1198, is_active=True)
    other_s = Facility(id=uuid.uuid4(), organization_id=org.id, name="Other State PHC", code="OS-1",
                       facility_type=FacilityType.CHC, state="Kerala", district="Kochi",
                       latitude=9.9312, longitude=76.2673, is_active=True)
    db_session.add_all([other_d, other_s])
    perm = (await db_session.execute(
        __import__("sqlalchemy").select(Permission).where(Permission.code == P.GOVERNANCE_REPORT_GENERATE))).scalar_one()
    role = Role(id=uuid.uuid4(), name="District Officer", code="DIST_OFF", is_system=False, is_active=True)
    db_session.add(role)
    await db_session.flush()
    db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    officer = User(id=uuid.uuid4(), email="dho@test.gov.in", hashed_password=get_password_hash("Pass12345!"),
                   full_name="DHO", organization_id=org.id, facility_id=fac.id, is_active=True, is_verified=True)
    db_session.add(officer)
    await db_session.flush()
    db_session.add(UserRole(user_id=officer.id, role_id=role.id, organization_id=org.id, facility_id=fac.id,
                            scope_level=ScopeLevel.DISTRICT))
    await db_session.commit()
    return {**seeded_data, "other_d": other_d, "other_s": other_s,
            "officer_token": create_access_token(officer.id, extra_claims={"email": officer.email})}


@pytest.mark.asyncio
async def test_endpoints_require_auth(async_client):
    assert (await async_client.get("/api/v1/google/status")).status_code in (401, 403)
    assert (await async_client.post("/api/v1/google/maps/nearest-facilities", json={"latitude": 1, "longitude": 1})
            ).status_code in (401, 403)
    assert (await async_client.post("/api/v1/google/bigquery/export", json={})).status_code in (401, 403)
    assert (await async_client.get("/api/v1/google/bigquery/national-summary")).status_code in (401, 403)


@pytest.mark.asyncio
async def test_status_is_booleans_and_reveals_no_secret(async_client, world, monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_MAPS_API_KEY", SECRET)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", SECRET + "G")
    monkeypatch.setattr(settings, "GOOGLE_CLOUD_PROJECT", "secret-project-id")
    monkeypatch.setattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", "/secret/path.json")
    r = await async_client.get("/api/v1/google/status", headers=hdr(world["doctor_token"]))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["maps"] is True and data["gemini"] is True and data["service_account"] is True
    assert data["bigquery"] is False  # no dataset
    assert all(isinstance(v, bool) for v in data.values())
    for secret in (SECRET, "secret-project-id", "/secret/path.json"):
        assert secret not in r.text


@pytest.mark.asyncio
async def test_bigquery_and_geocode_not_configured_503(async_client, world):
    r = await async_client.post("/api/v1/google/bigquery/export", json={}, headers=hdr(world["admin_token"]))
    assert r.status_code == 503 and "AI_NOT_CONFIGURED" in r.text
    r = await async_client.get("/api/v1/google/bigquery/national-summary", headers=hdr(world["admin_token"]))
    assert r.status_code == 503 and "AI_NOT_CONFIGURED" in r.text
    r = await async_client.post("/api/v1/google/maps/nearest-facilities", json={"address": "Kovalam beach"},
                                headers=hdr(world["doctor_token"]))
    assert r.status_code == 503 and "AI_NOT_CONFIGURED" in r.text


@pytest.mark.asyncio
async def test_nearest_facilities_without_key_uses_haversine(async_client, world):
    r = await async_client.post("/api/v1/google/maps/nearest-facilities",
                                json={"latitude": 12.8, "longitude": 80.2, "limit": 3},
                                headers=hdr(world["doctor_token"]))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["method"] == "haversine_only" and "not configured" in d["method_note"]
    names = [f["name"] for f in d["facilities"]]
    assert names[0] == "Test PHC Kovalam" and names[1] == "Other District PHC" and names[2] == "Other State PHC"
    assert d["facilities"][0]["straight_line_km"] < d["facilities"][1]["straight_line_km"]
    assert d["facilities"][0]["driving_minutes"] is None


@pytest.mark.asyncio
async def test_nearest_facilities_with_routes_refinement(async_client, world):
    # Routes says the Kerala CHC (destination index 2) is fastest.
    fake = FakeMaps(True, {0: RouteLeg(20_000, 1500), 1: RouteLeg(400_000, 30_000), 2: RouteLeg(5_000, 300)})
    app.dependency_overrides[get_maps_client] = lambda: fake
    r = await async_client.post("/api/v1/google/maps/nearest-facilities", json={"address": "Kovalam", "limit": 3},
                                headers=hdr(world["doctor_token"]))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["method"] == "google_routes" and d["origin_label"] == "Somewhere"
    assert d["facilities"][0]["name"] == "Other State PHC" and d["facilities"][0]["driving_minutes"] == 5.0


@pytest.mark.asyncio
async def test_nearest_facilities_validation(async_client, world):
    h = hdr(world["doctor_token"])
    assert (await async_client.post("/api/v1/google/maps/nearest-facilities", json={}, headers=h)).status_code == 422
    assert (await async_client.post("/api/v1/google/maps/nearest-facilities",
                                    json={"latitude": 95, "longitude": 0}, headers=h)).status_code == 422
    r = await async_client.post("/api/v1/google/maps/nearest-facilities",
                                json={"latitude": 1, "longitude": 1, "facility_type": "NOPE"}, headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_export_requires_governance_permission(async_client, world):
    app.dependency_overrides[get_bigquery_client] = lambda: FakeBQ()
    r = await async_client.post("/api/v1/google/bigquery/export", json={}, headers=hdr(world["doctor_token"]))
    assert r.status_code == 403
    r = await async_client.get("/api/v1/google/bigquery/national-summary", headers=hdr(world["doctor_token"]))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_export_scope_enforced_and_rows_anonymous(async_client, world):
    fake = FakeBQ()
    app.dependency_overrides[get_bigquery_client] = lambda: fake

    r = await async_client.post("/api/v1/google/bigquery/export", json={}, headers=hdr(world["officer_token"]))
    assert r.status_code == 200, r.text
    assert r.json()["data"]["rows_exported"] == 1  # only the officer's own district
    assert fake.ensured and fake.rows[0]["district"] == "Chengalpattu"
    assert set(fake.rows[0]) == set(EXPORT_COLUMN_NAMES)
    assert r.json()["data"]["beds_included"] is True

    r = await async_client.post("/api/v1/google/bigquery/export", json={}, headers=hdr(world["admin_token"]))
    assert r.status_code == 200
    assert {row["district"] for row in fake.rows} == {"Chengalpattu", "Madurai", "Kochi"}
    assert all(set(row) == set(EXPORT_COLUMN_NAMES) for row in fake.rows)


@pytest.mark.asyncio
async def test_summary_scope_comes_from_server_not_client(async_client, world):
    fake = FakeBQ()
    app.dependency_overrides[get_bigquery_client] = lambda: fake
    r = await async_client.get("/api/v1/google/bigquery/national-summary?state=Kerala&district=Kochi",
                               headers=hdr(world["officer_token"]))
    assert r.status_code == 200
    assert fake.summary_args == ("Tamil Nadu", "Chengalpattu")
    await async_client.get("/api/v1/google/bigquery/national-summary", headers=hdr(world["admin_token"]))
    assert fake.summary_args == (None, None)
    r = await async_client.get("/api/v1/google/bigquery/national-summary?date_from=2026-02-01&date_to=2026-01-01",
                               headers=hdr(world["admin_token"]))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_collect_aggregates_counts(db_session, world):
    from app.core.jurisdiction import Jurisdiction
    res = await collect_facility_aggregates(db_session, date(2026, 1, 2),
                                            Jurisdiction(ScopeLevel.GLOBAL, None, None, None))
    assert len(res.rows) == 3
    mine = [r for r in res.rows if r["district"] == "Chengalpattu"][0]
    assert mine["staff_assigned"] == 3 and mine["appointments"] == 0 and mine["staff_present"] == 0
