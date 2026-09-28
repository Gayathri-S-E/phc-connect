import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication
from app.models.pharmacy import BatchStatus, InventoryBatch, InventoryItem, StockMovement, StockMovementType


@pytest.mark.asyncio
async def test_demand_forecasting_and_stockout_risk_calculation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # 1. Create Medication
    med = Medication(
        id=uuid.uuid4(),
        name="Ciprofloxacin 500mg",
        code="MED-CIPRO-500",
        dosage_form="Tablet",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.flush()

    # Create Inventory Item with 60 units on hand
    inv_item = InventoryItem(
        id=uuid.uuid4(),
        facility_id=facility.id,
        medication_id=med.id,
        quantity_on_hand=60,
        quantity_reserved=0,
        reorder_level=50,
        minimum_stock_level=20,
    )
    db_session.add(inv_item)
    await db_session.flush()

    # Record 3 dispensing movements in the past 10 days totaling 90 units (approx 3 units/day)
    for i in range(3):
        mov = StockMovement(
            id=uuid.uuid4(),
            facility_id=facility.id,
            inventory_item_id=inv_item.id,
            movement_type=StockMovementType.DISPENSE,
            quantity=-30,
            balance_after=60,
            actor_id=seeded_data["admin_user"].id,
            created_at=datetime.now(timezone.utc) - timedelta(days=i * 2 + 1),
        )
        db_session.add(mov)
    await db_session.commit()

    # 2. Query Demand Forecast
    fc_res = await async_client.get(
        f"/api/v1/analytics/demand-forecast?facility_id={facility.id}&medication_id={med.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert fc_res.status_code == 200, fc_res.text
    forecasts = fc_res.json()["data"]
    assert len(forecasts) == 1
    fc = forecasts[0]

    assert fc["medication_name"] == "Ciprofloxacin 500mg"
    assert fc["current_stock"] == 60
    assert fc["avg_daily_consumption"] == 3.0  # 90 units / 30 days
    assert fc["days_of_supply_remaining"] == 20.0  # 60 units / 3.0 units/day
    assert fc["forecast_30d_demand"] == 90
    assert fc["risk_level"] in ["HIGH", "MEDIUM"]
    assert "explainability" in fc
    assert fc["confidence"] > 0.6


@pytest.mark.asyncio
async def test_anomaly_detection_flags_unusual_loss(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    facility = seeded_data["facility"]

    # 1. Create Medication & inventory item
    med = Medication(
        id=uuid.uuid4(),
        name="Artesunate Injection 60mg",
        code="MED-ART-60",
        dosage_form="Vial",
        strength="60mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.flush()

    inv_item = InventoryItem(
        id=uuid.uuid4(),
        facility_id=facility.id,
        medication_id=med.id,
        quantity_on_hand=80,
        reorder_level=40,
        minimum_stock_level=10,
    )
    db_session.add(inv_item)
    await db_session.flush()

    # Record large damage loss (-20 units)
    mov = StockMovement(
        id=uuid.uuid4(),
        facility_id=facility.id,
        inventory_item_id=inv_item.id,
        movement_type=StockMovementType.DAMAGE,
        quantity=-20,
        balance_after=80,
        notes="Freezer compressor failure caused denaturation",
        actor_id=seeded_data["admin_user"].id,
        created_at=datetime.now(timezone.utc) - timedelta(hours=3),
    )
    db_session.add(mov)
    await db_session.commit()

    # 2. Query Anomaly Detection API
    anom_res = await async_client.get(
        f"/api/v1/analytics/anomalies?facility_id={facility.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert anom_res.status_code == 200
    anomalies = anom_res.json()["data"]
    assert len(anomalies) >= 1
    anom = next(a for a in anomalies if a["anomaly_type"] == "UNUSUAL_STOCK_LOSS")
    assert anom["severity"] == "HIGH"
    assert "denaturation" in anom["description"]
    assert anom["confidence"] >= 0.90


@pytest.mark.asyncio
async def test_inter_facility_transfer_recommendations(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    org = seeded_data["org"]
    shortage_fac = seeded_data["facility"]

    # 1. Create Surplus Facility
    surplus_fac = Facility(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test District Warehouse Trichy",
        code="TEST-WH-001",
        facility_type=FacilityType.DISTRICT_WAREHOUSE,
        state="Tamil Nadu",
        district="Chengalpattu",
        is_active=True,
    )
    db_session.add(surplus_fac)

    # 2. Create Medication
    med = Medication(
        id=uuid.uuid4(),
        name="Azithromycin 500mg",
        code="MED-AZI-500",
        dosage_form="Tablet",
        strength="500mg",
        is_active=True,
    )
    db_session.add(med)
    await db_session.flush()

    # Shortage facility has only 5 units (reorder level 50) -> LOW STOCK / SHORTAGE
    shortage_item = InventoryItem(
        id=uuid.uuid4(),
        facility_id=shortage_fac.id,
        medication_id=med.id,
        quantity_on_hand=5,
        reorder_level=50,
        minimum_stock_level=20,
    )
    # Surplus facility has 300 units (reorder level 50) -> SURPLUS
    surplus_item = InventoryItem(
        id=uuid.uuid4(),
        facility_id=surplus_fac.id,
        medication_id=med.id,
        quantity_on_hand=300,
        reorder_level=50,
        minimum_stock_level=20,
    )
    db_session.add_all([shortage_item, surplus_item])
    await db_session.commit()

    # 3. Query Transfer Recommendations
    rec_res = await async_client.get(
        f"/api/v1/analytics/transfer-recommendations?facility_id={shortage_fac.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rec_res.status_code == 200
    recs = rec_res.json()["data"]
    assert len(recs) >= 1
    azi_rec = next(r for r in recs if r["medication_id"] == str(med.id))
    assert azi_rec["shortage_facility_id"] == str(shortage_fac.id)
    assert azi_rec["surplus_facility_id"] == str(surplus_fac.id)
    assert azi_rec["recommended_quantity"] > 0
    assert "surplus" in azi_rec["rationale"].lower()


@pytest.mark.asyncio
async def test_unified_ai_assistant_scope_aware_query(
    async_client: AsyncClient,
    db_session: AsyncSession,
    seeded_data: dict,
):
    admin_token = seeded_data["admin_token"]
    doctor_token = seeded_data["doctor_token"]
    facility = seeded_data["facility"]

    # 1. Query AI Assistant about shortages
    res1 = await async_client.post(
        "/api/v1/ai/assistant/query",
        json={"query": "Which medicines are running low or at risk of stockout?", "facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res1.status_code == 200, res1.text
    ans1 = res1.json()["data"]
    assert ans1["intent"] == "SHORTAGE_RISK"
    assert "evidence" in ans1
    assert ans1["confidence"] > 0.8
    assert "disclaimer" in ans1

    # 2. Query AI Assistant about expiring batches
    res2 = await async_client.post(
        "/api/v1/ai/assistant/query",
        json={"query": "Show me any batches expiring soon in this facility", "facility_id": str(facility.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
    ans2 = res2.json()["data"]
    assert ans2["intent"] == "EXPIRING_BATCHES"

    # 3. Test Scope Security: Doctor with FACILITY scope cannot query another facility's assistant
    fake_other_fac_id = uuid.uuid4()
    denied_res = await async_client.post(
        "/api/v1/ai/assistant/query",
        json={"query": "What are the stockouts here?", "facility_id": str(fake_other_fac_id)},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert denied_res.status_code == 403
