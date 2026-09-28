import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pharmacy import (
    BatchStatus,
    DispensingAllocation,
    DispensingRecord,
    InventoryBatch,
    InventoryItem,
    ShortageIncident,
    ShortageStatus,
    StockMovement,
    StockMovementType,
    StockTransfer,
    StockTransferStatus,
)


class PharmacyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # INVENTORY ITEM
    # ========================================================================

    async def get_inventory_item(
        self,
        facility_id: uuid.UUID,
        medication_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .where(
                InventoryItem.facility_id == facility_id,
                InventoryItem.medication_id == medication_id,
            )
            .options(
                selectinload(InventoryItem.medication),
                selectinload(InventoryItem.batches),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_inventory_item_by_id(
        self,
        item_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .where(InventoryItem.id == item_id)
            .options(
                selectinload(InventoryItem.medication),
                selectinload(InventoryItem.batches),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_inventory_item(self, item: InventoryItem) -> InventoryItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_inventory_items(
        self,
        facility_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[InventoryItem], int]:
        stmt = select(InventoryItem).options(
            selectinload(InventoryItem.medication),
            selectinload(InventoryItem.batches),
        )
        count_stmt = select(func.count(InventoryItem.id))

        if facility_id:
            stmt = stmt.where(InventoryItem.facility_id == facility_id)
            count_stmt = count_stmt.where(InventoryItem.facility_id == facility_id)

        if low_stock_only:
            condition = InventoryItem.quantity_on_hand <= InventoryItem.reorder_level
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        stmt = stmt.order_by(InventoryItem.quantity_on_hand.asc()).offset(offset).limit(limit)

        records_res = await self.session.execute(stmt)
        count_res = await self.session.execute(count_stmt)
        return records_res.scalars().all(), count_res.scalar() or 0

    # ========================================================================
    # INVENTORY BATCHES (FEFO ENGINE)
    # ========================================================================

    async def create_batch(self, batch: InventoryBatch) -> InventoryBatch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def get_batch_by_id(
        self,
        batch_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[InventoryBatch]:
        stmt = (
            select(InventoryBatch)
            .where(InventoryBatch.id == batch_id)
            .options(selectinload(InventoryBatch.inventory_item).selectinload(InventoryItem.medication))
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_batches_for_fefo(
        self,
        inventory_item_id: uuid.UUID,
        for_update: bool = True,
    ) -> Sequence[InventoryBatch]:
        """
        Retrieves active, unexpired batches ordered strictly by First-Expire, First-Out (FEFO).
        """
        today = date.today()
        stmt = (
            select(InventoryBatch)
            .where(
                InventoryBatch.inventory_item_id == inventory_item_id,
                InventoryBatch.status == BatchStatus.AVAILABLE,
                InventoryBatch.current_quantity > 0,
                InventoryBatch.expiry_date >= today,
            )
            .order_by(
                InventoryBatch.expiry_date.asc(),
                InventoryBatch.created_at.asc(),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_batches(
        self,
        inventory_item_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None,
        expiring_within_days: Optional[int] = None,
    ) -> Sequence[InventoryBatch]:
        stmt = select(InventoryBatch).options(
            selectinload(InventoryBatch.inventory_item).selectinload(InventoryItem.medication)
        )
        if inventory_item_id:
            stmt = stmt.where(InventoryBatch.inventory_item_id == inventory_item_id)
        if facility_id:
            stmt = stmt.join(InventoryItem).where(InventoryItem.facility_id == facility_id)
        if expiring_within_days is not None:
            target_date = date.today() + timedelta(days=expiring_within_days)
            stmt = stmt.where(
                InventoryBatch.status == BatchStatus.AVAILABLE,
                InventoryBatch.current_quantity > 0,
                InventoryBatch.expiry_date <= target_date,
            )
        stmt = stmt.order_by(InventoryBatch.expiry_date.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # ========================================================================
    # STOCK MOVEMENTS (IMMUTABLE LEDGER)
    # ========================================================================

    async def record_movement(self, movement: StockMovement) -> StockMovement:
        self.session.add(movement)
        await self.session.flush()
        return movement

    async def list_movements(
        self,
        facility_id: Optional[uuid.UUID] = None,
        inventory_item_id: Optional[uuid.UUID] = None,
        movement_type: Optional[StockMovementType] = None,
        limit: int = 50,
    ) -> Sequence[StockMovement]:
        stmt = select(StockMovement).options(
            selectinload(StockMovement.batch),
            selectinload(StockMovement.actor),
        )
        if facility_id:
            stmt = stmt.where(StockMovement.facility_id == facility_id)
        if inventory_item_id:
            stmt = stmt.where(StockMovement.inventory_item_id == inventory_item_id)
        if movement_type:
            stmt = stmt.where(StockMovement.movement_type == movement_type)
        stmt = stmt.order_by(StockMovement.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # ========================================================================
    # DISPENSING
    # ========================================================================

    async def create_dispensing_record(self, record: DispensingRecord) -> DispensingRecord:
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_dispensing_records(
        self,
        prescription_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None,
    ) -> Sequence[DispensingRecord]:
        stmt = select(DispensingRecord).options(
            selectinload(DispensingRecord.allocations).selectinload(DispensingAllocation.batch),
            selectinload(DispensingRecord.dispensed_by),
        )
        if prescription_id:
            stmt = stmt.where(DispensingRecord.prescription_id == prescription_id)
        if facility_id:
            stmt = stmt.where(DispensingRecord.facility_id == facility_id)
        stmt = stmt.order_by(DispensingRecord.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # ========================================================================
    # TRANSFERS
    # ========================================================================

    async def create_transfer(self, transfer: StockTransfer) -> StockTransfer:
        self.session.add(transfer)
        await self.session.flush()
        return transfer

    async def get_transfer_by_id(
        self,
        transfer_id: uuid.UUID,
        for_update: bool = False,
    ) -> Optional[StockTransfer]:
        stmt = (
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id)
            .options(
                selectinload(StockTransfer.medication),
                selectinload(StockTransfer.batch),
                selectinload(StockTransfer.source_facility),
                selectinload(StockTransfer.destination_facility),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_transfers(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[StockTransferStatus] = None,
    ) -> Sequence[StockTransfer]:
        stmt = select(StockTransfer).options(
            selectinload(StockTransfer.medication),
            selectinload(StockTransfer.source_facility),
            selectinload(StockTransfer.destination_facility),
        )
        if facility_id:
            stmt = stmt.where(
                (StockTransfer.source_facility_id == facility_id)
                | (StockTransfer.destination_facility_id == facility_id)
            )
        if status:
            stmt = stmt.where(StockTransfer.status == status)
        stmt = stmt.order_by(StockTransfer.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # ========================================================================
    # SHORTAGE INCIDENTS
    # ========================================================================

    async def create_shortage_incident(self, incident: ShortageIncident) -> ShortageIncident:
        self.session.add(incident)
        await self.session.flush()
        return incident

    async def get_shortage_incident_by_id(
        self,
        incident_id: uuid.UUID,
    ) -> Optional[ShortageIncident]:
        stmt = (
            select(ShortageIncident)
            .where(ShortageIncident.id == incident_id)
            .options(
                selectinload(ShortageIncident.medication),
                selectinload(ShortageIncident.facility),
                selectinload(ShortageIncident.reported_by),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_shortage_incidents(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[ShortageStatus] = None,
    ) -> Sequence[ShortageIncident]:
        stmt = select(ShortageIncident).options(
            selectinload(ShortageIncident.medication),
            selectinload(ShortageIncident.facility),
        )
        if facility_id:
            stmt = stmt.where(ShortageIncident.facility_id == facility_id)
        if status:
            stmt = stmt.where(ShortageIncident.status == status)
        stmt = stmt.order_by(ShortageIncident.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    # ========================================================================
    # INTELLIGENCE & CONSUMPTION ANALYTICS
    # ========================================================================

    async def get_dispensing_consumption(
        self,
        facility_id: uuid.UUID,
        medication_id: uuid.UUID,
        days: int = 30,
    ) -> Tuple[int, int]:
        """Returns (total_dispensed_units, count_of_dispensing_events) in the past `days`."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(
                func.coalesce(func.sum(StockMovement.quantity), 0),
                func.count(StockMovement.id),
            )
            .where(
                StockMovement.facility_id == facility_id,
                StockMovement.movement_type == StockMovementType.DISPENSE,
                StockMovement.created_at >= cutoff,
            )
            .join(InventoryItem, StockMovement.inventory_item_id == InventoryItem.id)
            .where(InventoryItem.medication_id == medication_id)
        )
        res = await self.session.execute(stmt)
        row = res.one()
        total_dispensed, event_count = row[0], row[1]
        return abs(int(total_dispensed)), int(event_count)

    async def get_recent_movements_for_analysis(
        self,
        facility_id: Optional[uuid.UUID] = None,
        days: int = 14,
    ) -> Sequence[StockMovement]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(StockMovement)
            .options(
                selectinload(StockMovement.inventory_item).selectinload(InventoryItem.medication),
                selectinload(StockMovement.batch),
                selectinload(StockMovement.facility),
            )
            .where(StockMovement.created_at >= cutoff)
            .order_by(StockMovement.created_at.desc())
        )
        if facility_id:
            stmt = stmt.where(StockMovement.facility_id == facility_id)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def list_items_for_medication(
        self,
        medication_id: uuid.UUID,
    ) -> Sequence[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .options(
                selectinload(InventoryItem.facility),
                selectinload(InventoryItem.medication),
            )
            .where(InventoryItem.medication_id == medication_id)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
