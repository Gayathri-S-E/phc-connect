import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.healthcare import Medication, Prescription, PrescriptionItem, PrescriptionItemStatus, PrescriptionStatus
from app.models.pharmacy import BatchStatus, InventoryBatch, InventoryItem, StockMovementType


@pytest.mark.asyncio
async def test_stock_receipt_creates_batch_and_movement(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # 1. Create a Medication in the master catalog
    med = Medication(
        id=uuid.uuid4(),
        name="Amoxicillin 500mg",
        code="MED-AMOX-500",
        dosage_form="Capsule",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    # 2. Receive Stock (Batch receipt)
    expiry = date.today() + timedelta(days=180)
    receipt_payload = {
        "facility_id": str(facility.id),
        "medication_id": str(med.id),
        "batch_number": "BATCH-AMOX-001",
        "manufacture_date": str(date.today() - timedelta(days=30)),
        "expiry_date": str(expiry),
        "quantity": 100,
        "supplier_name": "Tamil Nadu Medical Services Corp",
        "notes": "Initial monthly consignment",
    }

    res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json=receipt_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["batch_number"] == "BATCH-AMOX-001"
    assert data["current_quantity"] == 100
    assert data["status"] == "AVAILABLE"

    # 3. Verify Inventory Item quantity_on_hand updated
    inv_res = await async_client.get(
        f"/api/v1/inventory?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert inv_res.status_code == 200
    inv_items = inv_res.json()["data"]
    amox_item = next((i for i in inv_items if i["medication_id"] == str(med.id)), None)
    assert amox_item is not None
    assert amox_item["quantity_on_hand"] == 100
    assert amox_item["available_quantity"] == 100

    # 4. Verify Stock Movement entry in immutable ledger
    mov_res = await async_client.get(
        f"/api/v1/inventory/movements?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert mov_res.status_code == 200
    movements = mov_res.json()["data"]
    assert len(movements) >= 1
    receipt_mov = next((m for m in movements if m["movement_type"] == "RECEIPT"), None)
    assert receipt_mov is not None
    assert receipt_mov["quantity"] == 100
    assert receipt_mov["balance_after"] == 100


@pytest.mark.asyncio
async def test_stock_adjustment_deducts_inventory_and_logs_damage(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # 1. Create Medication & receive 50 units
    med = Medication(
        id=uuid.uuid4(),
        name="Paracetamol 650mg",
        code="MED-PARA-650",
        dosage_form="Tablet",
        strength="650mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    receipt_payload = {
        "facility_id": str(facility.id),
        "medication_id": str(med.id),
        "batch_number": "BATCH-PARA-101",
        "manufacture_date": str(date.today() - timedelta(days=20)),
        "expiry_date": str(date.today() + timedelta(days=365)),
        "quantity": 50,
        "supplier_name": "District Drug Warehouse",
    }
    rc_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json=receipt_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rc_res.status_code == 201
    batch_id = rc_res.json()["data"]["id"]

    # 2. Adjust stock down due to water damage (5 units)
    adjust_payload = {
        "batch_id": batch_id,
        "quantity": -5,
        "movement_type": "DAMAGE",
        "notes": "Rainwater seepage damaged outer packaging on 5 strips",
    }
    adj_res = await async_client.post(
        "/api/v1/inventory/batches/adjust",
        json=adjust_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert adj_res.status_code == 200, adj_res.text
    movement_data = adj_res.json()["data"]
    assert movement_data["quantity"] == -5
    assert movement_data["balance_after"] == 45
    assert movement_data["movement_type"] == "DAMAGE"

    # 3. Check batch current_quantity
    batches_res = await async_client.get(
        f"/api/v1/inventory/batches?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert batches_res.status_code == 200
    batch = next((b for b in batches_res.json()["data"] if b["id"] == batch_id), None)
    assert batch is not None
    assert batch["current_quantity"] == 45


@pytest.mark.asyncio
async def test_atomic_fefo_multi_batch_dispensing(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]
    doctor = seeded_data["doctor_user"]

    # 1. Create Medication
    med = Medication(
        id=uuid.uuid4(),
        name="Metformin 500mg",
        code="MED-MET-500",
        dosage_form="Tablet",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.commit()

    # 2. Receive 2 Batches with DIFFERENT expiry dates
    # Batch 1: Earlier expiry (30 days), quantity 20
    b1_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(facility.id),
            "medication_id": str(med.id),
            "batch_number": "MET-EXP-SOON",
            "manufacture_date": str(date.today() - timedelta(days=60)),
            "expiry_date": str(date.today() + timedelta(days=30)),
            "quantity": 20,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b1_res.status_code == 201
    b1_id = b1_res.json()["data"]["id"]

    # Batch 2: Later expiry (180 days), quantity 40
    b2_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(facility.id),
            "medication_id": str(med.id),
            "batch_number": "MET-EXP-LATER",
            "manufacture_date": str(date.today() - timedelta(days=30)),
            "expiry_date": str(date.today() + timedelta(days=180)),
            "quantity": 40,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b2_res.status_code == 201
    b2_id = b2_res.json()["data"]["id"]

    # 3. Create Patient & Prescription for 35 units
    from app.models.healthcare import Patient
    patient = Patient(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_identifier="PAT-MET-001",
        first_name="Ramesh",
        last_name="Kumar",
        date_of_birth=date(1975, 4, 12),
        gender="MALE",
        phone_number="+919876543210",
        is_active=True,
    )
    db_session.add(patient)
    await db_session.flush()

    from app.models.healthcare import Consultation
    consultation = Consultation(
        id=uuid.uuid4(),
        facility_id=facility.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        chief_complaint="Type 2 Diabetes follow-up",
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(consultation)
    await db_session.flush()

    prescription = Prescription(
        id=uuid.uuid4(),
        facility_id=facility.id,
        consultation_id=consultation.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        status=PrescriptionStatus.ISSUED,
    )
    db_session.add(prescription)
    await db_session.flush()

    rx_item = PrescriptionItem(
        id=uuid.uuid4(),
        prescription_id=prescription.id,
        medication_id=med.id,
        medication_name="Metformin 500mg",
        dosage="500mg",
        frequency="Twice daily",
        duration_days=30,
        quantity_prescribed=35,
        quantity_dispensed=0,
        status=PrescriptionItemStatus.PENDING,
    )
    db_session.add(rx_item)
    await db_session.commit()

    # 4. Perform FEFO Dispensing: Dispense 35 units
    # FEFO Engine must allocate:
    # 20 units from Batch 1 (MET-EXP-SOON, which depletes it)
    # 15 units from Batch 2 (MET-EXP-LATER, leaving 25 units)
    dispense_payload = {
        "items": [
            {
                "prescription_item_id": str(rx_item.id),
                "quantity": 35,
            }
        ],
        "notes": "Dispensed to patient attendant with dietary instructions",
    }
    disp_res = await async_client.post(
        f"/api/v1/prescriptions/{prescription.id}/dispense-fefo",
        json=dispense_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disp_res.status_code == 200, disp_res.text
    disp_records = disp_res.json()["data"]
    assert len(disp_records) == 1
    rec = disp_records[0]
    assert rec["quantity_dispensed"] == 35
    assert len(rec["allocations"]) == 2

    alloc_b1 = next((a for a in rec["allocations"] if a["batch_id"] == b1_id), None)
    alloc_b2 = next((a for a in rec["allocations"] if a["batch_id"] == b2_id), None)
    assert alloc_b1 is not None and alloc_b1["allocated_quantity"] == 20
    assert alloc_b2 is not None and alloc_b2["allocated_quantity"] == 15

    # 5. Check Batch 1 status: DEPLETED, current_quantity: 0
    batches_res = await async_client.get(
        f"/api/v1/inventory/batches?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    batches = batches_res.json()["data"]
    b1_after = next(b for b in batches if b["id"] == b1_id)
    b2_after = next(b for b in batches if b["id"] == b2_id)
    assert b1_after["current_quantity"] == 0
    assert b1_after["status"] == "DEPLETED"
    assert b2_after["current_quantity"] == 25
    assert b2_after["status"] == "AVAILABLE"

    # 6. Check Inventory total on hand: 20 + 40 - 35 = 25
    inv_res = await async_client.get(
        f"/api/v1/inventory?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    inv_item = next(i for i in inv_res.json()["data"] if i["medication_id"] == str(med.id))
    assert inv_item["quantity_on_hand"] == 25
    assert inv_item["available_quantity"] == 25

    # 7. Check Over-dispensing protection: Attempting to dispense more than prescribed must fail
    over_res = await async_client.post(
        f"/api/v1/prescriptions/{prescription.id}/dispense-fefo",
        json={
            "items": [
                {
                    "prescription_item_id": str(rx_item.id),
                    "quantity": 10,
                }
            ]
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert over_res.status_code == 400
