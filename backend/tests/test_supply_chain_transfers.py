import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication
from app.models.pharmacy import StockTransferStatus


@pytest.mark.asyncio
async def test_two_phase_inter_facility_stock_transfer_pipeline(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    org = seeded_data["org"]
    source_fac = seeded_data["facility"]

    # 1. Create Destination Facility
    dest_fac = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test CHC Kelambakkam",
        code="TEST-CHC-002",
        facility_type=FacilityType.CHC,
        state="Tamil Nadu",
        district="Chengalpattu",
        is_active=True,
    )
    db_session.add(dest_fac)

    # 2. Create Medication & seed source facility inventory (100 units)
    med = Medication(
        id=uuid.uuid4(),
        name="Human Insulin 100IU",
        code="MED-INS-100",
        dosage_form="Vial",
        strength="100IU/ml",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    # Receive 100 units at source facility
    b_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(source_fac.id),
            "medication_id": str(med.id),
            "batch_number": "INS-LOT-999",
            "manufacture_date": str(date.today() - timedelta(days=45)),
            "expiry_date": str(date.today() + timedelta(days=240)),
            "quantity": 100,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b_res.status_code == 201

    # 3. Destination Facility requests 40 units from Source Facility
    req_res = await async_client.post(
        "/api/v1/transfers",
        json={
            "source_facility_id": str(source_fac.id),
            "destination_facility_id": str(dest_fac.id),
            "medication_id": str(med.id),
            "requested_quantity": 40,
            "notes": "Emergency stock requisition due to heatwave influx",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert req_res.status_code == 201, req_res.text
    transfer = req_res.json()["data"]
    transfer_id = transfer["id"]
    assert transfer["status"] == "REQUESTED"
    assert transfer["transfer_number"].startswith("TRF-")

    # 4. District / State Admin approves transfer
    appr_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/approve",
        json={"notes": "Approved by District Medical Officer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["data"]["status"] == "APPROVED"

    # 5. Source Facility dispatches transfer (Stock deducted -> IN_TRANSIT)
    disp_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/dispatch",
        json={"dispatched_quantity": 40, "notes": "Dispatched via cold-chain van TN-01-AB-1234"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disp_res.status_code == 200, disp_res.text
    assert disp_res.json()["data"]["status"] == "IN_TRANSIT"

    # Verify source facility stock has been deducted to 60
    source_inv_res = await async_client.get(
        f"/api/v1/inventory?facility_id={source_fac.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    source_item = next(i for i in source_inv_res.json()["data"] if i["medication_id"] == str(med.id))
    assert source_item["quantity_on_hand"] == 60

    # 6. Destination Facility receives transfer (Stock added -> RECEIVED)
    rec_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/receive",
        json={"received_quantity": 40, "notes": "Received in good condition at 4°C"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rec_res.status_code == 200, rec_res.text
    assert rec_res.json()["data"]["status"] == "RECEIVED"

    # Verify destination facility inventory now has 40 units
    dest_inv_res = await async_client.get(
        f"/api/v1/inventory?facility_id={dest_fac.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    dest_item = next(i for i in dest_inv_res.json()["data"] if i["medication_id"] == str(med.id))
    assert dest_item["quantity_on_hand"] == 40
    assert dest_item["available_quantity"] == 40

    # 7. Check Guardrails: Double receive must be rejected
    double_rec = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/receive",
        json={"received_quantity": 40},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert double_rec.status_code == 400


@pytest.mark.asyncio
async def test_shortage_incident_reporting_and_resolution(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # 1. Create Medication
    med = Medication(
        id=uuid.uuid4(),
        name="Rabies Vaccine Human 2.5IU",
        code="MED-RAB-25",
        dosage_form="Vial",
        strength="2.5IU",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    # 2. Report Shortage Incident
    report_res = await async_client.post(
        "/api/v1/shortages",
        json={
            "facility_id": str(facility.id),
            "medication_id": str(med.id),
            "severity": "CRITICAL",
            "description": "Zero vials on hand following local animal bite outbreak; urgent replenishment required",
            "estimated_impact_patients": 25,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert report_res.status_code == 201, report_res.text
    inc = report_res.json()["data"]
    inc_id = inc["id"]
    assert inc["incident_number"].startswith("SHT-")
    assert inc["severity"] == "CRITICAL"
    assert inc["status"] == "REPORTED"

    # 3. Resolve Shortage Incident
    res_res = await async_client.patch(
        f"/api/v1/shortages/{inc_id}/resolve",
        json={"resolution_notes": "Emergency courier delivered 50 vials from State Medical Depot"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_res.status_code == 200
    resolved = res_res.json()["data"]
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_at"] is not None
