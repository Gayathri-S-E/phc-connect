# Phase 3 Design: Pharmacy, Inventory, and FEFO Dispensing

## 1. Domain Overview
The Pharmacy & Inventory subsystem connects clinical prescribing with physical medication inventory across health facilities (PHCs, CHCs, District Warehouses).

```
Prescription
   │
   ▼
PrescriptionItem (Clinical Intent)
   │
   ▼
InventoryItem (Facility-Medication Stock)
   │
   ▼
InventoryBatch (Physical Lot with Expiry)
   │
   ▼
FEFO Dispensing Engine (Earliest Expiry First)
   │
   ▼
DispensingRecord & DispensingAllocation (Physical Traceability)
   │
   ▼
StockMovement (Append-Only Immutable Ledger)
```

## 2. Core Entities & Database Constraints
1. **InventoryItem**:
   - Unique on `(facility_id, medication_id)`.
   - Non-negative check constraints on `quantity_on_hand` and `quantity_reserved`.
   - Thresholds: `reorder_level` (default 50), `minimum_stock_level` (default 20), `maximum_stock_level` (default 1000).
   - Dynamic server-side stock status: `NORMAL`, `LOW_STOCK`, `SHORTAGE_RISK`, `OUT_OF_STOCK`.

2. **InventoryBatch**:
   - Unique on `(inventory_item_id, batch_number)`.
   - Tracked properties: `manufacture_date`, `expiry_date`, `initial_quantity`, `current_quantity`, `supplier_name`.
   - Status: `AVAILABLE`, `QUARANTINED`, `EXPIRED`, `DEPLETED`, `DAMAGED`, `RECALLED`.
   - Check constraint: `current_quantity >= 0`, `initial_quantity > 0`.

3. **StockMovement**:
   - Append-only physical audit ledger.
   - Movement types: `RECEIPT`, `DISPENSE`, `TRANSFER_OUT`, `TRANSFER_IN`, `ADJUSTMENT`, `DAMAGE`, `EXPIRY`, `RETURN`.
   - Records `quantity`, `balance_after`, `actor_id`, `reference_id`, and `created_at`.

4. **DispensingRecord & DispensingAllocation**:
   - `DispensingRecord` links physical dispensing event to `Prescription`, `PrescriptionItem`, `Facility`, and `DispensedBy`.
   - `DispensingAllocation` maps units dispensed to specific batches, enabling multi-batch split allocation with batch-level traceability.

## 3. FEFO Allocation Algorithm
- Selects active, usable batches (`status == AVAILABLE`, `current_quantity > 0`, `expiry_date >= CURRENT_DATE`).
- Orders batches strictly by `expiry_date ASC, created_at ASC`.
- Allocates requested quantity sequentially across earliest expiring batches.
- When a batch quantity hits 0, its status automatically transitions to `DEPLETED`.
- Atomically executes within a database transaction locking rows with `with_for_update()`.
- Updates `PrescriptionItem.quantity_dispensed` and marks `Prescription` as `COMPLETED` or `PARTIALLY_DISPENSED`.
- Protects against over-dispensing beyond `quantity_prescribed`.

## 4. API Endpoints
- `GET /api/v1/inventory`: List facility inventory with pagination and low-stock filtering.
- `GET /api/v1/inventory/{id}`: Single inventory item details.
- `POST /api/v1/inventory/batches/receive`: Stock receipt with batch creation and ledger entry.
- `POST /api/v1/inventory/batches/adjust`: Stock adjustments (damage, expiry quarantine, count correction).
- `GET /api/v1/inventory/batches`: Query batches with optional filters (expiring within days, facility).
- `GET /api/v1/inventory/movements`: View immutable stock ledger movements.
- `POST /api/v1/prescriptions/{id}/dispense-fefo`: Execute multi-batch FEFO prescription dispensing.
- `GET /api/v1/prescriptions/{id}/dispensing-records`: View physical dispensing history with batch allocations.
