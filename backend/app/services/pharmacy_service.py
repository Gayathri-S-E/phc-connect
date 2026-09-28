import math
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, PermissionDeniedException, ResourceNotFoundException
from app.models.healthcare import Medication, Prescription, PrescriptionItem, PrescriptionItemStatus, PrescriptionStatus
from app.models.pharmacy import (
    BatchStatus,
    DispensingAllocation,
    DispensingRecord,
    InventoryBatch,
    InventoryItem,
    ShortageIncident,
    ShortageSeverity,
    ShortageStatus,
    StockMovement,
    StockMovementReferenceType,
    StockMovementType,
    StockTransfer,
    StockTransferStatus,
)
from app.models.supply_chain import Supplier
from app.repositories.audit_repository import AuditRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.healthcare_repository import HealthcareRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.services.supply_request_service import SupplyRequestService
from app.schemas.pharmacy import (
    DispenseItemFEFO,
    DispensePrescriptionRequest,
    InventoryBatchCreate,
    InventoryBatchResponse,
    InventoryBatchStatusUpdate,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    ShortageIncidentCreate,
    ShortageIncidentResolveRequest,
    ShortageIncidentResponse,
    StockAdjustmentRequest,
    StockMovementResponse,
    StockReceiptRequest,
    StockTransferApproveRequest,
    StockTransferCreate,
    StockTransferDispatchRequest,
    StockTransferReceiveRequest,
    StockTransferResponse,
)


class PharmacyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PharmacyRepository(session)
        self.health_repo = HealthcareRepository(session)
        self.facility_repo = FacilityRepository(session)
        self.audit_repo = AuditRepository(session)

    # ========================================================================
    # INVENTORY ITEM MANAGEMENT
    # ========================================================================

    def _compute_stock_status(self, item: InventoryItem) -> str:
        if item.quantity_on_hand == 0:
            return "OUT_OF_STOCK"
        elif item.quantity_on_hand <= item.minimum_stock_level:
            return "SHORTAGE_RISK"
        elif item.quantity_on_hand <= item.reorder_level:
            return "LOW_STOCK"
        return "NORMAL"

    def _to_inventory_item_response(self, item: InventoryItem) -> InventoryItemResponse:
        resp = InventoryItemResponse.model_validate(item)
        resp.stock_status = self._compute_stock_status(item)
        return resp

    async def get_or_create_inventory_item(
        self,
        facility_id: uuid.UUID,
        medication_id: uuid.UUID,
        reorder_level: int = 50,
        minimum_stock_level: int = 20,
        maximum_stock_level: int = 1000,
    ) -> InventoryItem:
        item = await self.repo.get_inventory_item(facility_id, medication_id, for_update=True)
        if not item:
            item = InventoryItem(
                facility_id=facility_id,
                medication_id=medication_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                reorder_level=reorder_level,
                minimum_stock_level=minimum_stock_level,
                maximum_stock_level=maximum_stock_level,
            )
            await self.repo.create_inventory_item(item)
        return item

    async def list_inventory(
        self,
        facility_id: Optional[uuid.UUID] = None,
        low_stock_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[InventoryItemResponse], int]:
        offset = (page - 1) * page_size
        items, total = await self.repo.list_inventory_items(
            facility_id=facility_id,
            low_stock_only=low_stock_only,
            offset=offset,
            limit=page_size,
        )
        responses = [self._to_inventory_item_response(it) for it in items]
        return responses, total

    async def get_inventory_item(
        self, item_id: uuid.UUID
    ) -> InventoryItemResponse:
        """Retrieve a single inventory item by its UUID. Used by GET /inventory/{item_id}."""
        item = await self.repo.get_inventory_item_by_id(item_id)
        if not item:
            raise ResourceNotFoundException("Inventory item", str(item_id))
        return self._to_inventory_item_response(item)

    async def get_inventory_item_details(
        self, facility_id: uuid.UUID, medication_id: uuid.UUID
    ) -> InventoryItemResponse:
        item = await self.repo.get_inventory_item(facility_id, medication_id)
        if not item:
            raise ResourceNotFoundException("Inventory item for specified facility and medication")
        return self._to_inventory_item_response(item)

    async def list_batches(
        self,
        inventory_item_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None,
        expiring_within_days: Optional[int] = None,
    ) -> List[InventoryBatchResponse]:
        batches = await self.repo.list_batches(
            inventory_item_id=inventory_item_id,
            facility_id=facility_id,
            expiring_within_days=expiring_within_days,
        )
        return [InventoryBatchResponse.model_validate(b) for b in batches]

    # ========================================================================
    # STOCK RECEIPT & ADJUSTMENTS
    # ========================================================================

    async def receive_stock(
        self,
        data: StockReceiptRequest,
        actor_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> InventoryBatchResponse:
        """
        Records verified receipt of medicine shipment into facility inventory.
        Creates or increments batch and updates the stock ledger atomically.
        """
        async with self.session.begin_nested():
            facility = await self.facility_repo.get_facility_by_id(data.facility_id)
            if not facility:
                raise ResourceNotFoundException("Facility", str(data.facility_id))

            medication = await self.health_repo.get_medication_by_id(data.medication_id)
            if not medication:
                raise ResourceNotFoundException("Medication", str(data.medication_id))

            if data.expiry_date <= date.today():
                raise BadRequestException("Cannot receive expired medication batches into active inventory.")

            supplier_name = data.supplier_name
            if data.supplier_id:
                supplier = await self.session.get(Supplier, data.supplier_id)
                if not supplier:
                    raise ResourceNotFoundException("Supplier", str(data.supplier_id))
                supplier_name = supplier_name or supplier.name

            item = await self.get_or_create_inventory_item(data.facility_id, data.medication_id)

            # Check if this batch number already exists for this inventory item
            batch = None
            existing_batches = await self.repo.list_batches(inventory_item_id=item.id)
            for b in existing_batches:
                if b.batch_number.upper() == data.batch_number.strip().upper():
                    batch = b
                    break

            if batch:
                batch.current_quantity += data.quantity
                batch.initial_quantity += data.quantity
                if batch.status == BatchStatus.DEPLETED:
                    batch.status = BatchStatus.AVAILABLE
            else:
                batch = InventoryBatch(
                    inventory_item_id=item.id,
                    batch_number=data.batch_number.strip().upper(),
                    manufacture_date=data.manufacture_date,
                    expiry_date=data.expiry_date,
                    initial_quantity=data.quantity,
                    current_quantity=data.quantity,
                    status=BatchStatus.AVAILABLE,
                    supplier_name=supplier_name,
                    supplier_id=data.supplier_id,
                    unit_cost=data.unit_cost,
                )
                await self.repo.create_batch(batch)

            # Update inventory total
            item.quantity_on_hand += data.quantity

            # Immutable stock ledger entry
            movement = StockMovement(
                facility_id=data.facility_id,
                inventory_item_id=item.id,
                batch_id=batch.id,
                movement_type=StockMovementType.RECEIPT,
                quantity=data.quantity,
                balance_after=item.quantity_on_hand,
                reference_type=StockMovementReferenceType.PO if data.purchase_order_id else None,
                reference_id=str(data.purchase_order_id) if data.purchase_order_id else None,
                notes=data.notes or f"Goods receipt: batch {batch.batch_number}",
                actor_id=actor_id,
            )
            await self.repo.record_movement(movement)

            await self.audit_repo.record_event(
                action="STOCK_RECEIVED",
                resource_type="inventory_batch",
                resource_id=str(batch.id),
                actor_id=actor_id,
                facility_id=data.facility_id,
                new_state={
                    "batch_number": batch.batch_number,
                    "quantity_received": data.quantity,
                    "new_balance": item.quantity_on_hand,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return InventoryBatchResponse.model_validate(batch)

    async def adjust_stock(
        self,
        data: StockAdjustmentRequest,
        actor_id: uuid.UUID,
        facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StockMovementResponse:
        """
        Performs audited physical stock adjustment (damage, expiry quarantine, count reconciliation).
        """
        async with self.session.begin_nested():
            batch = await self.repo.get_batch_by_id(data.batch_id, for_update=True)
            if not batch:
                raise ResourceNotFoundException("Batch", str(data.batch_id))

            item = await self.repo.get_inventory_item_by_id(batch.inventory_item_id, for_update=True)
            if not item:
                raise ResourceNotFoundException("Inventory item for batch", str(data.batch_id))

            if item.facility_id != facility_id:
                raise PermissionDeniedException("Cross-facility inventory adjustment prohibited.")

            # If deducting, ensure adequate stock exists
            if data.quantity < 0:
                deduction = abs(data.quantity)
                if batch.current_quantity < deduction:
                    raise BadRequestException(
                        f"Cannot deduct {deduction} units from batch '{batch.batch_number}'. Current quantity is only {batch.current_quantity}."
                    )
                if item.quantity_on_hand < deduction:
                    raise BadRequestException("Cannot deduct more stock than facility total on hand.")

            batch.current_quantity += data.quantity
            item.quantity_on_hand += data.quantity

            if batch.current_quantity == 0:
                batch.status = BatchStatus.DEPLETED

            movement = StockMovement(
                facility_id=facility_id,
                inventory_item_id=item.id,
                batch_id=batch.id,
                movement_type=data.movement_type,
                quantity=data.quantity,
                balance_after=item.quantity_on_hand,
                notes=data.notes,
                actor_id=actor_id,
            )
            await self.repo.record_movement(movement)

            await self.audit_repo.record_event(
                action="STOCK_ADJUSTED",
                resource_type="inventory_batch",
                resource_id=str(batch.id),
                actor_id=actor_id,
                facility_id=facility_id,
                new_state={
                    "adjustment_type": data.movement_type.value,
                    "adjustment_quantity": data.quantity,
                    "balance_after": item.quantity_on_hand,
                    "reason": data.notes,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return StockMovementResponse.model_validate(movement)

    # ========================================================================
    # FEFO DISPENSING ENGINE
    # ========================================================================

    async def dispense_prescription_fefo(
        self,
        prescription_id: uuid.UUID,
        payload: DispensePrescriptionRequest,
        pharmacist_id: uuid.UUID,
        facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> List[DispensingRecord]:
        """
        First-Expire, First-Out (FEFO) dispensing execution engine.
        Allocates requested medicine quantities strictly across earliest-expiring usable batches.
        Atomically updates batch quantities, stock ledger, dispensing records, and prescription status.
        """
        rx = await self.health_repo.get_prescription_by_id(prescription_id)
        if not rx:
            raise ResourceNotFoundException("Prescription", str(prescription_id))

        if rx.facility_id != facility_id:
            raise PermissionDeniedException("Prescriptions must be dispensed at the issuing health facility.")

        if rx.status in (PrescriptionStatus.DRAFT, PrescriptionStatus.CANCELLED):
            raise BadRequestException(f"Cannot dispense prescription in status '{rx.status.value}'.")

        if rx.status == PrescriptionStatus.COMPLETED:
            raise BadRequestException("Prescription is already fully completed and dispensed.")

        rx_items_by_id = {item.id: item for item in rx.items}
        dispensed_records = []

        async with self.session.begin_nested():
            for req_item in payload.items:
                if req_item.prescription_item_id not in rx_items_by_id:
                    raise BadRequestException(
                        f"Prescription item '{req_item.prescription_item_id}' does not belong to prescription '{prescription_id}'."
                    )

                p_item = rx_items_by_id[req_item.prescription_item_id]
                if p_item.status == PrescriptionItemStatus.CANCELLED:
                    raise BadRequestException(f"Cannot dispense cancelled item '{p_item.medication_name}'.")

                remaining_needed = p_item.quantity_prescribed - p_item.quantity_dispensed
                if req_item.quantity > remaining_needed:
                    raise BadRequestException(
                        f"Requested quantity ({req_item.quantity}) exceeds remaining prescribed quantity ({remaining_needed}) for '{p_item.medication_name}'."
                    )

                # Resolve Medication entity
                med_id = p_item.medication_id
                if not med_id:
                    # Find or auto-associate medication from catalog
                    med_query = p_item.medication_name.split()[0]
                    meds = await self.health_repo.list_medications(search=med_query)
                    if meds:
                        med_id = meds[0].id
                        p_item.medication_id = med_id
                    else:
                        raise BadRequestException(
                            f"Prescription item '{p_item.medication_name}' is not mapped to an active medication in the formulary."
                        )

                # Acquire row lock on facility inventory item
                inv_item = await self.repo.get_inventory_item(facility_id, med_id, for_update=True)
                if not inv_item:
                    raise BadRequestException(
                        f"No inventory record found at this facility for medication '{p_item.medication_name}'."
                    )

                # Retrieve usable batches ordered by FEFO: expiry_date ASC, created_at ASC
                usable_batches = await self.repo.get_batches_for_fefo(inv_item.id, for_update=True)
                total_available = sum(b.current_quantity for b in usable_batches)

                if total_available < req_item.quantity:
                    raise BadRequestException(
                        f"Insufficient stock for '{p_item.medication_name}'. Available usable stock: {total_available}, Requested: {req_item.quantity}."
                    )

                # Create Dispensing Record
                disp_record = DispensingRecord(
                    prescription_id=rx.id,
                    prescription_item_id=p_item.id,
                    facility_id=facility_id,
                    dispensed_by_id=pharmacist_id,
                    quantity_dispensed=req_item.quantity,
                    notes=payload.notes,
                )
                self.session.add(disp_record)
                await self.session.flush()

                # Allocate strictly across FEFO batches
                qty_to_allocate = req_item.quantity
                for batch in usable_batches:
                    if qty_to_allocate <= 0:
                        break

                    allocation_qty = min(qty_to_allocate, batch.current_quantity)
                    batch.current_quantity -= allocation_qty
                    if batch.current_quantity == 0:
                        batch.status = BatchStatus.DEPLETED

                    # Create batch allocation link
                    alloc = DispensingAllocation(
                        dispensing_record_id=disp_record.id,
                        batch_id=batch.id,
                        allocated_quantity=allocation_qty,
                    )
                    self.session.add(alloc)

                    qty_to_allocate -= allocation_qty

                # Deduct total from facility on hand
                inv_item.quantity_on_hand -= req_item.quantity

                # Record stock ledger movement
                movement = StockMovement(
                    facility_id=facility_id,
                    inventory_item_id=inv_item.id,
                    batch_id=usable_batches[0].id if usable_batches else None,
                    movement_type=StockMovementType.DISPENSE,
                    quantity=-req_item.quantity,
                    balance_after=inv_item.quantity_on_hand,
                    reference_id=str(rx.id),
                    notes=f"Dispensed for prescription {rx.id} item {p_item.medication_name}",
                    actor_id=pharmacist_id,
                )
                await self.repo.record_movement(movement)

                # Update prescription item progress
                p_item.quantity_dispensed += req_item.quantity
                if p_item.quantity_dispensed >= p_item.quantity_prescribed:
                    p_item.status = PrescriptionItemStatus.DISPENSED

                dispensed_records.append(disp_record)

            # Update overall prescription status
            all_dispensed = all(it.quantity_dispensed >= it.quantity_prescribed for it in rx.items)
            any_dispensed = any(it.quantity_dispensed > 0 for it in rx.items)

            if all_dispensed:
                rx.status = PrescriptionStatus.COMPLETED
            elif any_dispensed:
                rx.status = PrescriptionStatus.PARTIALLY_DISPENSED

            await self.audit_repo.record_event(
                action="PRESCRIPTION_DISPENSED_FEFO",
                resource_type="prescription",
                resource_id=str(rx.id),
                actor_id=pharmacist_id,
                facility_id=facility_id,
                new_state={
                    "prescription_status": rx.status.value,
                    "items_dispensed_count": len(payload.items),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return dispensed_records

    # ========================================================================
    # INTER-FACILITY STOCK TRANSFERS
    # ========================================================================

    def _generate_transfer_number(self) -> str:
        now = datetime.now(timezone.utc)
        random_suffix = secrets.randbelow(90000) + 10000
        return f"TRF-{now.strftime('%Y%m')}-{random_suffix}"

    async def create_transfer_request(
        self,
        data: StockTransferCreate,
        requester_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StockTransferResponse:
        if data.source_facility_id == data.destination_facility_id:
            raise BadRequestException("Source and destination facilities must be different.")

        source = await self.facility_repo.get_facility_by_id(data.source_facility_id)
        if not source:
            raise ResourceNotFoundException("Source facility", str(data.source_facility_id))

        dest = await self.facility_repo.get_facility_by_id(data.destination_facility_id)
        if not dest:
            raise ResourceNotFoundException("Destination facility", str(data.destination_facility_id))

        medication = await self.health_repo.get_medication_by_id(data.medication_id)
        if not medication:
            raise ResourceNotFoundException("Medication", str(data.medication_id))

        transfer = StockTransfer(
            transfer_number=self._generate_transfer_number(),
            source_facility_id=data.source_facility_id,
            destination_facility_id=data.destination_facility_id,
            medication_id=data.medication_id,
            requested_quantity=data.requested_quantity,
            status=StockTransferStatus.REQUESTED,
            urgency=data.urgency,
            requested_by_id=requester_id,
            notes=data.notes,
        )
        await self.repo.create_transfer(transfer)

        await self.audit_repo.record_event(
            action="STOCK_TRANSFER_REQUESTED",
            resource_type="stock_transfer",
            resource_id=str(transfer.id),
            actor_id=requester_id,
            facility_id=data.destination_facility_id,
            new_state={"transfer_number": transfer.transfer_number, "quantity": data.requested_quantity},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return StockTransferResponse.model_validate(transfer)

    async def approve_transfer(
        self,
        transfer_id: uuid.UUID,
        approver_id: uuid.UUID,
        data: StockTransferApproveRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StockTransferResponse:
        transfer = await self.repo.get_transfer_by_id(transfer_id, for_update=True)
        if not transfer:
            raise ResourceNotFoundException("StockTransfer", str(transfer_id))

        if transfer.status != StockTransferStatus.REQUESTED:
            raise BadRequestException(f"Cannot approve transfer in status '{transfer.status.value}'.")

        transfer.status = StockTransferStatus.APPROVED
        transfer.approved_by_id = approver_id
        if data.notes:
            transfer.notes = (transfer.notes or "") + f" | Approval: {data.notes}"

        await self.audit_repo.record_event(
            action="STOCK_TRANSFER_APPROVED",
            resource_type="stock_transfer",
            resource_id=str(transfer.id),
            actor_id=approver_id,
            facility_id=transfer.source_facility_id,
            new_state={"status": StockTransferStatus.APPROVED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return StockTransferResponse.model_validate(transfer)

    async def dispatch_transfer(
        self,
        transfer_id: uuid.UUID,
        dispatcher_id: uuid.UUID,
        data: StockTransferDispatchRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StockTransferResponse:
        """
        Phase 1 of physical transfer: Deducts stock from source facility and marks status IN_TRANSIT.
        """
        async with self.session.begin_nested():
            transfer = await self.repo.get_transfer_by_id(transfer_id, for_update=True)
            if not transfer:
                raise ResourceNotFoundException("StockTransfer", str(transfer_id))

            if transfer.status != StockTransferStatus.APPROVED:
                raise BadRequestException(f"Cannot dispatch transfer in status '{transfer.status.value}'. Must be APPROVED.")

            # Deduct from source inventory
            source_item = await self.repo.get_inventory_item(
                transfer.source_facility_id, transfer.medication_id, for_update=True
            )
            if not source_item:
                raise BadRequestException("Source facility does not have this medication in inventory.")

            # Select batch (either requested or earliest-expiring via FEFO)
            batches = await self.repo.get_batches_for_fefo(source_item.id, for_update=True)
            total_avail = sum(b.current_quantity for b in batches)

            if total_avail < data.dispatched_quantity:
                raise BadRequestException(
                    f"Source facility has insufficient usable stock ({total_avail}) for dispatch quantity ({data.dispatched_quantity})."
                )

            # Deduct across FEFO batch
            remaining_to_deduct = data.dispatched_quantity
            dispatched_batch_id = None
            for b in batches:
                if remaining_to_deduct <= 0:
                    break
                deduct = min(remaining_to_deduct, b.current_quantity)
                b.current_quantity -= deduct
                if b.current_quantity == 0:
                    b.status = BatchStatus.DEPLETED
                dispatched_batch_id = b.id
                remaining_to_deduct -= deduct

            source_item.quantity_on_hand -= data.dispatched_quantity

            # Record TRANSFER_OUT movement
            movement = StockMovement(
                facility_id=transfer.source_facility_id,
                inventory_item_id=source_item.id,
                batch_id=dispatched_batch_id,
                movement_type=StockMovementType.TRANSFER_OUT,
                quantity=-data.dispatched_quantity,
                balance_after=source_item.quantity_on_hand,
                reference_id=transfer.transfer_number,
                notes=f"Dispatched in transfer {transfer.transfer_number}",
                actor_id=dispatcher_id,
            )
            await self.repo.record_movement(movement)

            transfer.status = StockTransferStatus.IN_TRANSIT
            transfer.dispatched_quantity = data.dispatched_quantity
            transfer.batch_id = dispatched_batch_id
            transfer.dispatched_by_id = dispatcher_id
            transfer.dispatched_at = datetime.now(timezone.utc)
            await SupplyRequestService.on_transfer_dispatched(self.session, transfer, dispatcher_id)

            await self.audit_repo.record_event(
                action="STOCK_TRANSFER_DISPATCHED",
                resource_type="stock_transfer",
                resource_id=str(transfer.id),
                actor_id=dispatcher_id,
                facility_id=transfer.source_facility_id,
                new_state={"status": StockTransferStatus.IN_TRANSIT.value, "dispatched_qty": data.dispatched_quantity},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return StockTransferResponse.model_validate(transfer)

    async def receive_transfer(
        self,
        transfer_id: uuid.UUID,
        receiver_id: uuid.UUID,
        data: StockTransferReceiveRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StockTransferResponse:
        """
        Phase 2 of physical transfer: Adds received stock to destination facility inventory.
        """
        async with self.session.begin_nested():
            transfer = await self.repo.get_transfer_by_id(transfer_id, for_update=True)
            if not transfer:
                raise ResourceNotFoundException("StockTransfer", str(transfer_id))

            if transfer.status != StockTransferStatus.IN_TRANSIT:
                raise BadRequestException(f"Cannot receive transfer in status '{transfer.status.value}'. Must be IN_TRANSIT.")

            dest_item = await self.get_or_create_inventory_item(
                transfer.destination_facility_id, transfer.medication_id
            )

            # Get source batch details to replicate lot number and expiry date
            source_batch = None
            if transfer.batch_id:
                source_batch = await self.repo.get_batch_by_id(transfer.batch_id)

            if source_batch is None and not (data.batch_number and data.expiry_date):
                raise BadRequestException(
                    "Dispatched batch is unknown; the receiver must record batch_number and expiry_date."
                )
            # The receiver's verified batch/expiry wins over the dispatch record (Role 07 §8).
            batch_num = data.batch_number or source_batch.batch_number
            exp_date = data.expiry_date or source_batch.expiry_date
            mfg_date = source_batch.manufacture_date if source_batch else date.today()
            if exp_date < date.today():
                raise BadRequestException("Received stock is already expired; record it as damaged and report a discrepancy.")
            mismatch = []
            if source_batch and data.batch_number and data.batch_number != source_batch.batch_number:
                mismatch.append(f"batch {source_batch.batch_number} dispatched, {data.batch_number} received")
            if source_batch and data.expiry_date and data.expiry_date != source_batch.expiry_date:
                mismatch.append(f"expiry {source_batch.expiry_date} dispatched, {data.expiry_date} received")
            discrepancy_reason = "; ".join(filter(None, [data.discrepancy_reason] + mismatch)) or None

            # Find or create batch at destination
            dest_batch = None
            dest_batches = await self.repo.list_batches(inventory_item_id=dest_item.id)
            for b in dest_batches:
                if b.batch_number == batch_num:
                    dest_batch = b
                    break

            if dest_batch:
                dest_batch.current_quantity += data.received_quantity
                if dest_batch.status == BatchStatus.DEPLETED:
                    dest_batch.status = BatchStatus.AVAILABLE
            else:
                dest_batch = InventoryBatch(
                    inventory_item_id=dest_item.id,
                    batch_number=batch_num,
                    manufacture_date=mfg_date,
                    expiry_date=exp_date,
                    initial_quantity=data.received_quantity,
                    current_quantity=data.received_quantity,
                    status=BatchStatus.AVAILABLE,
                    supplier_name=f"Transferred from {transfer.source_facility.name if transfer.source_facility else 'PHC'}",
                )
                await self.repo.create_batch(dest_batch)

            dest_item.quantity_on_hand += data.received_quantity

            # Record TRANSFER_IN movement
            movement = StockMovement(
                facility_id=transfer.destination_facility_id,
                inventory_item_id=dest_item.id,
                batch_id=dest_batch.id,
                movement_type=StockMovementType.TRANSFER_IN,
                quantity=data.received_quantity,
                balance_after=dest_item.quantity_on_hand,
                reference_id=transfer.transfer_number,
                notes=f"Received transfer {transfer.transfer_number}",
                actor_id=receiver_id,
            )
            await self.repo.record_movement(movement)

            transfer.status = StockTransferStatus.RECEIVED
            transfer.received_quantity = data.received_quantity
            transfer.received_by_id = receiver_id
            transfer.received_at = datetime.now(timezone.utc)
            await SupplyRequestService.on_transfer_received(
                self.session, transfer, receiver_id, received=data.received_quantity,
                damaged=data.damaged_quantity, batch_number=batch_num, expiry_date=exp_date,
                discrepancy_reason=discrepancy_reason,
            )

            await self.audit_repo.record_event(
                action="STOCK_TRANSFER_RECEIVED",
                resource_type="stock_transfer",
                resource_id=str(transfer.id),
                actor_id=receiver_id,
                facility_id=transfer.destination_facility_id,
                new_state={"status": StockTransferStatus.RECEIVED.value, "received_qty": data.received_quantity},
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return StockTransferResponse.model_validate(transfer)

    async def list_transfers(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[StockTransferStatus] = None,
    ) -> List[StockTransferResponse]:
        transfers = await self.repo.list_transfers(facility_id=facility_id, status=status)
        return [StockTransferResponse.model_validate(t) for t in transfers]

    # ========================================================================
    # SHORTAGE INCIDENT REPORTING
    # ========================================================================

    def _generate_incident_number(self) -> str:
        now = datetime.now(timezone.utc)
        rand = secrets.randbelow(90000) + 10000
        return f"SHT-{now.strftime('%Y%m')}-{rand}"

    async def report_shortage_incident(
        self,
        data: ShortageIncidentCreate,
        reporter_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ShortageIncidentResponse:
        facility = await self.facility_repo.get_facility_by_id(data.facility_id)
        if not facility:
            raise ResourceNotFoundException("Facility", str(data.facility_id))

        medication = await self.health_repo.get_medication_by_id(data.medication_id)
        if not medication:
            raise ResourceNotFoundException("Medication", str(data.medication_id))

        incident = ShortageIncident(
            incident_number=self._generate_incident_number(),
            facility_id=data.facility_id,
            medication_id=data.medication_id,
            severity=data.severity,
            status=ShortageStatus.REPORTED,
            reported_by_id=reporter_id,
            description=data.description,
            estimated_impact_patients=data.estimated_impact_patients,
        )
        await self.repo.create_shortage_incident(incident)

        await self.audit_repo.record_event(
            action="SHORTAGE_INCIDENT_REPORTED",
            resource_type="shortage_incident",
            resource_id=str(incident.id),
            actor_id=reporter_id,
            facility_id=data.facility_id,
            new_state={"incident_number": incident.incident_number, "severity": data.severity.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return ShortageIncidentResponse.model_validate(incident)

    async def resolve_shortage_incident(
        self,
        incident_id: uuid.UUID,
        resolver_id: uuid.UUID,
        data: ShortageIncidentResolveRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ShortageIncidentResponse:
        incident = await self.repo.get_shortage_incident_by_id(incident_id)
        if not incident:
            raise ResourceNotFoundException("Shortage incident", str(incident_id))

        incident.status = ShortageStatus.RESOLVED
        incident.resolution_notes = data.resolution_notes
        incident.resolved_at = datetime.now(timezone.utc)

        await self.audit_repo.record_event(
            action="SHORTAGE_INCIDENT_RESOLVED",
            resource_type="shortage_incident",
            resource_id=str(incident.id),
            actor_id=resolver_id,
            facility_id=incident.facility_id,
            new_state={"status": ShortageStatus.RESOLVED.value, "notes": data.resolution_notes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return ShortageIncidentResponse.model_validate(incident)

    async def list_shortage_incidents(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[ShortageStatus] = None,
    ) -> List[ShortageIncidentResponse]:
        incidents = await self.repo.list_shortage_incidents(facility_id=facility_id, status=status)
        return [ShortageIncidentResponse.model_validate(i) for i in incidents]
