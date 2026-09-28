# Supply Chain Resilience Design: Inter-Facility Transfers & Shortage Monitoring

## 1. Overview
The Supply Chain Resilience subsystem coordinates inter-facility drug distribution, shortage mitigation, and inventory rebalancing between primary health centres, community health centres, and district warehouses.

```
       Source Facility (Warehouse / CHC)
                       │
       [1] REQUESTED (Requisition Created)
                       │
       [2] APPROVED (District/State Approval)
                       │
       [3] DISPATCHED (Source stock deducted, status IN_TRANSIT)
                       │
                       ▼
       [4] RECEIVED (Destination stock credited, status RECEIVED)
                       │
       Destination Facility (PHC)
```

## 2. Stock Transfer State Machine
1. `REQUESTED`: Initiated by destination facility or warehouse admin.
2. `APPROVED`: Authorized by district/state pharmacy officer.
3. `DISPATCHED`: Source facility dispatches batch. Deducts physical stock from source facility and creates `StockMovement(TRANSFER_OUT)`. Status transitions to `IN_TRANSIT`.
4. `RECEIVED`: Destination facility inspects and acknowledges delivery. Increments physical stock at destination and creates `StockMovement(TRANSFER_IN)`. Status transitions to `RECEIVED`.
5. `REJECTED` / `CANCELLED`: Terminal states preventing further inventory transactions.

### Guardrails:
- No stock deduction prior to `DISPATCHED`.
- Strict prevention of double-dispatch and double-receipt.
- Cross-facility scope verification: facility users cannot dispatch or receive stock for unassigned facilities.

## 3. Shortage Incident Management
- `ShortageIncident` tracking with canonical identifier `SHT-YYYYMM-XXXXX`.
- Severity levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- Lifecycle: `REPORTED` -> `INVESTIGATING` -> `ACTION_TAKEN` -> `RESOLVED`.
- Audited reporting and resolution with estimated patient impact tracking.

## 4. API Endpoints
- `POST /api/v1/transfers`: Request stock transfer between facilities.
- `GET /api/v1/transfers`: List stock transfers filtered by facility and status.
- `GET /api/v1/transfers/{id}`: View stock transfer details.
- `PATCH /api/v1/transfers/{id}/approve`: Approve transfer.
- `PATCH /api/v1/transfers/{id}/dispatch`: Dispatch shipment (stock deducted, marked `IN_TRANSIT`).
- `PATCH /api/v1/transfers/{id}/receive`: Receive shipment (destination stock credited, marked `RECEIVED`).
- `POST /api/v1/shortages`: Report shortage incident.
- `GET /api/v1/shortages`: List shortage incidents.
- `PATCH /api/v1/shortages/{id}/resolve`: Resolve incident with operational notes.
