import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, seeded_data):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.gov.in", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient, seeded_data):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.gov.in", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTHENTICATION_FAILED"
    assert "detail" in body


@pytest.mark.asyncio
async def test_refresh_token_rotation(async_client: AsyncClient, seeded_data):
    # 1. Login to get refresh token
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.gov.in", "password": "AdminPass123!"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    # 2. Use refresh token to rotate
    refresh_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()["data"]
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token

    # 3. Old refresh token should now be burned/revoked (Replay attack defense)
    replay_res = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replay_res.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_me(async_client: AsyncClient, seeded_data):
    headers = {"Authorization": f"Bearer {seeded_data['doctor_token']}"}
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["email"] == "doctor@test.gov.in"
    assert "DOCTOR" in body["roles"]
    assert "consultations.conduct" in body["permissions"]
    assert "prescriptions.create" in body["permissions"]
    # Doctor should NOT have administrative user management permissions
    assert "identity.user.create" not in body["permissions"]


@pytest.mark.asyncio
async def test_register_patient(async_client: AsyncClient, seeded_data):
    payload = {
        "email": "citizen.priya@example.com",
        "password": "SecurePassword123!",
        "full_name": "Priya Ramanathan",
        "phone_number": "+919840123456",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["email"] == "citizen.priya@example.com"
    assert body["full_name"] == "Priya Ramanathan"
    assert body["is_active"] is True
