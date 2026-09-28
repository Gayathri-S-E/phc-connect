"""
Test Suite — Role 06: Facility Admin / MPHS Portal
===================================================
Tests: cold chain equipment registration + logging + excursion,
outreach camp scheduling + completion, staff attendance summary,
complaint management, and monthly facility report.

All tests run against SQLite in-memory (via conftest seeded_data fixture).
"""

import uuid
from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.permissions import SystemPermissions
from app.models.healthcare import (
    AttendanceStatus,
    ComplaintStatus,
    FeedbackComplaint,
    Patient,
    StaffAttendance,
)


# ─── 1. Cold Chain Equipment Registration + Listing ────────────────────────────

@pytest.mark.asyncio
async def test_cold_chain_equipment_registration_and_listing(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Facility admin can register ILR equipment and list it."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]

    # Register equipment
    payload = {
        "equipment_type": "ILR",
        "serial_number": f"ILR-TN-{uuid.uuid4().hex[:8]}",
        "model_name": "Vestfrost VLS 100T",
        "min_temp_c": 2.0,
        "max_temp_c": 8.0,
    }
    resp = await async_client.post(
        f"/api/v1/facility-admin/cold-chain/equipment?facility_id={facility_id}",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()["data"]
    assert data["equipment_type"] == "ILR"
    assert data["serial_number"] == payload["serial_number"]
    assert data["is_functional"] is True
    assert data["is_temperature_in_range"] is True
    equipment_id = data["id"]

    # List equipment
    list_resp = await async_client.get(
        f"/api/v1/facility-admin/cold-chain/equipment?facility_id={facility_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    equipments = list_resp.json()["data"]
    assert any(e["id"] == equipment_id for e in equipments)


# ─── 2. Temperature Logging + Excursion Detection ──────────────────────────────

@pytest.mark.asyncio
async def test_temperature_logging_and_excursion_detection(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Temperature logs detect excursions when temp leaves valid range."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]

    # Register equipment
    serial = f"ILR-LOG-{uuid.uuid4().hex[:8]}"
    reg_resp = await async_client.post(
        f"/api/v1/facility-admin/cold-chain/equipment?facility_id={facility_id}",
        json={
            "equipment_type": "ILR",
            "serial_number": serial,
            "model_name": "Haier HYC-90",
            "min_temp_c": 2.0,
            "max_temp_c": 8.0,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert reg_resp.status_code == 201
    equip_id = reg_resp.json()["data"]["id"]

    # Log normal temperature (no excursion)
    normal_resp = await async_client.post(
        f"/api/v1/facility-admin/cold-chain/equipment/{equip_id}/log",
        json={"temperature_c": 5.0, "notes": "Morning reading"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert normal_resp.status_code == 201
    normal_log = normal_resp.json()["data"]
    assert normal_log["is_excursion"] is False
    assert normal_log["temperature_c"] == 5.0

    # Log excursion temperature (too high)
    exc_resp = await async_client.post(
        f"/api/v1/facility-admin/cold-chain/equipment/{equip_id}/log",
        json={"temperature_c": 11.5, "excursion_reason": "Power cut", "notes": "Afternoon reading"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert exc_resp.status_code == 201
    exc_log = exc_resp.json()["data"]
    assert exc_log["is_excursion"] is True
    assert exc_log["temperature_c"] == 11.5
    assert exc_log["excursion_reason"] == "Power cut"

    # Log history
    logs_resp = await async_client.get(
        f"/api/v1/facility-admin/cold-chain/equipment/{equip_id}/logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert logs_resp.status_code == 200
    logs = logs_resp.json()["data"]
    assert len(logs) >= 2
    excursion_logs = [l for l in logs if l["is_excursion"]]
    assert len(excursion_logs) >= 1


# ─── 3. Outreach Camp Scheduling + Completion ──────────────────────────────────

@pytest.mark.asyncio
async def test_outreach_camp_scheduling_and_completion(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Admin can schedule an outreach camp and mark it complete with beneficiary count."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]

    # Schedule a camp
    create_resp = await async_client.post(
        f"/api/v1/facility-admin/outreach-camps?facility_id={facility_id}",
        json={
            "camp_name": "Pallikaranai Village Immunization Camp",
            "target_village": "Pallikaranai",
            "scheduled_date": "2025-11-15",
            "target_beneficiaries": 80,
            "notes": "Focus on pregnant women and under-5 children",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201, f"{create_resp.status_code}: {create_resp.text}"
    camp = create_resp.json()["data"]
    assert camp["status"] == "SCHEDULED"
    assert camp["target_beneficiaries"] == 80
    assert camp["actual_beneficiaries_served"] == 0
    camp_id = camp["id"]

    # List camps
    list_resp = await async_client.get(
        f"/api/v1/facility-admin/outreach-camps?facility_id={facility_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    camps = list_resp.json()["data"]
    assert any(c["id"] == camp_id for c in camps)

    # Mark camp as completed
    complete_resp = await async_client.patch(
        f"/api/v1/facility-admin/outreach-camps/{camp_id}",
        json={"status": "COMPLETED", "actual_beneficiaries_served": 73, "notes": "Camp completed successfully"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert complete_resp.status_code == 200, f"{complete_resp.status_code}: {complete_resp.text}"
    updated_camp = complete_resp.json()["data"]
    assert updated_camp["status"] == "COMPLETED"
    assert updated_camp["actual_beneficiaries_served"] == 73


# ─── 4. Complaint Listing + Resolution ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_complaint_listing_and_resolution(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Facility admin can list complaints and mark one as resolved."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]
    admin_user = seeded_data["admin_user"]

    # Seed a complaint directly in DB
    import secrets
    now = datetime.now(timezone.utc)
    tracking = f"CMP-{now.strftime('%Y%m')}-{secrets.randbelow(90000) + 10000}"

    # Get or create patient
    patient_stmt = select(Patient).where(Patient.primary_facility_id == facility_id)
    patient = (await db_session.execute(patient_stmt)).scalar_one_or_none()
    if patient is None:
        patient = Patient(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            patient_identifier=f"PAT-{uuid.uuid4().hex[:6].upper()}",
            first_name="Anitha",
            last_name="Rajan",
            date_of_birth=date(1990, 1, 1),
            gender="FEMALE",
            phone_number="+919876543210",
            primary_facility_id=facility_id,
            is_active=True,
        )
        db_session.add(patient)
        await db_session.flush()

    complaint = FeedbackComplaint(
        id=uuid.uuid4(),
        tracking_number=tracking,
        patient_id=patient.id,
        facility_id=facility_id,
        category="SERVICE",
        subject="Long waiting time",
        description="Waited 3 hours for consultation",
        status=ComplaintStatus.SUBMITTED,
    )
    db_session.add(complaint)
    await db_session.commit()

    complaint_id = complaint.id

    # List complaints for facility
    list_resp = await async_client.get(
        f"/api/v1/facility-admin/complaints?facility_id={facility_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    complaints = list_resp.json()["data"]
    assert any(c["id"] == str(complaint_id) for c in complaints)

    # Resolve the complaint
    resolve_resp = await async_client.patch(
        f"/api/v1/facility-admin/complaints/{complaint_id}",
        json={
            "status": "RESOLVED",
            "resolution_notes": "Patient was counselled and appointment prioritised.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resolve_resp.status_code == 200, f"{resolve_resp.status_code}: {resolve_resp.text}"
    resolved = resolve_resp.json()["data"]
    assert resolved["status"] == "RESOLVED"
    assert "appointment prioritised" in resolved["resolution_notes"]


# ─── 5. Monthly Facility Report ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_monthly_facility_report(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Admin can generate a monthly HMIS-style facility performance report."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]

    # Request a monthly report for the current month/year
    now = datetime.now(timezone.utc)
    resp = await async_client.get(
        f"/api/v1/facility-admin/reports/monthly"
        f"?facility_id={facility_id}&month={now.month}&year={now.year}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text}"
    report = resp.json()["data"]

    # Structural assertions — all numeric fields must be present and non-negative
    assert report["facility_id"] == str(facility_id)
    assert report["report_month"] == now.month
    assert report["report_year"] == now.year
    assert report["total_opd_patients"] >= 0
    assert report["total_consultations"] >= 0
    assert report["total_lab_tests_ordered"] >= 0
    assert report["cold_chain_excursions"] >= 0
    assert report["outreach_camps_scheduled"] >= 0
    assert report["grievance_resolution_rate_percent"] >= 0


# ─── 6. Staff Attendance Admin View ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_staff_attendance_admin_view(
    async_client: AsyncClient,
    seeded_data: dict,
    db_session,
):
    """Facility admin can view staff attendance records for their facility."""
    facility_id = seeded_data["facility"].id
    admin_token = seeded_data["admin_token"]
    admin_user = seeded_data["admin_user"]

    # Seed a staff attendance record
    today = date.today()
    attendance = StaffAttendance(
        id=uuid.uuid4(),
        user_id=admin_user.id,
        facility_id=facility_id,
        attendance_date=today,
        check_in_time=datetime.now(timezone.utc),
        status=AttendanceStatus.PRESENT,
        shift="GENERAL",
    )
    db_session.add(attendance)
    await db_session.commit()

    resp = await async_client.get(
        f"/api/v1/facility-admin/staff-attendance"
        f"?facility_id={facility_id}&from_date={today}&to_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text}"
    records = resp.json()["data"]
    assert isinstance(records, list)
    assert any(r["user_id"] == str(admin_user.id) for r in records)
