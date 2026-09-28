import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, ResourceNotFoundException
from app.models.intelligence import Alert, AlertSeverity, AlertType
from app.models.pharmacy import ShortageIncident, ShortageSeverity, ShortageStatus, StockTransferStatus
from app.models.supply_chain import (
    PurchaseOrder,
    PurchaseOrderStatus,
    PurchaseRequest,
    PurchaseRequestStatus,
    Shipment,
    ShipmentEvent,
    ShipmentEventType,
    ShipmentStatus,
    Supplier,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.repositories.supply_chain_repository import SupplyChainRepository
from app.schemas.supply_chain import (
    PurchaseOrderCreate,
    PurchaseRequestCreate,
    ShipmentCreate,
    ShipmentEventCreate,
    ShortageEscalateRequest,
    SupplierCreate,
)

TERMINAL_SHIPMENT_STATES = {ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED}
SHIPPABLE_PO_STATES = {PurchaseOrderStatus.ISSUED, PurchaseOrderStatus.ACKNOWLEDGED, PurchaseOrderStatus.IN_TRANSIT}
SHIPPABLE_TRANSFER_STATES = {StockTransferStatus.APPROVED, StockTransferStatus.DISPATCHED, StockTransferStatus.IN_TRANSIT}
ESCALATION_ORDER = [ShortageStatus.ESCALATED_DISTRICT, ShortageStatus.ESCALATED_STATE]


def _ref(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(4).upper()}"


class SupplyChainService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SupplyChainRepository(session)
        self.pharm_repo = PharmacyRepository(session)
        self.facility_repo = FacilityRepository(session)
        self.audit_repo = AuditRepository(session)

    async def _audit(self, action: str, resource_type: str, resource_id, actor_id, facility_id=None, new_state=None,
                     old_state=None, ctx: Tuple[Optional[str], Optional[str]] = (None, None)) -> None:
        await self.audit_repo.record_event(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            actor_id=actor_id,
            facility_id=facility_id,
            old_state=old_state,
            new_state=new_state,
            ip_address=ctx[0],
            user_agent=ctx[1],
        )

    async def _require_facility(self, facility_id: uuid.UUID) -> None:
        if not await self.facility_repo.get_facility_by_id(facility_id):
            raise ResourceNotFoundException("Facility", str(facility_id))

    # ------------------------------------------------------------------ suppliers
    async def create_supplier(self, data: SupplierCreate, actor_id: uuid.UUID, ctx) -> Supplier:
        if await self.repo.get_supplier_by_code(data.code):
            raise ConflictException(f"Supplier with code '{data.code}' already exists.")
        supplier = await self.repo.add(Supplier(**data.model_dump(), is_active=True))
        await self._audit("SUPPLIER_CREATED", "supplier", supplier.id, actor_id,
                          new_state={"code": supplier.code, "name": supplier.name}, ctx=ctx)
        return supplier

    async def list_suppliers(self, search, active_only, page, page_size):
        return await self.repo.list_suppliers(search, active_only, (page - 1) * page_size, page_size)

    # ------------------------------------------------------------------ purchase requests
    async def create_purchase_request(self, data: PurchaseRequestCreate, actor_id: uuid.UUID, ctx) -> PurchaseRequest:
        await self._require_facility(data.facility_id)
        pr = await self.repo.add(PurchaseRequest(**data.model_dump(), requested_by=actor_id,
                                                 status=PurchaseRequestStatus.SUBMITTED))
        await self._audit("PURCHASE_REQUEST_SUBMITTED", "purchase_request", pr.id, actor_id, pr.facility_id,
                          new_state={"urgency": pr.urgency.value}, ctx=ctx)
        return pr

    async def get_purchase_request(self, request_id: uuid.UUID) -> PurchaseRequest:
        pr = await self.repo.get_purchase_request(request_id)
        if not pr:
            raise ResourceNotFoundException("PurchaseRequest", str(request_id))
        return pr

    async def decide_purchase_request(self, pr: PurchaseRequest, approve: bool, notes: Optional[str],
                                      actor_id: uuid.UUID, ctx) -> PurchaseRequest:
        if pr.status != PurchaseRequestStatus.SUBMITTED:
            raise BadRequestException(f"Only SUBMITTED requests can be reviewed (current: {pr.status.value}).")
        if pr.requested_by == actor_id:
            raise BadRequestException("Segregation of duties: you cannot review your own purchase request.")
        pr.status = PurchaseRequestStatus.DISTRICT_APPROVED if approve else PurchaseRequestStatus.REJECTED
        if notes:
            pr.notes = f"{pr.notes}\n[Review] {notes}" if pr.notes else f"[Review] {notes}"
        await self.session.flush()
        await self._audit("PURCHASE_REQUEST_APPROVED" if approve else "PURCHASE_REQUEST_REJECTED",
                          "purchase_request", pr.id, actor_id, pr.facility_id,
                          new_state={"status": pr.status.value}, ctx=ctx)
        return pr

    async def list_purchase_requests(self, facility_ids, status, page, page_size):
        return await self.repo.list_purchase_requests(facility_ids, status, (page - 1) * page_size, page_size)

    # ------------------------------------------------------------------ purchase orders
    async def create_purchase_order(self, data: PurchaseOrderCreate, actor_id: uuid.UUID, ctx) -> PurchaseOrder:
        supplier = await self.repo.get_supplier(data.supplier_id)
        if not supplier:
            raise ResourceNotFoundException("Supplier", str(data.supplier_id))
        if not supplier.is_active:
            raise BadRequestException("Cannot raise a purchase order against an inactive supplier.")
        await self._require_facility(data.destination_facility_id)

        if data.purchase_request_id:
            pr = await self.get_purchase_request(data.purchase_request_id)
            if pr.status != PurchaseRequestStatus.DISTRICT_APPROVED:
                raise BadRequestException("Purchase request must be DISTRICT_APPROVED before conversion to a PO.")
            if pr.facility_id != data.destination_facility_id:
                raise BadRequestException("PO destination must match the purchase request's facility.")
            pr.status = PurchaseRequestStatus.CONVERTED_TO_PO

        po = await self.repo.add(PurchaseOrder(
            po_number=_ref("PO"),
            **data.model_dump(),
            created_by=actor_id,
            status=PurchaseOrderStatus.DRAFT,
        ))
        await self._audit("PURCHASE_ORDER_CREATED", "purchase_order", po.id, actor_id, po.destination_facility_id,
                          new_state={"po_number": po.po_number, "supplier": supplier.code}, ctx=ctx)
        return po

    async def get_purchase_order(self, po_id: uuid.UUID) -> PurchaseOrder:
        po = await self.repo.get_purchase_order(po_id)
        if not po:
            raise ResourceNotFoundException("PurchaseOrder", str(po_id))
        return po

    async def approve_purchase_order(self, po: PurchaseOrder, actor_id: uuid.UUID, ctx) -> PurchaseOrder:
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BadRequestException(f"Only DRAFT purchase orders can be approved (current: {po.status.value}).")
        if po.created_by == actor_id:
            raise BadRequestException("Segregation of duties: the PO creator cannot approve it.")
        po.status = PurchaseOrderStatus.ISSUED
        po.approved_by = actor_id
        await self.session.flush()
        await self._audit("PURCHASE_ORDER_APPROVED", "purchase_order", po.id, actor_id, po.destination_facility_id,
                          new_state={"status": po.status.value}, ctx=ctx)
        return po

    async def list_purchase_orders(self, facility_ids, supplier_id, status, page, page_size):
        return await self.repo.list_purchase_orders(facility_ids, supplier_id, status,
                                                    (page - 1) * page_size, page_size)

    # ------------------------------------------------------------------ shipments
    async def resolve_shipment_route(self, data: ShipmentCreate) -> Tuple[Optional[uuid.UUID], uuid.UUID]:
        if data.purchase_order_id:
            po = await self.get_purchase_order(data.purchase_order_id)
            if po.status not in SHIPPABLE_PO_STATES:
                raise BadRequestException(f"PO in status {po.status.value} cannot be shipped; it must be approved first.")
            return None, po.destination_facility_id
        transfer = await self.pharm_repo.get_transfer_by_id(data.transfer_id)
        if not transfer:
            raise ResourceNotFoundException("StockTransfer", str(data.transfer_id))
        if transfer.status not in SHIPPABLE_TRANSFER_STATES:
            raise BadRequestException(f"Transfer in status {transfer.status.value} cannot be shipped.")
        return transfer.source_facility_id, transfer.destination_facility_id

    async def create_shipment(self, data: ShipmentCreate, actor_id: uuid.UUID, ctx) -> Shipment:
        origin_id, destination_id = await self.resolve_shipment_route(data)
        shipment = await self.repo.add(Shipment(
            tracking_number=data.tracking_number or _ref("SHP"),
            purchase_order_id=data.purchase_order_id,
            transfer_id=data.transfer_id,
            origin_facility_id=origin_id,
            destination_facility_id=destination_id,
            status=ShipmentStatus.PENDING,
            carrier_name=data.carrier_name,
            temperature_monitored=data.temperature_monitored,
        ))
        await self._audit("SHIPMENT_CREATED", "shipment", shipment.id, actor_id, destination_id,
                          new_state={"tracking_number": shipment.tracking_number}, ctx=ctx)
        return await self.get_shipment(shipment.id)

    async def get_shipment(self, shipment_id: uuid.UUID) -> Shipment:
        shipment = await self.repo.get_shipment(shipment_id)
        if not shipment:
            raise ResourceNotFoundException("Shipment", str(shipment_id))
        return shipment

    async def log_shipment_event(self, shipment: Shipment, data: ShipmentEventCreate, actor_id: uuid.UUID,
                                 ctx) -> Shipment:
        if shipment.status in TERMINAL_SHIPMENT_STATES:
            raise BadRequestException(f"Shipment is {shipment.status.value}; no further events can be logged.")
        if data.event_type == ShipmentEventType.TEMPERATURE_EXCURSION and data.recorded_temp is None:
            raise BadRequestException("recorded_temp is required for TEMPERATURE_EXCURSION events.")

        now = datetime.now(timezone.utc)
        await self.repo.add_shipment_event(ShipmentEvent(
            shipment_id=shipment.id, logged_by=actor_id, timestamp=now, **data.model_dump(),
        ))

        po = await self.repo.get_purchase_order(shipment.purchase_order_id) if shipment.purchase_order_id else None
        if data.event_type in (ShipmentEventType.DEPARTED, ShipmentEventType.MILESTONE_CHECKPOINT):
            if shipment.dispatched_at is None:
                shipment.dispatched_at = now
            shipment.status = ShipmentStatus.IN_TRANSIT
            if po and po.status in (PurchaseOrderStatus.ISSUED, PurchaseOrderStatus.ACKNOWLEDGED):
                po.status = PurchaseOrderStatus.IN_TRANSIT
        elif data.event_type == ShipmentEventType.DELAY_REPORTED:
            shipment.status = ShipmentStatus.DELAYED
        elif data.event_type == ShipmentEventType.DELIVERED:
            shipment.status = ShipmentStatus.DELIVERED
            shipment.delivered_at = now
            if po:
                po.status = PurchaseOrderStatus.FULFILLED
        elif data.event_type == ShipmentEventType.TEMPERATURE_EXCURSION and shipment.temperature_monitored:
            await self.repo.create_alert(
                shipment.destination_facility_id,
                AlertType.COLD_CHAIN_BREACH,
                AlertSeverity.CRITICAL,
                f"Cold-chain excursion on shipment {shipment.tracking_number}",
                f"Recorded {data.recorded_temp}°C at {data.location_name or 'unknown location'}. "
                f"Quarantine and inspect affected stock on arrival.",
            )

        await self.session.flush()
        await self._audit("SHIPMENT_EVENT_LOGGED", "shipment", shipment.id, actor_id,
                          shipment.destination_facility_id,
                          new_state={"event": data.event_type.value, "status": shipment.status.value}, ctx=ctx)
        self.session.expire(shipment, ["events"])
        return await self.get_shipment(shipment.id)

    async def list_shipments(self, facility_ids, status, page, page_size):
        return await self.repo.list_shipments(facility_ids, status, (page - 1) * page_size, page_size)

    # ------------------------------------------------------------------ shortages
    async def escalate_shortage(self, incident: ShortageIncident, data: ShortageEscalateRequest,
                                actor_id: uuid.UUID, ctx) -> ShortageIncident:
        if incident.status in (ShortageStatus.RESOLVED, ShortageStatus.DISMISSED):
            raise BadRequestException(f"Cannot escalate a {incident.status.value} incident.")
        target = ShortageStatus.ESCALATED_DISTRICT if data.level == "DISTRICT" else ShortageStatus.ESCALATED_STATE
        if incident.status in ESCALATION_ORDER and ESCALATION_ORDER.index(incident.status) >= ESCALATION_ORDER.index(target):
            raise BadRequestException(f"Incident is already {incident.status.value}; escalation must go upward.")

        old = incident.status
        incident.status = target
        incident.resolution_notes = (
            f"{incident.resolution_notes}\n[Escalation] {data.notes}" if incident.resolution_notes
            else f"[Escalation] {data.notes}"
        )
        severity = (AlertSeverity.EMERGENCY if incident.severity == ShortageSeverity.CRITICAL
                    else AlertSeverity.CRITICAL)
        await self.repo.create_alert(
            incident.facility_id,
            AlertType.CRITICAL_SHORTAGE,
            severity,
            f"Shortage {incident.incident_number} escalated to {data.level.lower()} level",
            data.notes,
        )
        await self.session.flush()
        await self._audit("SHORTAGE_INCIDENT_ESCALATED", "shortage_incident", incident.id, actor_id,
                          incident.facility_id, old_state={"status": old.value},
                          new_state={"status": target.value}, ctx=ctx)
        return incident

    # ------------------------------------------------------------------ alerts
    async def list_alerts(self, facility_ids, acknowledged, severity, alert_type, page, page_size):
        return await self.repo.list_alerts(facility_ids, acknowledged, severity, alert_type,
                                           (page - 1) * page_size, page_size)

    async def get_alert(self, alert_id: uuid.UUID) -> Alert:
        alert = await self.repo.get_alert(alert_id)
        if not alert:
            raise ResourceNotFoundException("Alert", str(alert_id))
        return alert

    async def acknowledge_alert(self, alert: Alert, notes: Optional[str], actor_id: uuid.UUID, ctx) -> Alert:
        if alert.is_acknowledged:
            raise ConflictException("Alert has already been acknowledged.")
        alert.is_acknowledged = True
        alert.acknowledged_by = actor_id
        await self.session.flush()
        await self._audit("ALERT_ACKNOWLEDGED", "alert", alert.id, actor_id, alert.facility_id,
                          new_state={"notes": notes} if notes else None, ctx=ctx)
        return alert
