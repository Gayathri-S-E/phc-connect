import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, PermissionDeniedException, ResourceNotFoundException
from app.models.identity import ScopeLevel, User
from app.models.pharmacy import BatchStatus, StockMovementType, StockTransferStatus
from app.repositories.facility_repository import FacilityRepository
from app.repositories.healthcare_repository import HealthcareRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.schemas.pharmacy import (
    AIAssistantQueryResponse,
    AnomalyItem,
    DemandForecastResponse,
    TransferRecommendationItem,
)


class IntelligenceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pharm_repo = PharmacyRepository(session)
        self.health_repo = HealthcareRepository(session)
        self.facility_repo = FacilityRepository(session)

    # ========================================================================
    # DEMAND FORECASTING & STOCKOUT RISK
    # ========================================================================

    async def get_demand_forecast(
        self,
        facility_id: uuid.UUID,
        medication_id: Optional[uuid.UUID] = None,
    ) -> List[DemandForecastResponse]:
        facility = await self.facility_repo.get_facility_by_id(facility_id)
        if not facility:
            raise ResourceNotFoundException("Facility", str(facility_id))

        if medication_id:
            item = await self.pharm_repo.get_inventory_item(facility_id, medication_id)
            items = [item] if item else []
        else:
            items_seq, _ = await self.pharm_repo.list_inventory_items(
                facility_id=facility_id,
                limit=100,
            )
            items = list(items_seq)

        forecasts: List[DemandForecastResponse] = []
        today = date.today()

        for item in items:
            med_name = item.medication.name if item.medication else "Unknown Medication"
            total_dispensed, event_count = await self.pharm_repo.get_dispensing_consumption(
                facility_id=facility_id,
                medication_id=item.medication_id,
                days=30,
            )

            avg_daily = round(total_dispensed / 30.0, 2)
            forecast_30d = int(round(avg_daily * 30))

            if avg_daily > 0:
                days_left = round(item.available_quantity / avg_daily, 1)
                days_to_add = min(int(days_left), 365)
                pred_stockout = today + timedelta(days=days_to_add)
            else:
                days_left = 999.0
                pred_stockout = None

            # Determine risk tier
            if item.available_quantity == 0:
                risk_level = "CRITICAL"
                explanation = f"Stockout active: 0 units available for {med_name}. Immediate replenishment required."
            elif days_left <= 7:
                risk_level = "CRITICAL"
                explanation = (
                    f"Critical shortage risk: {item.available_quantity} units available with consumption "
                    f"of {avg_daily} units/day yields only {days_left} days of supply. Projected stockout on {pred_stockout}."
                )
            elif days_left <= 15 or item.available_quantity <= item.minimum_stock_level:
                risk_level = "HIGH"
                explanation = (
                    f"High shortage risk: {days_left} days of supply remaining ({item.available_quantity} units) "
                    f"below minimum safety threshold ({item.minimum_stock_level}). Stockout projected around {pred_stockout}."
                )
            elif days_left <= 30 or item.available_quantity <= item.reorder_level:
                risk_level = "MEDIUM"
                explanation = (
                    f"Moderate supply level: {days_left} days remaining. Stock is near or at reorder point "
                    f"({item.reorder_level} units). Normal replenishment recommended."
                )
            else:
                risk_level = "LOW"
                explanation = (
                    f"Adequate stock: {item.available_quantity} units available ({days_left} days of supply). "
                    f"Consumption rate is stable at {avg_daily} units/day."
                )

            # Explainable confidence calculation based on transaction density
            if event_count >= 10:
                confidence = 0.90
            elif event_count >= 3:
                confidence = 0.75
            elif event_count >= 1:
                confidence = 0.60
            else:
                confidence = 0.40

            forecasts.append(
                DemandForecastResponse(
                    facility_id=facility_id,
                    medication_id=item.medication_id,
                    medication_name=med_name,
                    current_stock=item.available_quantity,
                    avg_daily_consumption=avg_daily,
                    days_of_supply_remaining=days_left,
                    forecast_30d_demand=forecast_30d,
                    predicted_stockout_date=pred_stockout,
                    risk_level=risk_level,
                    confidence=confidence,
                    explainability=explanation,
                )
            )

        return forecasts

    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================

    async def detect_anomalies(
        self,
        facility_id: Optional[uuid.UUID] = None,
    ) -> List[AnomalyItem]:
        movements = await self.pharm_repo.get_recent_movements_for_analysis(
            facility_id=facility_id,
            days=14,
        )

        anomalies: List[AnomalyItem] = []

        for m in movements:
            med_name = (
                m.inventory_item.medication.name
                if (m.inventory_item and m.inventory_item.medication)
                else "Medication"
            )
            # Anomaly Pattern 1: Spike in single dispensing event (> 50 units)
            if m.movement_type == StockMovementType.DISPENSE and abs(m.quantity) >= 50:
                anomalies.append(
                    AnomalyItem(
                        facility_id=m.facility_id,
                        medication_id=m.inventory_item.medication_id if m.inventory_item else uuid.uuid4(),
                        medication_name=med_name,
                        anomaly_type="CONSUMPTION_SPIKE",
                        severity="MEDIUM",
                        description=(
                            f"Unusual high-volume dispensing event: {abs(m.quantity)} units of {med_name} "
                            f"dispensed in a single transaction (Ref: {m.reference_id or 'N/A'})."
                        ),
                        confidence=0.85,
                        timestamp=m.created_at,
                    )
                )

            # Anomaly Pattern 2: High loss/damage/expiry adjustments (> 15 units)
            if m.movement_type in [StockMovementType.DAMAGE, StockMovementType.EXPIRY] and abs(m.quantity) >= 15:
                anomalies.append(
                    AnomalyItem(
                        facility_id=m.facility_id,
                        medication_id=m.inventory_item.medication_id if m.inventory_item else uuid.uuid4(),
                        medication_name=med_name,
                        anomaly_type="UNUSUAL_STOCK_LOSS",
                        severity="HIGH",
                        description=(
                            f"Significant stock loss recorded via {m.movement_type.value}: {abs(m.quantity)} units "
                            f"of {med_name} removed. Reason: '{m.notes or 'None'}'."
                        ),
                        confidence=0.92,
                        timestamp=m.created_at,
                    )
                )

        return anomalies

    # ========================================================================
    # INTER-FACILITY TRANSFER RECOMMENDATIONS
    # ========================================================================

    async def get_transfer_recommendations(
        self,
        facility_id: Optional[uuid.UUID] = None,
    ) -> List[TransferRecommendationItem]:
        recommendations: List[TransferRecommendationItem] = []

        # Find items at shortage risk
        shortage_items, _ = await self.pharm_repo.list_inventory_items(
            facility_id=facility_id,
            low_stock_only=True,
            limit=50,
        )

        for shortage_item in shortage_items:
            med_id = shortage_item.medication_id
            med_name = shortage_item.medication.name if shortage_item.medication else "Medication"

            # Look for surplus facilities with the same medication
            peer_items = await self.pharm_repo.list_items_for_medication(med_id)

            for peer in peer_items:
                if peer.facility_id == shortage_item.facility_id:
                    continue

                # Surplus definition: has at least 1.5x reorder level and > 50 units
                surplus = peer.available_quantity - peer.reorder_level
                if surplus >= 30 and peer.available_quantity > peer.reorder_level:
                    recommended_qty = min(surplus // 2, max(20, shortage_item.reorder_level - shortage_item.available_quantity))
                    if recommended_qty > 0:
                        recommendations.append(
                            TransferRecommendationItem(
                                medication_id=med_id,
                                medication_name=med_name,
                                shortage_facility_id=shortage_item.facility_id,
                                shortage_facility_name=shortage_item.facility.name if shortage_item.facility else "Shortage Facility",
                                surplus_facility_id=peer.facility_id,
                                surplus_facility_name=peer.facility.name if peer.facility else "Surplus Facility",
                                recommended_quantity=recommended_qty,
                                rationale=(
                                    f"Destination facility is at shortage risk ({shortage_item.available_quantity} units on hand, "
                                    f"reorder point {shortage_item.reorder_level}). Source facility has healthy surplus of {peer.available_quantity} "
                                    f"units (surplus buffer: {surplus} units). Recommended transfer of {recommended_qty} units balances resilience."
                                ),
                                confidence=0.88,
                            )
                        )
                        break  # Found best match for this shortage item

        return recommendations

    # ========================================================================
    # UNIFIED AI ASSISTANT (SCOPE-AWARE, TRANSACTION-BACKED)
    # ========================================================================

    async def query_ai_assistant(
        self,
        query: str,
        current_user: User,
        user_scope: ScopeLevel,
        facility_id: Optional[uuid.UUID] = None,
    ) -> AIAssistantQueryResponse:
        # Enforce scope boundaries
        target_facility_id = facility_id
        if user_scope in [ScopeLevel.FACILITY, ScopeLevel.SELF]:
            if not current_user.facility_id:
                raise PermissionDeniedException("User has facility scope but is not assigned to a facility")
            if target_facility_id and target_facility_id != current_user.facility_id:
                raise PermissionDeniedException("Cannot query inventory intelligence outside your assigned facility")
            target_facility_id = current_user.facility_id

        q_lower = query.lower()

        # Intent 1: Expiring Batches
        if any(w in q_lower for w in ["expir", "batch", "shelf life"]):
            batches = await self.pharm_repo.list_batches(
                facility_id=target_facility_id,
                expiring_within_days=60,
            )
            evidence = {
                "expiring_batches_count": len(batches),
                "batches": [
                    {
                        "batch_number": b.batch_number,
                        "medication": b.inventory_item.medication.name if b.inventory_item and b.inventory_item.medication else "Unknown",
                        "current_quantity": b.current_quantity,
                        "expiry_date": str(b.expiry_date),
                    }
                    for b in batches[:10]
                ],
            }
            if batches:
                answer = (
                    f"Found {len(batches)} batch(es) expiring within the next 60 days. "
                    f"Earliest expiring: Batch '{batches[0].batch_number}' with {batches[0].current_quantity} units "
                    f"expiring on {batches[0].expiry_date}. Prioritize FEFO dispensing or initiate inter-facility rebalancing."
                )
            else:
                answer = "No active batches are expiring within the next 60 days in the selected facility scope."

            return AIAssistantQueryResponse(
                query=query,
                answer=answer,
                intent="EXPIRING_BATCHES",
                evidence=evidence,
                confidence=0.95,
                data_freshness=datetime.now(timezone.utc),
            )

        # Intent 2: Shortages / Low Stock / Risk
        elif any(w in q_lower for w in ["low", "shortage", "stockout", "risk", "deplet", "run out"]):
            if target_facility_id:
                forecasts = await self.get_demand_forecast(facility_id=target_facility_id)
                at_risk = [f for f in forecasts if f.risk_level in ["CRITICAL", "HIGH", "MEDIUM"]]
                evidence = {
                    "at_risk_count": len(at_risk),
                    "items": [f.model_dump(mode="json") for f in at_risk[:5]],
                }
                if at_risk:
                    concern_names = ", ".join([f.medication_name for f in at_risk[:3]])
                    answer = (
                        f"Facility has {len(at_risk)} medication(s) currently at low stock or shortage risk ({concern_names}). "
                        f"Top concern: {at_risk[0].medication_name} with {at_risk[0].days_of_supply_remaining} days of supply remaining "
                        f"(current stock: {at_risk[0].current_stock} units). "
                        f"Recommended action: Review transfer recommendations or initiate replenishment."
                    )
                else:
                    answer = "All monitored medications in this facility currently have healthy inventory levels above safety thresholds."
            else:
                incidents = await self.pharm_repo.list_shortage_incidents()
                evidence = {"open_incidents_count": len(incidents)}
                answer = f"Across system scope, there are {len(incidents)} open shortage incidents recorded."

            return AIAssistantQueryResponse(
                query=query,
                answer=answer,
                intent="SHORTAGE_RISK",
                evidence=evidence,
                confidence=0.92,
                data_freshness=datetime.now(timezone.utc),
            )

        # Intent 3: Stock Transfers
        elif any(w in q_lower for w in ["transfer", "transit", "shipment", "dispatch"]):
            transfers = await self.pharm_repo.list_transfers(facility_id=target_facility_id)
            in_transit = [t for t in transfers if t.status == StockTransferStatus.IN_TRANSIT]
            evidence = {
                "total_transfers": len(transfers),
                "in_transit_count": len(in_transit),
                "transfers": [
                    {
                        "transfer_number": t.transfer_number,
                        "medication": t.medication.name if t.medication else "Medication",
                        "status": t.status.value,
                        "quantity": t.dispatched_quantity or t.requested_quantity,
                    }
                    for t in transfers[:5]
                ],
            }
            answer = (
                f"There are currently {len(in_transit)} transfer(s) in transit and {len(transfers)} total transfers on record "
                f"for this facility scope."
            )
            return AIAssistantQueryResponse(
                query=query,
                answer=answer,
                intent="STOCK_TRANSFERS",
                evidence=evidence,
                confidence=0.95,
                data_freshness=datetime.now(timezone.utc),
            )

        # Intent 4: Anomalies / Spikes
        elif any(w in q_lower for w in ["anomal", "spike", "unusual", "loss", "damage"]):
            anomalies = await self.detect_anomalies(facility_id=target_facility_id)
            evidence = {
                "anomalies_count": len(anomalies),
                "anomalies": [a.model_dump(mode="json") for a in anomalies[:5]],
            }
            if anomalies:
                answer = (
                    f"Detected {len(anomalies)} unusual inventory pattern(s) in the past 14 days. "
                    f"Latest: {anomalies[0].description}"
                )
            else:
                answer = "No anomalous consumption spikes or unexpected stock adjustments detected in recent records."

            return AIAssistantQueryResponse(
                query=query,
                answer=answer,
                intent="ANOMALY_DETECTION",
                evidence=evidence,
                confidence=0.88,
                data_freshness=datetime.now(timezone.utc),
            )

        # Intent 5: General Status / Operational Summary (Fallback)
        else:
            if target_facility_id:
                items_seq, total_items = await self.pharm_repo.list_inventory_items(facility_id=target_facility_id)
                evidence = {"facility_id": str(target_facility_id), "total_catalog_items": total_items}
                answer = (
                    f"Operational summary for facility {target_facility_id}: "
                    f"{total_items} medication inventory lines active. Ask about 'shortages', 'expiring batches', "
                    f"'transfers', or 'anomalies' for detailed analysis."
                )
            else:
                answer = (
                    "Smart Health & Supply Chain Resilience Assistant online. "
                    "You may query shortage risks, expiring batches, inter-facility transfers, or consumption anomalies."
                )
                evidence = {"scope": user_scope.value if hasattr(user_scope, "value") else str(user_scope)}

            return AIAssistantQueryResponse(
                query=query,
                answer=answer,
                intent="OPERATIONAL_SUMMARY",
                evidence=evidence,
                confidence=0.85,
                data_freshness=datetime.now(timezone.utc),
            )
