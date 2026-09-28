# ARCHITECTURE.md — System Architecture & Engineering Blueprint
## Smart Health & Supply Chain Resilience Platform

> **System Topology:** Modular Monolith (Domain-Driven, Configuration-Driven, Security-First)  
> **Framework:** FastAPI (Python 3.11+)  
> **Persistence:** PostgreSQL 15+ via Async SQLAlchemy 2.0  
> **Authentication:** Asymmetric/Symmetric Signed JWT with Stateful Refresh Tokens  
> **Authorization:** Fully Database-Driven Scoped RBAC

---

### 1. Conceptual Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Clients (Web / Mobile)                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS + Bearer JWT
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application Gateway                       │
│  - Correlation ID Middleware (X-Request-ID)                            │
│  - Security & Rate-Limiting Headers (CORS, CSP, X-Frame)               │
│  - Global RFC 7807 Exception Handlers                                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Dependency Layer                         │
│  - Authentication: get_current_user (JWT validation & session check)   │
│  - Authorization: require_permission(code) (RBAC + Scope Check)        │
│  - DB Session: get_db_session (AsyncSession generator per request)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Application Services / Use Cases                    │
│  - Orchestrates domain repositories and transaction boundaries         │
│  - Enforces Segregation of Duties (SoD) & State Machine rules          │
│  - Emits immutable Audit Events to AuditService                        │
└───────────────────────┬────────────────────────┬───────────────────────┘
                        │                        │
                        ▼                        ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│     Domain Repositories       │        │     Domain Services           │
│ - Pure SQLAlchemy 2.0 select  │        │ - Clinical validation logic   │
│ - with_for_update() locks     │        │ - FEFO batch allocation logic │
│ - Scoped tenant filters       │        │ - Stock balance reconciler    │
└───────────────┬───────────────┘        └───────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL 15+ Database                           │
│  - Row-Level Locking (Pessimistic Concurrency on Stock)                │
│  - Non-negative Check Constraints                                      │
│  - Foreign Key Relational Integrity & Indexed Lookup                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Transaction Management & Concurrency Control

#### 2.1 Critical Stock Allocation (Pessimistic Locking)
In healthcare and pharmaceutical supply chains, two nurses or pharmacists dispensing the last 10 units of an antibiotic simultaneously must **never** result in negative stock or phantom inventory.

To guarantee zero race conditions, inventory operations must use row-level locking (`with_for_update()`):

```python
# app/domains/inventory/repositories.py
async def get_batch_for_update(self, batch_id: UUID) -> MedicationBatch | None:
    stmt = (
        select(MedicationBatch)
        .where(MedicationBatch.id == batch_id)
        .with_for_update()  # Acquires exclusive row lock until transaction commit
    )
    result = await self._session.execute(stmt)
    return result.scalar_one_or_none()
```

#### 2.2 First-Expired, First-Out (FEFO) Allocation
When medications are dispensed or transferred, the system automatically suggests or allocates from batches with the earliest expiration date:
```sql
SELECT * FROM medication_batches
WHERE facility_id = :facility_id 
  AND medication_id = :medication_id
  AND quantity_available > 0
  AND is_quarantined = FALSE
ORDER BY expiry_date ASC
FOR UPDATE;
```

#### 2.3 Segregation of Duties (SoD)
State-changing executive actions enforce separation of roles at the business service layer:
- A user who drafted a `PurchaseOrder` cannot approve it (`created_by != approved_by`).
- A doctor who prescribed an item cannot dispense it in a facility staffed with a licensed pharmacist.

---

### 3. Error Handling Architecture (RFC 7807)

No raw Python tracebacks or inconsistent JSON dictionaries are ever emitted. All domain and system exceptions are intercepted by global handlers and mapped to RFC 7807 Problem Details:

```json
{
  "type": "https://errors.smarthealth.gov/insufficient-stock",
  "title": "Insufficient Stock Balance",
  "status": 409,
  "detail": "Batch B-2024-09 has only 5 units remaining, but 12 were requested for dispensing.",
  "instance": "/api/v1/prescriptions/a8f3.../dispense",
  "code": "INSUFFICIENT_STOCK",
  "trace_id": "req-98e3-47b2"
}
```

---

### 4. Background Job & Event Engine

Long-running or asynchronous operations must not block the main HTTP request/response cycle:
- **Audit Logging**: Recorded within the same transaction or pushed to an async event dispatcher.
- **Stock Alert Generation**: When `balance_after <= critical_level`, an alert record is immediately inserted and broadcast to the district dashboard.
- **Consumption Forecasting**: Scheduled nightly background workers compute rolling 30-day moving averages and Holt-Winters trend forecasts for vital medications.
