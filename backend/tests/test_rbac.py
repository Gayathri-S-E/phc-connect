import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_permission_denied_returns_403(async_client: AsyncClient, seeded_data):
    """Verify that a user without required permission is rejected with RFC 7807 403 Forbidden."""
    doctor_headers = {"Authorization": f"Bearer {seeded_data['doctor_token']}"}

    # Doctor does NOT have identity.user.create permission
    payload = {
        "email": "newnurse@test.gov.in",
        "password": "Password123!",
        "full_name": "Nurse Kavitha",
    }
    response = await async_client.post("/api/v1/users", json=payload, headers=doctor_headers)
    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "PERMISSION_DENIED"
    assert "Missing required permission" in body["detail"]


@pytest.mark.asyncio
async def test_permission_granted_succeeds(async_client: AsyncClient, seeded_data):
    """Verify that an administrator possessing identity.user.create succeeds."""
    admin_headers = {"Authorization": f"Bearer {seeded_data['admin_token']}"}

    payload = {
        "email": "nurse.anita@test.gov.in",
        "password": "Password123!",
        "full_name": "Nurse Anita",
        "facility_id": str(seeded_data["facility"].id),
    }
    response = await async_client.post("/api/v1/users", json=payload, headers=admin_headers)
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["email"] == "nurse.anita@test.gov.in"
    assert body["full_name"] == "Nurse Anita"


@pytest.mark.asyncio
async def test_dynamic_role_creation_and_assignment(async_client: AsyncClient, seeded_data):
    """Verify that roles and permissions can be dynamically defined in database and assigned."""
    admin_headers = {"Authorization": f"Bearer {seeded_data['admin_token']}"}

    # 1. Fetch available permissions to get their UUIDs
    perms_res = await async_client.get("/api/v1/permissions", headers=admin_headers)
    assert perms_res.status_code == 200
    all_perms = perms_res.json()["data"]
    inventory_read_perm = next(p for p in all_perms if p["code"] == "inventory.item.read")

    # 2. Create a new custom role 'PHC_INTERN' with only inventory.item.read
    role_payload = {
        "name": "PHC Intern",
        "code": "PHC_INTERN",
        "description": "Internship role with read-only inventory visibility",
        "permission_ids": [inventory_read_perm["id"]],
    }
    create_role_res = await async_client.post("/api/v1/roles", json=role_payload, headers=admin_headers)
    assert create_role_res.status_code == 201
    created_role = create_role_res.json()["data"]
    assert created_role["code"] == "PHC_INTERN"
    assert len(created_role["permissions"]) == 1

    # 3. Create a new user for intern
    user_payload = {
        "email": "intern@test.gov.in",
        "password": "Password123!",
        "full_name": "Intern Rajesh",
        "initial_role_ids": [created_role["id"]],
    }
    user_res = await async_client.post("/api/v1/users", json=user_payload, headers=admin_headers)
    assert user_res.status_code == 201

    # 4. Login as the newly created intern
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "intern@test.gov.in", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    intern_token = login_res.json()["data"]["access_token"]
    intern_headers = {"Authorization": f"Bearer {intern_token}"}

    # 5. Check intern's granted permissions via /auth/me
    me_res = await async_client.get("/api/v1/auth/me", headers=intern_headers)
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert "PHC_INTERN" in me_data["roles"]
    assert "inventory.item.read" in me_data["permissions"]
    # Intern must NOT have doctor or admin permissions
    assert "consultations.conduct" not in me_data["permissions"]
    assert "identity.user.create" not in me_data["permissions"]
