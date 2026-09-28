import asyncio
import os
import sys
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db_session
from app.core.permissions import SystemPermissions
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.facility import Facility, FacilityType
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.models.organization import Organization, OrganizationType

from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()



@pytest_asyncio.fixture(scope="function")
async def seeded_data(db_session: AsyncSession):
    """Seed foundational permissions, roles, and test users."""
    # 1. Organization & Facility
    org = Organization(
        id=uuid.uuid4(),
        name="Test Health Directorate",
        code="TEST-ORG-01",
        org_type=OrganizationType.STATE_HEALTH_DEPT,
        is_active=True,
    )
    db_session.add(org)
    await db_session.flush()

    fac = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test PHC Kovalam",
        code="TEST-PHC-001",
        facility_type=FacilityType.PHC,
        state="Tamil Nadu",
        district="Chengalpattu",
        is_active=True,
    )
    db_session.add(fac)
    await db_session.flush()

    # 2. Permissions
    perm_map = {}
    for code in SystemPermissions.all_permissions():
        parts = code.split(".")
        p = Permission(
            id=uuid.uuid4(),
            code=code,
            module=parts[0],
            resource=parts[1] if len(parts) > 1 else "res",
            action=parts[2] if len(parts) > 2 else "act",
            is_active=True,
        )
        db_session.add(p)
        perm_map[code] = p
    await db_session.flush()

    # 3. Roles
    admin_role = Role(
        id=uuid.uuid4(),
        name="Super Administrator",
        code="SUPER_ADMIN",
        is_system=True,
        is_active=True,
    )
    doctor_role = Role(
        id=uuid.uuid4(),
        name="Medical Officer",
        code="DOCTOR",
        is_system=True,
        is_active=True,
    )
    db_session.add_all([admin_role, doctor_role])
    await db_session.flush()

    # Map all permissions to admin
    for p in perm_map.values():
        db_session.add(RolePermission(role_id=admin_role.id, permission_id=p.id))

    # Map doctor permissions
    doctor_perms = [
        SystemPermissions.PATIENTS_PROFILE_READ,
        SystemPermissions.PATIENTS_RECORDS_READ,
        SystemPermissions.APPOINTMENTS_VIEW,
        SystemPermissions.CONSULTATIONS_CONDUCT,
        SystemPermissions.PRESCRIPTIONS_CREATE,
        SystemPermissions.PRESCRIPTIONS_READ,
        SystemPermissions.LABS_ORDER_CREATE,
        SystemPermissions.LABS_ORDER_READ,
    ]
    for dp_code in doctor_perms:
        db_session.add(RolePermission(role_id=doctor_role.id, permission_id=perm_map[dp_code].id))

    await db_session.flush()

    # 4. Users
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@test.gov.in",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    doctor_user = User(
        id=uuid.uuid4(),
        email="doctor@test.gov.in",
        hashed_password=get_password_hash("DoctorPass123!"),
        full_name="Dr. Suresh",
        organization_id=org.id,
        facility_id=fac.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([admin_user, doctor_user])
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=admin_user.id,
            role_id=admin_role.id,
            organization_id=org.id,
            facility_id=fac.id,
            scope_level=ScopeLevel.GLOBAL,
        )
    )
    db_session.add(
        UserRole(
            user_id=doctor_user.id,
            role_id=doctor_role.id,
            organization_id=org.id,
            facility_id=fac.id,
            scope_level=ScopeLevel.FACILITY,
        )
    )
    await db_session.commit()

    return {
        "org": org,
        "facility": fac,
        "admin_user": admin_user,
        "doctor_user": doctor_user,
        "admin_token": create_access_token(admin_user.id, extra_claims={"email": admin_user.email}),
        "doctor_token": create_access_token(doctor_user.id, extra_claims={"email": doctor_user.email}),
    }
