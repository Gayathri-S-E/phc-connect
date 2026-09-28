"""Supply requests from PHC → District (Role 07) → State warehouse (Role 10), incl. emergency requests (Role 08).

Allocation creates an APPROVED StockTransfer on the shared ledger; dispatch and
receipt then use the existing transfer endpoints, so inventory is only ever
changed by the one FEFO-safe transfer workflow. Receipt verification (in
PharmacyService.receive_transfer) records SupplyReceipts and closes the loop.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.models.emergency import EmergencyIncident
from app.models.facility import Facility, FacilityType
from app.models.healthcare import Medication
from app.models.identity import ScopeLevel
from app.models.intelligence import Alert, AlertSeverity, AlertType
from app.models.pharmacy import (
    BatchStatus,
    InventoryBatch,
    InventoryItem,
    ShortageIncident,
    StockMovement,
    StockMovementType,
    StockTransfer,
    StockTransferStatus,
    TransferUrgency,
)
from app.models.supply_chain import (
    PurchaseRequestUrgency,
    ReceiptVerificationStatus,
    SupplyHealthImpact,
    SupplyReceipt,
    SupplyRequest,
    SupplyRequestEvent,
    SupplyRequestLevel,
    SupplyRequestStatus,
)
from app.schemas.supply_requests import (
    HealthImpactCreate,
    SupplyAllocationCreate,
    SupplyEscalationCreate,
    SupplyRequestClarify,
    SupplyRequestCreate,
    SupplyRequestDecision,
)
from app.services.common import AuditCtx, AuditMixin, make_reference, paginate, utcnow
from app.services.health_aggregation_service import ACTIVE_EMERGENCY_STATES

OPEN_REQUEST_STATES = [
    SupplyRequestStatus.SUBMITTED, SupplyRequestStatus.UNDER_REVIEW, SupplyRequestStatus.CLARIFICATION_REQUESTED,
    SupplyRequestStatus.APPROVED, SupplyRequestStatus.PARTIALLY_APPROVED, SupplyRequestStatus.ALLOCATED,
    SupplyRequestStatus.DISPATCHED,
]
REVIEWABLE = {SupplyRequestStatus.SUBMITTED, SupplyRequestStatus.UNDER_REVIEW}
WAREHOUSE_TYPES = {FacilityType.DISTRICT_WAREHOUSE, FacilityType.CENTRAL_WAREHOUSE}
PRIORITY_ORDER = case(
    (SupplyRequest.priority == PurchaseRequestUrgency.EMERGENCY, 0),
    (SupplyRequest.priority == PurchaseRequestUrgency.URGENT, 1),
    else_=2,
)
DELAY_THRESHOLD_DAYS = 3
EXPIRY_WINDOW_DAYS = 60
MONITOR_METHOD = "RULE_BASED_SUPPLY_MONITOR v1 (stock thresholds, expiry window, transit age)"


class SupplyRequestService(AuditMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------------------------------------------------------------------ helpers
    async def _facility(self, facility_id: uuid.UUID) -> Facility:
        facility = await self.session.get(Facility, facility_id)
        if not facility:
            raise ResourceNotFoundException("Facility", str(facility_id))
        return facility

    def _ensure_facility_in(self, j: Jurisdiction, facility: Facility) -> None:
        if j.is_facility_bound:
            if facility.id != j.facility_id:
                raise PermissionDeniedException("You can only act for your own facility.")
            return
        j.ensure_covers(facility.state, facility.district if j.scope == ScopeLevel.DISTRICT else None)

    async def _event(self, req: SupplyRequest, actor_id: uuid.UUID, old: Optional[SupplyRequestStatus], note: Optional[str]):
        self.session.add(SupplyRequestEvent(request_id=req.id, actor_id=actor_id,
                                            from_status=old.value if old else None,
                                            to_status=req.status.value, note=note))

    def _visible(self, stmt, j: Jurisdiction):
        if j.is_facility_bound:
            return stmt.where(SupplyRequest.requesting_facility_id == j.facility_id)
        return j.filter(stmt, SupplyRequest.state, SupplyRequest.district if j.scope == ScopeLevel.DISTRICT else None)

    # ------------------------------------------------------------------ create
    async def create(self, data: SupplyRequestCreate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> SupplyRequest:
        facility = await self._facility(data.requesting_facility_id)
        self._ensure_facility_in(j, facility)
        if not await self.session.get(Medication, data.medication_id):
            raise ResourceNotFoundException("Medication", str(data.medication_id))
        level = (SupplyRequestLevel.DISTRICT_TO_STATE if facility.facility_type == FacilityType.DISTRICT_WAREHOUSE
                 else SupplyRequestLevel.PHC_TO_DISTRICT)
        priority = data.priority
        if data.emergency_incident_id:
            incident = await self.session.get(EmergencyIncident, data.emergency_incident_id)
            if not incident or incident.status not in ACTIVE_EMERGENCY_STATES:
                raise BadRequestException("Linked emergency does not exist or is no longer active.")
            if incident.district.lower() != facility.district.lower() or incident.state.lower() != facility.state.lower():
                raise BadRequestException("Emergency and requesting facility must be in the same district.")
            priority = PurchaseRequestUrgency.EMERGENCY
        duplicate = (await self.session.execute(select(SupplyRequest.reference).where(
            SupplyRequest.requesting_facility_id == facility.id, SupplyRequest.medication_id == data.medication_id,
            SupplyRequest.level == level, SupplyRequest.status.in_(OPEN_REQUEST_STATES),
            SupplyRequest.emergency_incident_id.is_(None) if not data.emergency_incident_id
            else SupplyRequest.emergency_incident_id == data.emergency_incident_id,
        ))).first()
        if duplicate:
            raise ConflictException(f"An open request ({duplicate[0]}) already exists for this medicine and facility.")
        req = SupplyRequest(
            reference=make_reference("SRQ"), level=level, requesting_facility_id=facility.id,
            state=facility.state, district=facility.district, medication_id=data.medication_id,
            requested_quantity=data.requested_quantity, priority=priority, status=SupplyRequestStatus.SUBMITTED,
            reason=data.reason, required_by=data.required_by, emergency_incident_id=data.emergency_incident_id,
            requested_by=actor_id,
        )
        self.session.add(req)
        await self.session.flush()
        await self._event(req, actor_id, None, "Request submitted.")
        await self._audit("SUPPLY_REQUEST_SUBMITTED", "supply_request", req.id, actor_id, ctx, facility_id=facility.id,
                          new_state={"reference": req.reference, "level": level.value, "priority": priority.value,
                                     "quantity": data.requested_quantity})
        return req

    # ------------------------------------------------------------------ read
    async def list(self, j: Jurisdiction, level: Optional[SupplyRequestLevel], status: Optional[SupplyRequestStatus],
                   priority: Optional[PurchaseRequestUrgency], open_only: bool, emergency_only: bool,
                   facility_id: Optional[uuid.UUID], page: int, page_size: int):
        stmt = self._visible(select(SupplyRequest), j)
        if level:
            stmt = stmt.where(SupplyRequest.level == level)
        if status:
            stmt = stmt.where(SupplyRequest.status == status)
        elif open_only:
            stmt = stmt.where(SupplyRequest.status.in_(OPEN_REQUEST_STATES))
        if priority:
            stmt = stmt.where(SupplyRequest.priority == priority)
        if emergency_only:
            stmt = stmt.where(SupplyRequest.emergency_incident_id.is_not(None))
        if facility_id:
            stmt = stmt.where(SupplyRequest.requesting_facility_id == facility_id)
        total = (await self.session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        rows = await self.session.execute(
            stmt.order_by(PRIORITY_ORDER, SupplyRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return rows.scalars().all(), total

    async def get(self, request_id: uuid.UUID, j: Jurisdiction, for_update: bool = False) -> SupplyRequest:
        stmt = self._visible(select(SupplyRequest).where(SupplyRequest.id == request_id)
                             .options(selectinload(SupplyRequest.events), selectinload(SupplyRequest.medication),
                                      selectinload(SupplyRequest.requesting_facility))
                             .execution_options(populate_existing=True), j)
        if for_update:
            stmt = stmt.with_for_update(of=SupplyRequest)
        req = (await self.session.execute(stmt)).scalar_one_or_none()
        if not req:
            raise ResourceNotFoundException("SupplyRequest", str(request_id))
        return req

    async def _committed(self, facility_id: uuid.UUID, medication_id: uuid.UUID) -> int:
        return (await self.session.execute(
            select(func.coalesce(func.sum(StockTransfer.requested_quantity), 0)).where(
                StockTransfer.source_facility_id == facility_id, StockTransfer.medication_id == medication_id,
                StockTransfer.status == StockTransferStatus.APPROVED,
            )
        )).scalar_one() or 0

    async def _usable(self, facility_id: uuid.UUID, medication_id: uuid.UUID):
        row = (await self.session.execute(
            select(func.coalesce(func.sum(InventoryBatch.current_quantity), 0), func.min(InventoryBatch.expiry_date))
            .join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
            .where(InventoryItem.facility_id == facility_id, InventoryItem.medication_id == medication_id,
                   InventoryBatch.status == BatchStatus.AVAILABLE, InventoryBatch.current_quantity > 0,
                   InventoryBatch.expiry_date >= date.today())
        )).first()
        reserved = (await self.session.execute(
            select(func.coalesce(func.sum(InventoryItem.quantity_reserved), 0))
            .where(InventoryItem.facility_id == facility_id, InventoryItem.medication_id == medication_id)
        )).scalar_one() or 0
        return max(0, int(row[0] or 0) - int(reserved)), row[1]

    async def stock_options(self, req: SupplyRequest, j: Jurisdiction) -> List[dict]:
        stmt = select(Facility).where(Facility.is_active.is_(True), Facility.id != req.requesting_facility_id,
                                      func.lower(Facility.state) == req.state.lower())
        if req.level == SupplyRequestLevel.PHC_TO_DISTRICT:
            stmt = stmt.where(func.lower(Facility.district) == req.district.lower())
        else:
            stmt = stmt.where(Facility.facility_type == FacilityType.CENTRAL_WAREHOUSE)
        options = []
        for f in (await self.session.execute(stmt)).scalars().all():
            usable, nearest = await self._usable(f.id, req.medication_id)
            if usable <= 0:
                continue
            committed = await self._committed(f.id, req.medication_id)
            options.append({
                "facility_id": f.id, "facility_name": f.name, "facility_type": f.facility_type.value,
                "district": f.district, "available_quantity": usable, "committed_quantity": committed,
                "allocatable_quantity": max(0, usable - committed), "nearest_expiry": nearest,
            })
        options.sort(key=lambda o: (o["facility_type"] not in {t.value for t in WAREHOUSE_TYPES}, -o["allocatable_quantity"]))
        return options

    async def detail(self, request_id: uuid.UUID, j: Jurisdiction, include_stock: bool) -> dict:
        req = await self.get(request_id, j)
        own_item = (await self.session.execute(select(InventoryItem).where(
            InventoryItem.facility_id == req.requesting_facility_id, InventoryItem.medication_id == req.medication_id,
        ))).scalar_one_or_none()
        consumption = None
        if own_item:
            since = datetime.now(timezone.utc) - timedelta(days=30)
            consumption = -int((await self.session.execute(
                select(func.coalesce(func.sum(StockMovement.quantity), 0)).where(
                    StockMovement.inventory_item_id == own_item.id,
                    StockMovement.movement_type == StockMovementType.DISPENSE, StockMovement.created_at >= since,
                ))).scalar_one() or 0)
        return {
            **{c.name: getattr(req, c.name) for c in SupplyRequest.__table__.columns},
            "medication_name": req.medication.name if req.medication else None,
            "requesting_facility_name": req.requesting_facility.name if req.requesting_facility else None,
            "requesting_facility_stock": (own_item.quantity_on_hand - own_item.quantity_reserved) if own_item else 0,
            "requesting_facility_30d_consumption": consumption,
            "events": req.events,
            "stock_options": await self.stock_options(req, j) if include_stock else [],
        }

    # ------------------------------------------------------------------ review
    def _ensure_reviewer_level(self, req: SupplyRequest, j: Jurisdiction) -> None:
        if j.is_facility_bound:
            raise PermissionDeniedException("Facility-level users cannot review supply requests.")
        if req.level == SupplyRequestLevel.DISTRICT_TO_STATE and j.scope == ScopeLevel.DISTRICT:
            raise PermissionDeniedException("District-to-state requests are reviewed by the State Supply Chain Manager.")

    async def decide(self, request_id: uuid.UUID, data: SupplyRequestDecision, j: Jurisdiction, actor_id: uuid.UUID,
                     ctx: AuditCtx) -> SupplyRequest:
        req = await self.get(request_id, j, for_update=True)
        self._ensure_reviewer_level(req, j)
        if req.requested_by == actor_id and data.decision != "CLOSE":
            raise BadRequestException("Segregation of duties: you cannot review your own request.")
        old = req.status
        if data.decision == "START_REVIEW":
            if req.status != SupplyRequestStatus.SUBMITTED:
                raise BadRequestException(f"Only SUBMITTED requests can move to review (current: {req.status.value}).")
            req.status = SupplyRequestStatus.UNDER_REVIEW
        elif data.decision == "CLOSE":
            if req.status not in (SupplyRequestStatus.FULFILLED, SupplyRequestStatus.PARTIALLY_FULFILLED,
                                  SupplyRequestStatus.REJECTED):
                raise BadRequestException("Only fulfilled, partially fulfilled or rejected requests can be closed.")
            req.status = SupplyRequestStatus.CLOSED
        else:
            if req.status not in REVIEWABLE:
                raise ConflictException(f"Request is {req.status.value}; it has already been decided.")
            if data.decision == "APPROVE":
                req.approved_quantity = data.approved_quantity or req.requested_quantity
                if req.approved_quantity > req.requested_quantity:
                    raise BadRequestException("approved_quantity cannot exceed the requested quantity.")
                req.status = (SupplyRequestStatus.APPROVED if req.approved_quantity == req.requested_quantity
                              else SupplyRequestStatus.PARTIALLY_APPROVED)
            elif data.decision == "PARTIALLY_APPROVE":
                if data.approved_quantity >= req.requested_quantity:
                    raise BadRequestException("Partial approval must be below the requested quantity.")
                req.approved_quantity = data.approved_quantity
                req.status = SupplyRequestStatus.PARTIALLY_APPROVED
            elif data.decision == "REJECT":
                req.status = SupplyRequestStatus.REJECTED
            elif data.decision == "REQUEST_CLARIFICATION":
                req.status = SupplyRequestStatus.CLARIFICATION_REQUESTED
            req.reviewed_by = actor_id
            req.decision_reason = data.reason
        await self._event(req, actor_id, old, data.reason or data.decision.replace("_", " ").title())
        await self.session.flush()
        await self._audit(f"SUPPLY_REQUEST_{data.decision}", "supply_request", req.id, actor_id, ctx,
                          facility_id=req.requesting_facility_id, old_state={"status": old.value},
                          new_state={"status": req.status.value, "approved_quantity": req.approved_quantity,
                                     "reason": data.reason})
        return await self.get(req.id, j)

    async def clarify(self, request_id: uuid.UUID, data: SupplyRequestClarify, j: Jurisdiction, actor_id: uuid.UUID,
                      ctx: AuditCtx) -> SupplyRequest:
        req = await self.get(request_id, j, for_update=True)
        if req.status != SupplyRequestStatus.CLARIFICATION_REQUESTED:
            raise BadRequestException("Clarification can only be provided when it has been requested.")
        old = req.status
        req.reason = f"{req.reason}\n[Clarification] {data.note}"
        if data.requested_quantity:
            req.requested_quantity = data.requested_quantity
        req.status = SupplyRequestStatus.SUBMITTED
        await self._event(req, actor_id, old, data.note)
        await self.session.flush()
        await self._audit("SUPPLY_REQUEST_CLARIFIED", "supply_request", req.id, actor_id, ctx,
                          facility_id=req.requesting_facility_id, new_state={"status": req.status.value})
        return await self.get(req.id, j)

    # ------------------------------------------------------------------ allocation
    async def allocate(self, request_id: uuid.UUID, data: SupplyAllocationCreate, j: Jurisdiction,
                       actor_id: uuid.UUID, ctx: AuditCtx) -> SupplyRequest:
        req = await self.get(request_id, j, for_update=True)
        self._ensure_reviewer_level(req, j)
        if req.status not in (SupplyRequestStatus.APPROVED, SupplyRequestStatus.PARTIALLY_APPROVED):
            raise ConflictException(f"Request is {req.status.value}; only approved requests can be allocated.")
        if data.quantity > (req.approved_quantity or 0):
            raise BadRequestException(f"Allocation ({data.quantity}) exceeds approved quantity ({req.approved_quantity}).")
        source = await self._facility(data.fulfilling_facility_id)
        if source.id == req.requesting_facility_id:
            raise BadRequestException("Source and destination facilities must differ.")
        if source.state.lower() != req.state.lower():
            raise PermissionDeniedException("Stock can only be allocated from within the same state.")
        if req.level == SupplyRequestLevel.PHC_TO_DISTRICT and source.district.lower() != req.district.lower():
            raise BadRequestException("District requests must be fulfilled from within the district; escalate to state instead.")
        if source.facility_type == FacilityType.CENTRAL_WAREHOUSE and j.scope == ScopeLevel.DISTRICT:
            raise PermissionDeniedException("District officers cannot allocate State Warehouse stock; escalate to the state.")
        self._ensure_facility_in(j, source)

        item = (await self.session.execute(select(InventoryItem).where(
            InventoryItem.facility_id == source.id, InventoryItem.medication_id == req.medication_id,
        ).with_for_update())).scalar_one_or_none()
        if not item:
            raise BadRequestException(f"{source.name} holds no stock of this medicine.")
        usable, _ = await self._usable(source.id, req.medication_id)
        committed = await self._committed(source.id, req.medication_id)
        if data.quantity > usable - committed:
            raise ConflictException(
                f"Insufficient allocatable stock at {source.name}: usable {usable}, already committed {committed}."
            )
        transfer = StockTransfer(
            transfer_number=make_reference("TRF"), source_facility_id=source.id,
            destination_facility_id=req.requesting_facility_id, medication_id=req.medication_id,
            requested_quantity=data.quantity, status=StockTransferStatus.APPROVED,
            urgency=TransferUrgency.EMERGENCY_SHORTAGE if req.priority == PurchaseRequestUrgency.EMERGENCY else TransferUrgency.NORMAL,
            requested_by_id=req.requested_by, approved_by_id=actor_id,
            notes=f"Allocation for {req.reference}" + (f" | {data.notes}" if data.notes else ""),
        )
        self.session.add(transfer)
        await self.session.flush()
        old = req.status
        req.transfer_id = transfer.id
        req.fulfilling_facility_id = source.id
        req.status = SupplyRequestStatus.ALLOCATED
        await self._event(req, actor_id, old, f"Allocated {data.quantity} from {source.name} (transfer {transfer.transfer_number}).")
        await self.session.flush()
        await self._audit("SUPPLY_REQUEST_ALLOCATED", "supply_request", req.id, actor_id, ctx, facility_id=source.id,
                          new_state={"transfer": transfer.transfer_number, "quantity": data.quantity,
                                     "source": source.code})
        return await self.get(req.id, j)

    async def escalate(self, request_id: uuid.UUID, data: SupplyEscalationCreate, j: Jurisdiction,
                       actor_id: uuid.UUID, ctx: AuditCtx) -> SupplyRequest:
        """DSCO escalates an unmet PHC requirement to the State Supply Chain / Warehouse Manager."""
        req = await self.get(request_id, j, for_update=True)
        if req.level != SupplyRequestLevel.PHC_TO_DISTRICT:
            raise BadRequestException("Only district-level requests can be escalated to the state.")
        self._ensure_reviewer_level(req, j)
        if req.status not in (SupplyRequestStatus.SUBMITTED, SupplyRequestStatus.UNDER_REVIEW,
                              SupplyRequestStatus.APPROVED, SupplyRequestStatus.PARTIALLY_APPROVED):
            raise ConflictException(f"Request is {req.status.value}; it cannot be escalated.")
        # Prefer the district warehouse as the receiving point; fall back to the PHC itself.
        warehouse = (await self.session.execute(select(Facility).where(
            Facility.facility_type == FacilityType.DISTRICT_WAREHOUSE, Facility.is_active.is_(True),
            func.lower(Facility.district) == req.district.lower(), func.lower(Facility.state) == req.state.lower(),
        ))).scalars().first()
        child = SupplyRequest(
            reference=make_reference("SRQ"), level=SupplyRequestLevel.DISTRICT_TO_STATE,
            requesting_facility_id=warehouse.id if warehouse else req.requesting_facility_id,
            state=req.state, district=req.district, medication_id=req.medication_id,
            requested_quantity=data.quantity, priority=req.priority, status=SupplyRequestStatus.SUBMITTED,
            reason=f"Escalated from {req.reference}: {data.reason}", required_by=req.required_by,
            emergency_incident_id=req.emergency_incident_id, parent_request_id=req.id, requested_by=actor_id,
        )
        self.session.add(child)
        await self.session.flush()
        await self._event(child, actor_id, None, f"Escalated from {req.reference}.")
        old = req.status
        req.status = SupplyRequestStatus.ESCALATED
        req.reviewed_by = actor_id
        req.decision_reason = data.reason
        await self._event(req, actor_id, old, f"Escalated to state as {child.reference}: {data.reason}")
        self.session.add(Alert(
            facility_id=child.requesting_facility_id, alert_type=AlertType.CRITICAL_SHORTAGE,
            severity=AlertSeverity.EMERGENCY if req.priority == PurchaseRequestUrgency.EMERGENCY else AlertSeverity.CRITICAL,
            title=f"State escalation {child.reference}",
            message=f"District stock insufficient for {req.reference}; {data.quantity} units requested from state.",
        ))
        await self.session.flush()
        await self._audit("SUPPLY_REQUEST_ESCALATED", "supply_request", req.id, actor_id, ctx,
                          facility_id=req.requesting_facility_id,
                          new_state={"child": child.reference, "quantity": data.quantity})
        return await self.get(child.id, _state_view(req))

    # ------------------------------------------------------------------ receipts (called from PharmacyService)
    @staticmethod
    async def on_transfer_dispatched(session: AsyncSession, transfer: StockTransfer, actor_id: uuid.UUID) -> None:
        req = (await session.execute(select(SupplyRequest).where(SupplyRequest.transfer_id == transfer.id))).scalar_one_or_none()
        if req and req.status == SupplyRequestStatus.ALLOCATED:
            old = req.status
            req.status = SupplyRequestStatus.DISPATCHED
            session.add(SupplyRequestEvent(request_id=req.id, actor_id=actor_id, from_status=old.value,
                                           to_status=req.status.value,
                                           note=f"Dispatched {transfer.dispatched_quantity} units ({transfer.transfer_number})."))

    @staticmethod
    async def on_transfer_received(session: AsyncSession, transfer: StockTransfer, actor_id: uuid.UUID,
                                   received: int, damaged: int, batch_number: str, expiry_date: date,
                                   discrepancy_reason: Optional[str]) -> SupplyReceipt:
        dispatched = transfer.dispatched_quantity or 0
        if received + damaged < dispatched and not discrepancy_reason:
            raise BadRequestException(
                f"Received ({received}) plus damaged ({damaged}) is less than dispatched ({dispatched}); "
                "discrepancy_reason is required."
            )
        if received + damaged > dispatched:
            raise BadRequestException(f"Received plus damaged cannot exceed the dispatched quantity ({dispatched}).")
        if received == dispatched and not damaged and not discrepancy_reason:
            status = ReceiptVerificationStatus.VERIFIED
        elif received < dispatched:
            status = ReceiptVerificationStatus.PARTIALLY_RECEIVED
        else:
            status = ReceiptVerificationStatus.DISCREPANCY_REPORTED
        req = (await session.execute(select(SupplyRequest).where(SupplyRequest.transfer_id == transfer.id))).scalar_one_or_none()
        receipt = SupplyReceipt(
            transfer_id=transfer.id, supply_request_id=req.id if req else None,
            facility_id=transfer.destination_facility_id, medication_id=transfer.medication_id,
            dispatched_quantity=dispatched, received_quantity=received, damaged_quantity=damaged,
            batch_number=batch_number, expiry_date=expiry_date, verification_status=status,
            discrepancy_reason=discrepancy_reason, verified_by=actor_id,
        )
        session.add(receipt)
        if status != ReceiptVerificationStatus.VERIFIED:
            session.add(Alert(
                facility_id=transfer.source_facility_id, alert_type=AlertType.ABNORMAL_DEMAND,
                severity=AlertSeverity.WARNING, title=f"Receipt discrepancy on {transfer.transfer_number}",
                message=f"Dispatched {dispatched}, received {received}, damaged {damaged}. Reason: {discrepancy_reason or 'n/a'}",
            ))
        for r in [req] + ([await session.get(SupplyRequest, req.parent_request_id)] if req and req.parent_request_id else []):
            if r is None or r.requesting_facility_id != transfer.destination_facility_id:
                continue
            old = r.status
            r.received_quantity = (r.received_quantity or 0) + received
            target = r.approved_quantity or r.requested_quantity
            r.status = SupplyRequestStatus.FULFILLED if r.received_quantity >= target else SupplyRequestStatus.PARTIALLY_FULFILLED
            session.add(SupplyRequestEvent(
                request_id=r.id, actor_id=actor_id, from_status=old.value, to_status=r.status.value,
                note=f"Receipt verified: {received} received, {damaged} damaged ({status.value}).",
            ))
        await session.flush()
        return receipt

    async def list_receipts(self, j: Jurisdiction, status: Optional[ReceiptVerificationStatus], page: int, page_size: int):
        stmt = select(SupplyReceipt).join(Facility, SupplyReceipt.facility_id == Facility.id)
        if j.is_facility_bound:
            stmt = stmt.where(SupplyReceipt.facility_id == j.facility_id)
        else:
            stmt = j.filter(stmt, Facility.state, Facility.district if j.scope == ScopeLevel.DISTRICT else None)
        if status:
            stmt = stmt.where(SupplyReceipt.verification_status == status)
        return await paginate(self.session, stmt, SupplyReceipt.verified_at.desc(), page, page_size)

    # ------------------------------------------------------------------ DSCO → DHO health impact
    async def share_impact(self, data: HealthImpactCreate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> SupplyHealthImpact:
        if j.scope not in (ScopeLevel.DISTRICT, ScopeLevel.GLOBAL, ScopeLevel.STATE):
            raise PermissionDeniedException("Health impact notices are shared at district level.")
        state, district = j.state, j.district
        if data.affected_facility_id:
            f = await self._facility(data.affected_facility_id)
            self._ensure_facility_in(j, f)
            state, district = f.state, f.district
        if data.shortage_incident_id:
            inc = await self.session.get(ShortageIncident, data.shortage_incident_id)
            if not inc:
                raise ResourceNotFoundException("ShortageIncident", str(data.shortage_incident_id))
            f = await self._facility(inc.facility_id)
            self._ensure_facility_in(j, f)
            state, district = f.state, f.district
        if not state or not district:
            raise BadRequestException("affected_facility_id or shortage_incident_id is required outside district scope.")
        impact = SupplyHealthImpact(state=state, district=district, affected_facility_id=data.affected_facility_id,
                                    shortage_incident_id=data.shortage_incident_id, medication_id=data.medication_id,
                                    impact_summary=data.impact_summary, severity=data.severity, shared_by=actor_id)
        self.session.add(impact)
        await self.session.flush()
        await self._audit("SUPPLY_HEALTH_IMPACT_SHARED", "supply_health_impact", impact.id, actor_id, ctx,
                          facility_id=data.affected_facility_id, new_state={"severity": data.severity})
        return impact

    async def list_impacts(self, j: Jurisdiction, unacknowledged_only: bool, page: int, page_size: int):
        stmt = j.filter(select(SupplyHealthImpact), SupplyHealthImpact.state,
                        SupplyHealthImpact.district if j.scope != ScopeLevel.STATE else None)
        if unacknowledged_only:
            stmt = stmt.where(SupplyHealthImpact.acknowledged_by.is_(None))
        return await paginate(self.session, stmt, SupplyHealthImpact.created_at.desc(), page, page_size)

    async def acknowledge_impact(self, impact_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx):
        impact = await self.session.get(SupplyHealthImpact, impact_id)
        if not impact or not j.covers(impact.state, impact.district if j.scope != ScopeLevel.STATE else None):
            raise ResourceNotFoundException("SupplyHealthImpact", str(impact_id))
        if impact.acknowledged_by:
            raise ConflictException("Impact notice already acknowledged.")
        impact.acknowledged_by = actor_id
        impact.acknowledged_at = utcnow()
        await self.session.flush()
        await self._audit("SUPPLY_HEALTH_IMPACT_ACKNOWLEDGED", "supply_health_impact", impact.id, actor_id, ctx)
        return impact

    # ------------------------------------------------------------------ monitoring engine (Roles 07 & 10)
    async def _facilities(self, j: Jurisdiction) -> List[Facility]:
        stmt = select(Facility).where(Facility.is_active.is_(True))
        stmt = stmt.where(Facility.id == j.facility_id) if j.is_facility_bound else j.filter(stmt, Facility.state, Facility.district)
        return list((await self.session.execute(stmt)).scalars().all())

    async def _raise_once(self, facility_id, alert_type, severity, title, message) -> bool:
        exists = (await self.session.execute(select(Alert.id).where(
            Alert.facility_id == facility_id, Alert.title == title, Alert.is_acknowledged.is_(False),
        ))).first()
        if exists:
            return False
        self.session.add(Alert(facility_id=facility_id, alert_type=alert_type, severity=severity, title=title, message=message))
        return True

    async def run_monitoring(self, j: Jurisdiction) -> dict:
        facilities = await self._facilities(j)
        ids = [f.id for f in facilities]
        checks = {"stockouts": 0, "low_stock": 0, "expiring_batches": 0, "delayed_transfers": 0}
        created = skipped = 0
        if ids:
            available = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
            items = (await self.session.execute(
                select(InventoryItem, Medication.name).join(Medication, InventoryItem.medication_id == Medication.id)
                .where(InventoryItem.facility_id.in_(ids), available <= InventoryItem.reorder_level)
            )).all()
            for item, med in items:
                avail = item.quantity_on_hand - item.quantity_reserved
                if avail <= 0:
                    checks["stockouts"] += 1
                    ok = await self._raise_once(item.facility_id, AlertType.CRITICAL_SHORTAGE, AlertSeverity.CRITICAL,
                                                f"Stock-out: {med}", f"{med} has zero available stock (rule: available <= 0).")
                else:
                    checks["low_stock"] += 1
                    ok = await self._raise_once(item.facility_id, AlertType.LOW_STOCK, AlertSeverity.WARNING,
                                                f"Low stock: {med}",
                                                f"{med}: {avail} available, reorder level {item.reorder_level}.")
                created, skipped = created + ok, skipped + (not ok)
            horizon = date.today() + timedelta(days=EXPIRY_WINDOW_DAYS)
            batches = (await self.session.execute(
                select(InventoryBatch, InventoryItem.facility_id, Medication.name)
                .join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
                .join(Medication, InventoryItem.medication_id == Medication.id)
                .where(InventoryItem.facility_id.in_(ids), InventoryBatch.status == BatchStatus.AVAILABLE,
                       InventoryBatch.current_quantity > 0, InventoryBatch.expiry_date <= horizon)
            )).all()
            for b, fid, med in batches:
                checks["expiring_batches"] += 1
                ok = await self._raise_once(fid, AlertType.BATCH_EXPIRING, AlertSeverity.WARNING,
                                            f"Expiring batch {b.batch_number}: {med}",
                                            f"{b.current_quantity} units expire on {b.expiry_date} "
                                            f"(rule: within {EXPIRY_WINDOW_DAYS} days). Prioritise use or redistribution.")
                created, skipped = created + ok, skipped + (not ok)
            cutoff = datetime.now(timezone.utc) - timedelta(days=DELAY_THRESHOLD_DAYS)
            delayed = (await self.session.execute(select(StockTransfer).where(
                StockTransfer.status == StockTransferStatus.IN_TRANSIT, StockTransfer.dispatched_at < cutoff,
                (StockTransfer.source_facility_id.in_(ids)) | (StockTransfer.destination_facility_id.in_(ids)),
            ))).scalars().all()
            for t in delayed:
                checks["delayed_transfers"] += 1
                ok = await self._raise_once(t.destination_facility_id, AlertType.ABNORMAL_DEMAND, AlertSeverity.WARNING,
                                            f"Delayed delivery {t.transfer_number}",
                                            f"In transit since {t.dispatched_at:%Y-%m-%d} "
                                            f"(rule: > {DELAY_THRESHOLD_DAYS} days without receipt).")
                created, skipped = created + ok, skipped + (not ok)
        await self.session.flush()
        return {"scope": j.label, "run_at": utcnow(), "checks": checks, "alerts_created": created,
                "alerts_already_open": skipped, "method": MONITOR_METHOD}

    # ------------------------------------------------------------------ state dashboard (Role 10)
    async def state_dashboard(self, j: Jurisdiction) -> dict:
        facilities = await self._facilities(j)
        ids = [f.id for f in facilities]
        warehouses = [f for f in facilities if f.facility_type in WAREHOUSE_TYPES]
        wh_rows = []
        for w in warehouses:
            agg = (await self.session.execute(select(
                func.count(InventoryItem.id), func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0),
                func.coalesce(func.sum(InventoryItem.quantity_reserved), 0),
                func.sum(case((InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved <= InventoryItem.reorder_level, 1), else_=0)),
            ).where(InventoryItem.facility_id == w.id))).first()
            wh_rows.append({"facility_id": w.id, "name": w.name, "type": w.facility_type.value, "district": w.district,
                            "items_tracked": agg[0] or 0, "units_on_hand": int(agg[1] or 0),
                            "units_reserved": int(agg[2] or 0), "low_stock_items": int(agg[3] or 0),
                            "committed_to_allocations": int((await self.session.execute(
                                select(func.coalesce(func.sum(StockTransfer.requested_quantity), 0)).where(
                                    StockTransfer.source_facility_id == w.id,
                                    StockTransfer.status == StockTransferStatus.APPROVED))).scalar_one() or 0)})
        districts: Dict[str, dict] = {}
        if ids:
            available = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
            rows = (await self.session.execute(
                select(Facility.district, func.sum(case((available <= InventoryItem.reorder_level, 1), else_=0)),
                       func.sum(case((available <= 0, 1), else_=0)))
                .join(Facility, InventoryItem.facility_id == Facility.id)
                .where(InventoryItem.facility_id.in_(ids)).group_by(Facility.district)
            )).all()
            for d, low, out in rows:
                districts[d] = {"district": d, "low_stock_items": int(low or 0), "stockout_items": int(out or 0),
                                "open_requests": 0}
        req_stmt = j.filter(select(SupplyRequest.district, func.count()), SupplyRequest.state,
                            SupplyRequest.district if j.scope == ScopeLevel.DISTRICT else None)
        for d, n in (await self.session.execute(req_stmt.where(SupplyRequest.status.in_(OPEN_REQUEST_STATES))
                                                .group_by(SupplyRequest.district))).all():
            districts.setdefault(d, {"district": d, "low_stock_items": 0, "stockout_items": 0})["open_requests"] = n
        by_status_stmt = j.filter(select(SupplyRequest.status, func.count()), SupplyRequest.state,
                                  SupplyRequest.district if j.scope == ScopeLevel.DISTRICT else None)
        by_status = {s.value: n for s, n in (await self.session.execute(by_status_stmt.group_by(SupplyRequest.status))).all()}

        async def count(stmt) -> int:
            return (await self.session.execute(stmt)).scalar_one() or 0

        scoped_req = lambda stmt: j.filter(stmt, SupplyRequest.state,
                                           SupplyRequest.district if j.scope == ScopeLevel.DISTRICT else None)
        cutoff = datetime.now(timezone.utc) - timedelta(days=DELAY_THRESHOLD_DAYS)
        involving = (StockTransfer.source_facility_id.in_(ids)) | (StockTransfer.destination_facility_id.in_(ids))
        wh_ids = [w.id for w in warehouses]
        return {
            "as_of": utcnow(), "scope": j.label, "warehouses": wh_rows,
            "district_overview": sorted(districts.values(), key=lambda r: -(r["stockout_items"] * 10 + r["low_stock_items"])),
            "requests_by_status": by_status,
            "pending_district_requests": await count(scoped_req(select(func.count(SupplyRequest.id)).where(
                SupplyRequest.level == SupplyRequestLevel.DISTRICT_TO_STATE,
                SupplyRequest.status.in_([SupplyRequestStatus.SUBMITTED, SupplyRequestStatus.UNDER_REVIEW])))),
            "emergency_requests_open": await count(scoped_req(select(func.count(SupplyRequest.id)).where(
                SupplyRequest.priority == PurchaseRequestUrgency.EMERGENCY, SupplyRequest.status.in_(OPEN_REQUEST_STATES)))),
            "allocations_awaiting_dispatch": await count(select(func.count(StockTransfer.id)).where(
                StockTransfer.status == StockTransferStatus.APPROVED, involving)) if ids else 0,
            "in_transit_transfers": await count(select(func.count(StockTransfer.id)).where(
                StockTransfer.status == StockTransferStatus.IN_TRANSIT, involving)) if ids else 0,
            "delayed_transfers": await count(select(func.count(StockTransfer.id)).where(
                StockTransfer.status == StockTransferStatus.IN_TRANSIT, StockTransfer.dispatched_at < cutoff, involving)) if ids else 0,
            "receipt_discrepancies_30d": await count(select(func.count(SupplyReceipt.id)).where(
                SupplyReceipt.facility_id.in_(ids), SupplyReceipt.verification_status != ReceiptVerificationStatus.VERIFIED,
                SupplyReceipt.verified_at >= datetime.now(timezone.utc) - timedelta(days=30))) if ids else 0,
            "warehouse_batches_expiring_60d": await count(
                select(func.count(InventoryBatch.id)).join(InventoryItem, InventoryBatch.inventory_item_id == InventoryItem.id)
                .where(InventoryItem.facility_id.in_(wh_ids), InventoryBatch.status == BatchStatus.AVAILABLE,
                       InventoryBatch.current_quantity > 0,
                       InventoryBatch.expiry_date <= date.today() + timedelta(days=EXPIRY_WINDOW_DAYS))) if wh_ids else 0,
            "unacknowledged_supply_alerts": await count(select(func.count(Alert.id)).where(
                Alert.facility_id.in_(ids), Alert.is_acknowledged.is_(False))) if ids else 0,
        }


def _state_view(req: SupplyRequest) -> Jurisdiction:
    """Read-back view for a just-created child request (caller already authorized on the parent)."""
    return Jurisdiction(ScopeLevel.STATE, req.state, None, None)
