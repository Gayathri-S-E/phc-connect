import uuid
from typing import Iterable, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.intelligence import Alert, AlertSeverity, AlertType, ForecastRecord
from app.models.supply_chain import (
    PurchaseOrder,
    PurchaseOrderStatus,
    PurchaseRequest,
    PurchaseRequestStatus,
    Shipment,
    ShipmentEvent,
    ShipmentStatus,
    Supplier,
)


async def _paginate(session: AsyncSession, stmt, order_by, offset: int, limit: int) -> Tuple[Sequence, int]:
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    res = await session.execute(stmt.order_by(order_by).offset(offset).limit(limit))
    return res.scalars().all(), total


class SupplyChainRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, obj):
        self.session.add(obj)
        await self.session.flush()
        return obj

    # --- Suppliers ---
    async def get_supplier(self, supplier_id: uuid.UUID) -> Optional[Supplier]:
        return await self.session.get(Supplier, supplier_id)

    async def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        res = await self.session.execute(select(Supplier).where(Supplier.code == code))
        return res.scalar_one_or_none()

    async def list_suppliers(
        self, search: Optional[str], active_only: bool, offset: int, limit: int
    ) -> Tuple[Sequence[Supplier], int]:
        stmt = select(Supplier)
        if active_only:
            stmt = stmt.where(Supplier.is_active.is_(True))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(or_(func.lower(Supplier.name).like(like), func.lower(Supplier.code).like(like)))
        return await _paginate(self.session, stmt, Supplier.name.asc(), offset, limit)

    # --- Purchase requests ---
    async def get_purchase_request(self, request_id: uuid.UUID) -> Optional[PurchaseRequest]:
        return await self.session.get(PurchaseRequest, request_id)

    async def list_purchase_requests(
        self,
        facility_ids: Optional[Iterable[uuid.UUID]],
        status: Optional[PurchaseRequestStatus],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[PurchaseRequest], int]:
        stmt = select(PurchaseRequest)
        if facility_ids is not None:
            stmt = stmt.where(PurchaseRequest.facility_id.in_(list(facility_ids)))
        if status:
            stmt = stmt.where(PurchaseRequest.status == status)
        return await _paginate(self.session, stmt, PurchaseRequest.created_at.desc(), offset, limit)

    # --- Purchase orders ---
    async def get_purchase_order(self, po_id: uuid.UUID) -> Optional[PurchaseOrder]:
        return await self.session.get(PurchaseOrder, po_id)

    async def list_purchase_orders(
        self,
        facility_ids: Optional[Iterable[uuid.UUID]],
        supplier_id: Optional[uuid.UUID],
        status: Optional[PurchaseOrderStatus],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[PurchaseOrder], int]:
        stmt = select(PurchaseOrder)
        if facility_ids is not None:
            stmt = stmt.where(PurchaseOrder.destination_facility_id.in_(list(facility_ids)))
        if supplier_id:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)
        return await _paginate(self.session, stmt, PurchaseOrder.created_at.desc(), offset, limit)

    # --- Shipments ---
    async def get_shipment(self, shipment_id: uuid.UUID) -> Optional[Shipment]:
        res = await self.session.execute(
            select(Shipment).where(Shipment.id == shipment_id).options(selectinload(Shipment.events))
        )
        return res.scalar_one_or_none()

    async def list_shipments(
        self,
        facility_ids: Optional[Iterable[uuid.UUID]],
        status: Optional[ShipmentStatus],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[Shipment], int]:
        stmt = select(Shipment).options(selectinload(Shipment.events))
        if facility_ids is not None:
            ids = list(facility_ids)
            stmt = stmt.where(or_(Shipment.destination_facility_id.in_(ids), Shipment.origin_facility_id.in_(ids)))
        if status:
            stmt = stmt.where(Shipment.status == status)
        return await _paginate(self.session, stmt, Shipment.created_at.desc(), offset, limit)

    async def add_shipment_event(self, event: ShipmentEvent) -> ShipmentEvent:
        return await self.add(event)

    # --- Alerts ---
    async def create_alert(
        self,
        facility_id: Optional[uuid.UUID],
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
    ) -> Alert:
        return await self.add(
            Alert(facility_id=facility_id, alert_type=alert_type, severity=severity, title=title, message=message)
        )

    async def get_alert(self, alert_id: uuid.UUID) -> Optional[Alert]:
        return await self.session.get(Alert, alert_id)

    async def list_alerts(
        self,
        facility_ids: Optional[Iterable[uuid.UUID]],
        acknowledged: Optional[bool],
        severity: Optional[AlertSeverity],
        alert_type: Optional[AlertType],
        offset: int,
        limit: int,
    ) -> Tuple[Sequence[Alert], int]:
        stmt = select(Alert)
        if facility_ids is not None:
            stmt = stmt.where(or_(Alert.facility_id.in_(list(facility_ids)), Alert.facility_id.is_(None)))
        if acknowledged is not None:
            stmt = stmt.where(Alert.is_acknowledged.is_(acknowledged))
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type)
        return await _paginate(self.session, stmt, Alert.created_at.desc(), offset, limit)

    async def add_forecast_record(self, record: ForecastRecord) -> ForecastRecord:
        return await self.add(record)
