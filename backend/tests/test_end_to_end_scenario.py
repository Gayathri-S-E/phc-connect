import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication, DiagnosisCode
from app.models.pharmacy import StockTransferStatus


@pytest.mark.asyncio
async def test_section_73_complete_end_to_end_scenario(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    """
    Executes the exact 29-step lifecycle connecting:
    SMART HEALTH + PHARMACY + SUPPLY CHAIN RESILIENCE
    """
    admin_token = seeded_data["admin_token"]
    org = seeded_data["org"]
    phc_facility = seeded_data["facility"]
    doctor = seeded_data["doctor_user"]

    # ------------------------------------------------------------------------
    # STEP 0: Set up Reference Data & Facilities
    # ------------------------------------------------------------------------
    # Warehouse facility for replenishment
    warehouse = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="District Drug Depot Chengalpattu",
        code="DIST-DEPOT-001",
        facility_type=FacilityType.DISTRICT_WAREHOUSE,
        state="Tamil Nadu",
        district="Chengalpattu",
        is_active=True,
    )
    # Master Medication
    med = Medication(
        id=uuid.uuid4(),
        generic_name="Amoxicillin + Clavulanate 625mg",
        dosage_form="Tablet",
        strength="625mg",
        route="Oral",
        unit="Tablet",
        is_active=True,
    )
    # Diagnosis Code
    diag_code = DiagnosisCode(
        id=uuid.uuid4(),
        code="J18.9",
        description="Pneumonia, unspecified organism",
        category="Respiratory",
        version="ICD-10",
        is_active=True,
    )
    db_session.add_all([warehouse, med, diag_code])
    await db_session.commit()

    # Pre-seed PHC stock with 2 batches (total 50 units):
    # Batch A (earlier expiry, 20 units)
    # Batch B (later expiry, 30 units)
    # Reorder level is set to 40 so that dispensing 25 units drops on_hand from 50 -> 25 (triggering LOW_STOCK)
    b_early_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(phc_facility.id),
            "medication_id": str(med.id),
            "batch_number": "AUG-BATCH-EARLY",
            "manufacture_date": str(date.today() - timedelta(days=90)),
            "expiry_date": str(date.today() + timedelta(days=45)),
            "quantity": 20,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b_early_res.status_code == 201
    b_early_id = b_early_res.json()["data"]["id"]

    b_late_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(phc_facility.id),
            "medication_id": str(med.id),
            "batch_number": "AUG-BATCH-LATER",
            "manufacture_date": str(date.today() - timedelta(days=30)),
            "expiry_date": str(date.today() + timedelta(days=200)),
            "quantity": 30,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert b_late_res.status_code == 201
    b_late_id = b_late_res.json()["data"]["id"]

    # Pre-seed Warehouse with 500 units for transfer
    wh_batch_res = await async_client.post(
        "/api/v1/inventory/batches/receive",
        json={
            "facility_id": str(warehouse.id),
            "medication_id": str(med.id),
            "batch_number": "AUG-WH-DEPOT-1",
            "manufacture_date": str(date.today() - timedelta(days=20)),
            "expiry_date": str(date.today() + timedelta(days=365)),
            "quantity": 500,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert wh_batch_res.status_code == 201

    # ------------------------------------------------------------------------
    # STEP 1: Patient registered
    # ------------------------------------------------------------------------
    pat_res = await async_client.post(
        "/api/v1/patients",
        json={
            "first_name": "Murugan",
            "last_name": "Selvam",
            "date_of_birth": "1988-11-20",
            "gender": "MALE",
            "phone_number": "+919444123456",
            "primary_facility_id": str(phc_facility.id),
            "address": "42 Beach Road, Kovalam",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pat_res.status_code == 201, pat_res.text
    patient = pat_res.json()["data"]
    patient_id = patient["id"]

    # ------------------------------------------------------------------------
    # STEP 2: Patient gets appointment
    # ------------------------------------------------------------------------
    appt_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    appt_res = await async_client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "facility_id": str(phc_facility.id),
            "appointment_date": appt_time,
            "reason": "Persistent productive cough and fever",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert appt_res.status_code == 201
    appointment_id = appt_res.json()["data"]["id"]

    # ------------------------------------------------------------------------
    # STEP 3: Patient checks in
    # ------------------------------------------------------------------------
    chk_res = await async_client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CHECKED_IN"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert chk_res.status_code == 200
    assert chk_res.json()["data"]["status"] == "CHECKED_IN"

    # ------------------------------------------------------------------------
    # STEP 4: Clinician starts consultation
    # ------------------------------------------------------------------------
    consult_res = await async_client.post(
        "/api/v1/consultations",
        json={
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "chief_complaint": "Productive cough x 5 days, dyspnea on exertion",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert consult_res.status_code == 201
    consultation_id = consult_res.json()["data"]["id"]

    # ------------------------------------------------------------------------
    # STEP 5: Vitals recorded
    # ------------------------------------------------------------------------
    vitals_res = await async_client.post(
        f"/api/v1/consultations/{consultation_id}/vitals",
        json={
            "systolic_bp": 128,
            "diastolic_bp": 82,
            "pulse_rate": 88,
            "respiratory_rate": 20,
            "temperature_celsius": 38.6,
            "spo2_percent": 96,
            "triage_level": "URGENT",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert vitals_res.status_code == 201

    # ------------------------------------------------------------------------
    # STEP 6: Diagnosis recorded
    # ------------------------------------------------------------------------
    # Finalize consultation with primary diagnosis
    final_res = await async_client.post(
        f"/api/v1/consultations/{consultation_id}/finalize",
        json={
            "clinical_notes": "Bilateral coarse crackles at lung bases. Consistent with community acquired pneumonia.",
            "diagnoses": [
                {
                    "icd10_code": "J18.9",
                    "condition_name": "Pneumonia, unspecified organism",
                    "diagnosis_type": "PRIMARY",
                    "notes": "Community acquired pneumonia (ICD-10 J18.9)",
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert final_res.status_code == 200

    # ------------------------------------------------------------------------
    # STEP 7: Prescription issued with Medication
    # ------------------------------------------------------------------------
    rx_res = await async_client.post(
        "/api/v1/prescriptions",
        json={
            "consultation_id": consultation_id,
            "items": [
                {
                    "medication_id": str(med.id),
                    "medication_name": "Amoxicillin + Clavulanate 625mg",
                    "dosage": "625mg",
                    "frequency": "Every 8 hours",
                    "duration_days": 8,
                    "quantity_prescribed": 25,
                    "instructions": "Take after meals with plenty of water",
                }
            ],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rx_res.status_code == 201
    prescription = rx_res.json()["data"]
    prescription_id = prescription["id"]
    rx_item_id = prescription["items"][0]["id"]
    assert prescription["status"] == "ISSUED"

    # ------------------------------------------------------------------------
    # STEPS 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18:
    # Pharmacist opens prescription, FEFO selects earliest-expiring stock,
    # medicine dispensed, allocations recorded, stock ledger movement created,
    # inventory updated, prescription completed, audit log written!
    # ------------------------------------------------------------------------
    dispense_res = await async_client.post(
        f"/api/v1/prescriptions/{prescription_id}/dispense-fefo",
        json={
            "items": [{"prescription_item_id": rx_item_id, "quantity": 25}],
            "notes": "Verified patient allergies, dispensed 25 tablets",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dispense_res.status_code == 200, dispense_res.text
    disp_records = dispense_res.json()["data"]
    assert len(disp_records) == 1
    record = disp_records[0]
    assert record["quantity_dispensed"] == 25

    # Check FEFO allocations:
    # 20 units from earlier batch (depleted)
    # 5 units from later batch (25 units remaining)
    alloc_early = next(a for a in record["allocations"] if a["batch_id"] == b_early_id)
    alloc_late = next(a for a in record["allocations"] if a["batch_id"] == b_late_id)
    assert alloc_early["allocated_quantity"] == 20
    assert alloc_late["allocated_quantity"] == 5

    # Verify inventory item stock decreased from 50 to 25
    inv_check = await async_client.get(
        f"/api/v1/inventory?facility_id={phc_facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aug_item = next(i for i in inv_check.json()["data"] if i["medication_id"] == str(med.id))
    assert aug_item["quantity_on_hand"] == 25
    # Since 25 <= reorder_level (50), status must be LOW_STOCK or SHORTAGE_RISK
    assert aug_item["stock_status"] in ["LOW_STOCK", "SHORTAGE_RISK"]

    # ------------------------------------------------------------------------
    # STEPS 19, 20: Supply Chain Shortage Monitoring & AI Signal
    # ------------------------------------------------------------------------
    # AI Assistant detects low stock signal
    ai_res = await async_client.post(
        "/api/v1/ai/assistant/query",
        json={"query": "Which medicines are running low in this facility?", "facility_id": str(phc_facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ai_res.status_code == 200
    ai_answer = ai_res.json()["data"]
    assert ai_answer["intent"] == "SHORTAGE_RISK"
    assert "Amoxicillin + Clavulanate" in ai_answer["answer"]

    # Transfer recommendation identifies surplus at District Depot
    rec_res = await async_client.get(
        f"/api/v1/analytics/transfer-recommendations?facility_id={phc_facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rec_res.status_code == 200
    recs = rec_res.json()["data"]
    assert len(recs) >= 1
    transfer_rec = next(r for r in recs if r["medication_id"] == str(med.id))
    assert transfer_rec["surplus_facility_id"] == str(warehouse.id)

    # ------------------------------------------------------------------------
    # STEPS 21, 22, 23, 24, 25: Inter-facility Transfer Pipeline
    # ------------------------------------------------------------------------
    # 21. Request transfer from Depot to PHC
    trf_req_res = await async_client.post(
        "/api/v1/transfers",
        json={
            "source_facility_id": str(warehouse.id),
            "destination_facility_id": str(phc_facility.id),
            "medication_id": str(med.id),
            "requested_quantity": 100,
            "notes": "Monthly replenishment transfer",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert trf_req_res.status_code == 201
    transfer_id = trf_req_res.json()["data"]["id"]

    # 22. Approve transfer
    trf_app_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/approve",
        json={"notes": "Approved by District Pharmacy Officer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert trf_app_res.status_code == 200
    assert trf_app_res.json()["data"]["status"] == "APPROVED"

    # 23. Dispatch transfer from Warehouse (Stock deducted -> IN_TRANSIT)
    trf_disp_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/dispatch",
        json={"dispatched_quantity": 100, "notes": "Dispatched in logistics batch TRF-LOG-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert trf_disp_res.status_code == 200
    assert trf_disp_res.json()["data"]["status"] == "IN_TRANSIT"

    # 24 & 25. Destination PHC receives transfer (Stock added -> RECEIVED)
    trf_rec_res = await async_client.patch(
        f"/api/v1/transfers/{transfer_id}/receive",
        json={"received_quantity": 100, "notes": "Received 100 units in good order"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert trf_rec_res.status_code == 200
    assert trf_rec_res.json()["data"]["status"] == "RECEIVED"

    # Destination stock was 25, now becomes 25 + 100 = 125
    phc_after = await async_client.get(
        f"/api/v1/inventory?facility_id={phc_facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aug_after = next(i for i in phc_after.json()["data"] if i["medication_id"] == str(med.id))
    assert aug_after["quantity_on_hand"] == 125
    assert aug_after["stock_status"] == "NORMAL"

    # ------------------------------------------------------------------------
    # STEP 26: Complete Immutable Audit Trail Verified
    # ------------------------------------------------------------------------
    audit_res = await async_client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_res.status_code == 200
    events = [e["action"] for e in audit_res.json()["data"]]
    # Verify core actions logged
    assert "PATIENT_REGISTERED" in events
    assert "CONSULTATION_FINALIZED" in events
    assert "PRESCRIPTION_DISPENSED_FEFO" in events
    assert "STOCK_TRANSFER_REQUESTED" in events
    assert "STOCK_TRANSFER_DISPATCHED" in events
    assert "STOCK_TRANSFER_RECEIVED" in events
