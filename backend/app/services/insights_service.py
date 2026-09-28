import math
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.models.facility import Facility
from app.models.healthcare import (
    Appointment,
    Consultation,
    LabOrder,
    LabOrderStatus,
    Prescription,
    PrescriptionStatus,
)
from app.models.intelligence import Alert, AlertType, ForecastRecord
from app.models.pharmacy import (
    BatchStatus,
    InventoryBatch,
    InventoryItem,
    ShortageIncident,
    ShortageStatus,
    StockTransfer,
)
from app.models.supply_chain import PurchaseOrder, Shipment
from app.repositories.supply_chain_repository import SupplyChainRepository
from app.schemas.intelligence import (
    FacilityStockSummary,
    ForecastItem,
    ForecastResponse,
    PHCDashboardResponse,
    RiskAnalysisResponse,
    RiskFactor,
    SupplyChainDashboardResponse,
)
from app.services.intelligence_service import IntelligenceService

DISCLAIMER = (
    "Rule-based statistical estimate from the stock ledger (no ML model). "
    "Use as decision support; verify against physical stock before acting."
)
OPEN_SHORTAGE_STATES = [
    ShortageStatus.REPORTED,
    ShortageStatus.INVESTIGATING,
    ShortageStatus.ESCALATED_DISTRICT,
    ShortageStatus.ESCALATED_STATE,
    ShortageStatus.ACTION_TAKEN,
]
PENDING_RX_STATES = [PrescriptionStatus.ISSUED, PrescriptionStatus.PARTIALLY_DISPENSED]
PENDING_LAB_STATES = [LabOrderStatus.ORDERED, LabOrderStatus.SAMPLE_COLLECTED, LabOrderStatus.IN_ANALYSIS]


def _risk_level(score: float) -> str:
    if score >= 60:
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    return "LOW"


class InsightsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.intel = IntelligenceService(session)
        self.repo = SupplyChainRepository(session)

    async def _facility(self, facility_id: uuid.UUID) -> Facility:
        facility = await self.session.get(Facility, facility_id)
        if not facility:
            raise ResourceNotFoundException("Facility", str(facility_id))
        return facility

    async def _count(self, stmt) -> int:
        return (await self.session.execute(stmt)).scalar_one() or 0

    async def _group_count(self, column, *where) -> Dict[str, int]:
        rows = (await self.session.execute(select(column, func.count()).where(*where).group_by(column))).all()
        return {(k.value if hasattr(k, "value") else str(k)): n for k, n in rows}

    # ------------------------------------------------------------------ forecast
    async def forecast(
        self, facility_id: uuid.UUID, medication_id: Optional[uuid.UUID], horizon_days: int
    ) -> ForecastResponse:
        base = await self.intel.get_demand_forecast(facility_id=facility_id, medication_id=medication_id)
        today = date.today()
        items: List[ForecastItem] = []
        for f in base:
            predicted = round(f.avg_daily_consumption * horizon_days, 2)
            margin = round(predicted * (1 - f.confidence), 2)
            lower, upper = max(0.0, round(predicted - margin, 2)), round(predicted + margin, 2)
            shortfall = max(0, math.ceil(predicted) - f.current_stock)
            items.append(ForecastItem(
                medication_id=f.medication_id,
                medication_name=f.medication_name,
                current_stock=f.current_stock,
                avg_daily_consumption=f.avg_daily_consumption,
                horizon_days=horizon_days,
                predicted_consumption=predicted,
                confidence_interval_lower=lower,
                confidence_interval_upper=upper,
                projected_shortfall=shortfall,
                predicted_stockout_date=f.predicted_stockout_date,
                risk_level=f.risk_level,
                confidence=f.confidence,
                explainability=(
                    f"{f.avg_daily_consumption} units/day (30-day dispensing average) x {horizon_days} days = "
                    f"{predicted} units; band ±{margin} reflects {int(f.confidence * 100)}% confidence from "
                    f"transaction density. Shortfall vs current stock: {shortfall} units."
                ),
            ))
            await self.repo.add_forecast_record(ForecastRecord(
                facility_id=facility_id,
                medication_id=f.medication_id,
                forecast_date=today,
                forecast_horizon_days=horizon_days,
                predicted_consumption=predicted,
                confidence_interval_lower=lower,
                confidence_interval_upper=upper,
            ))
        return ForecastResponse(
            facility_id=facility_id, forecast_date=today, horizon_days=horizon_days, items=items,
            disclaimer=DISCLAIMER,
        )

    # ------------------------------------------------------------------ risk analysis
    async def risk_analysis(self, facility_id: uuid.UUID) -> RiskAnalysisResponse:
        facility = await self._facility(facility_id)
        forecasts = await self.intel.get_demand_forecast(facility_id=facility_id)
        tracked = len(forecasts)
        stockouts = sum(1 for f in forecasts if f.current_stock == 0)
        high_risk = sum(1 for f in forecasts if f.risk_level in ("CRITICAL", "HIGH"))

        open_shortages = await self._count(
            select(func.count(ShortageIncident.id)).where(
                ShortageIncident.facility_id == facility_id, ShortageIncident.status.in_(OPEN_SHORTAGE_STATES)
            )
        )
        batch_scope = (
            select(func.count(InventoryBatch.id))
            .join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
            .where(InventoryItem.facility_id == facility_id, InventoryBatch.status == BatchStatus.AVAILABLE,
                   InventoryBatch.current_quantity > 0)
        )
        active_batches = await self._count(batch_scope)
        expiring = await self._count(
            batch_scope.where(InventoryBatch.expiry_date <= date.today() + timedelta(days=30))
        )
        anomalies = len(await self.intel.detect_anomalies(facility_id=facility_id))
        cold_chain = await self._count(
            select(func.count(Alert.id)).where(
                Alert.facility_id == facility_id,
                Alert.alert_type == AlertType.COLD_CHAIN_BREACH,
                Alert.is_acknowledged.is_(False),
            )
        )

        def ratio(n: int, d: int) -> float:
            return round(n / d, 3) if d else 0.0

        raw = [
            ("stockout_ratio", ratio(stockouts, tracked), 30,
             f"{stockouts} of {tracked} tracked medicines have zero available stock."),
            ("high_risk_forecast_ratio", ratio(high_risk, tracked), 25,
             f"{high_risk} of {tracked} medicines forecast at HIGH/CRITICAL stockout risk."),
            ("open_shortage_incidents", min(open_shortages / 5, 1.0), 20,
             f"{open_shortages} open shortage incident(s); saturates at 5."),
            ("expiring_batch_ratio", ratio(expiring, active_batches), 10,
             f"{expiring} of {active_batches} active batches expire within 30 days."),
            ("consumption_anomalies", min(anomalies / 5, 1.0), 10,
             f"{anomalies} ledger anomalies in the last 14 days; saturates at 5."),
            ("unacknowledged_cold_chain_breaches", min(cold_chain / 3, 1.0), 5,
             f"{cold_chain} unacknowledged cold-chain breach alert(s); saturates at 3."),
        ]
        factors = [
            RiskFactor(factor=name, value=value, weight=weight, contribution=round(value * weight, 2),
                       explanation=text)
            for name, value, weight, text in raw
        ]
        score = round(sum(f.contribution for f in factors), 1)

        recommendations: List[str] = []
        if stockouts:
            recommendations.append("Raise emergency transfer requests for stocked-out medicines (see transfer recommendations).")
        if high_risk:
            recommendations.append("Submit a purchase request covering HIGH/CRITICAL forecast items.")
        if open_shortages:
            recommendations.append("Review open shortage incidents; escalate any without mitigation to district level.")
        if expiring:
            recommendations.append("Prioritise dispensing or redistributing batches expiring within 30 days (FEFO).")
        if anomalies:
            recommendations.append("Investigate flagged consumption spikes or stock losses.")
        if cold_chain:
            recommendations.append("Acknowledge cold-chain breach alerts and quarantine affected stock.")
        if not recommendations:
            recommendations.append("No immediate action required; continue routine monitoring.")

        return RiskAnalysisResponse(
            facility_id=facility.id,
            facility_name=facility.name,
            risk_score=score,
            risk_level=_risk_level(score),
            factors=factors,
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc),
            disclaimer=DISCLAIMER,
        )

    # ------------------------------------------------------------------ dashboards
    async def phc_dashboard(self, facility_id: uuid.UUID) -> PHCDashboardResponse:
        facility = await self._facility(facility_id)
        start = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        by_status = await self._group_count(
            Appointment.status,
            Appointment.facility_id == facility_id,
            Appointment.appointment_date >= start,
            Appointment.appointment_date < end,
        )
        stock = await self._stock_counts([facility_id])
        return PHCDashboardResponse(
            facility_id=facility.id,
            facility_name=facility.name,
            as_of=datetime.now(timezone.utc),
            appointments_today=sum(by_status.values()),
            appointments_by_status=by_status,
            consultations_today=await self._count(
                select(func.count(Consultation.id)).where(
                    Consultation.facility_id == facility_id,
                    Consultation.started_at >= start,
                    Consultation.started_at < end,
                )
            ),
            pending_prescriptions=await self._count(
                select(func.count(Prescription.id)).where(
                    Prescription.facility_id == facility_id, Prescription.status.in_(PENDING_RX_STATES)
                )
            ),
            pending_lab_orders=await self._count(
                select(func.count(LabOrder.id)).where(
                    LabOrder.facility_id == facility_id, LabOrder.status.in_(PENDING_LAB_STATES)
                )
            ),
            low_stock_items=stock[facility_id]["low"],
            stockout_items=stock[facility_id]["out"],
            batches_expiring_30d=await self._count(
                select(func.count(InventoryBatch.id))
                .join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
                .where(
                    InventoryItem.facility_id == facility_id,
                    InventoryBatch.status == BatchStatus.AVAILABLE,
                    InventoryBatch.current_quantity > 0,
                    InventoryBatch.expiry_date <= date.today() + timedelta(days=30),
                )
            ),
            open_shortages=stock[facility_id]["shortages"],
            unacknowledged_alerts=await self._count(
                select(func.count(Alert.id)).where(Alert.facility_id == facility_id, Alert.is_acknowledged.is_(False))
            ),
        )

    async def _stock_counts(self, facility_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Dict[str, int]]:
        counts = {fid: {"tracked": 0, "low": 0, "out": 0, "shortages": 0} for fid in facility_ids}
        if not facility_ids:
            return counts
        available = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
        rows = (await self.session.execute(
            select(
                InventoryItem.facility_id,
                func.count(InventoryItem.id),
                func.sum(case((available <= InventoryItem.reorder_level, 1), else_=0)),
                func.sum(case((available <= 0, 1), else_=0)),
            )
            .where(InventoryItem.facility_id.in_(facility_ids))
            .group_by(InventoryItem.facility_id)
        )).all()
        for fid, tracked, low, out in rows:
            counts[fid].update(tracked=tracked or 0, low=int(low or 0), out=int(out or 0))
        shortage_rows = (await self.session.execute(
            select(ShortageIncident.facility_id, func.count(ShortageIncident.id))
            .where(ShortageIncident.facility_id.in_(facility_ids), ShortageIncident.status.in_(OPEN_SHORTAGE_STATES))
            .group_by(ShortageIncident.facility_id)
        )).all()
        for fid, n in shortage_rows:
            counts[fid]["shortages"] = n
        return counts

    async def supply_chain_dashboard(
        self, facility_ids: Optional[List[uuid.UUID]], scope_label: str
    ) -> SupplyChainDashboardResponse:
        fac_stmt = select(Facility).where(Facility.is_active.is_(True))
        if facility_ids is not None:
            fac_stmt = fac_stmt.where(Facility.id.in_(facility_ids))
        facilities = (await self.session.execute(fac_stmt.order_by(Facility.name))).scalars().all()
        ids = [f.id for f in facilities]
        stock = await self._stock_counts(ids)

        return SupplyChainDashboardResponse(
            as_of=datetime.now(timezone.utc),
            scope=scope_label,
            facilities_in_scope=len(facilities),
            total_low_stock_items=sum(c["low"] for c in stock.values()),
            total_stockout_items=sum(c["out"] for c in stock.values()),
            open_shortages_by_severity=await self._group_count(
                ShortageIncident.severity,
                ShortageIncident.status.in_(OPEN_SHORTAGE_STATES),
                ShortageIncident.facility_id.in_(ids),
            ),
            transfers_by_status=await self._group_count(
                StockTransfer.status,
                (StockTransfer.source_facility_id.in_(ids)) | (StockTransfer.destination_facility_id.in_(ids)),
            ),
            purchase_orders_by_status=await self._group_count(
                PurchaseOrder.status, PurchaseOrder.destination_facility_id.in_(ids)
            ),
            shipments_by_status=await self._group_count(
                Shipment.status,
                (Shipment.destination_facility_id.in_(ids)) | (Shipment.origin_facility_id.in_(ids)),
            ),
            unacknowledged_alerts=await self._count(
                select(func.count(Alert.id)).where(
                    Alert.is_acknowledged.is_(False),
                    (Alert.facility_id.in_(ids)) | (Alert.facility_id.is_(None)),
                )
            ),
            facilities=[
                FacilityStockSummary(
                    facility_id=f.id,
                    facility_name=f.name,
                    district=f.district,
                    state=f.state,
                    items_tracked=stock[f.id]["tracked"],
                    low_stock_items=stock[f.id]["low"],
                    stockout_items=stock[f.id]["out"],
                    open_shortages=stock[f.id]["shortages"],
                )
                for f in facilities
            ],
        )
