# AI_START.md
## AI Agent Operational Handbook & Execution Protocol

> **Purpose:** This file defines the mandatory execution protocol for every AI agent interacting with this repository. Before authoring, modifying, refactoring, or reviewing any file, you MUST verify adherence to the instructions contained herein and in [ANTIGRAVITY.md](file:///f:/github/phc%20connect/ANTIGRAVITY.md).

---

### 1. The Prime Directives

Whenever you execute a coding task, you must operate under four non-negotiable constraints:

1. **NO Hardcoded Roles or Permissions**: You must never write `if user.role == ...`, `user.is_admin`, `ALLOWED_ROLES`, or conditional frontend renders based on role strings. Every authorization check evaluates database-backed granular permissions (`<module>.<resource>.<action>`).
2. **STRICT Domain Boundaries (DDD)**: Code must reside within its bounded context under `app/domains/<domain>/`. Do not create a single global `models/` or `services/` directory. Technical infrastructure belongs in `app/shared/`.
3. **Configuration & Data Over Code**: Navigation trees, business limits, feature flags, and workflow state transitions are defined in the database, never hardcoded in TypeScript or Python.
4. **SQLAlchemy 2.0 Async Exclusively**: Never use legacy `session.query()`. Always use `select()`, `insert()`, `update()`, and `delete()` constructs with `AsyncSession`.

---

### 2. Pre-Flight Checklist (Run Before Touching Code)

Before writing or editing code for any feature or bugfix, complete this mental and architectural audit:

- [ ] **Domain Context**: Which domain does this logic belong to? If it spans multiple domains, are you respecting boundaries and communicating via services/events rather than direct table writes?
- [ ] **Authorization Invariant**: What exact permission code (`<module>.<resource>.<action>`) guards this operation? Is it properly seeded or manageable via the RBAC database schema?
- [ ] **Audit Requirement**: Does this operation mutate state? If yes, will an audit log entry with `old_state` and `new_state` be recorded atomically?
- [ ] **Schema & Migration**: Does this change require an Alembic migration? Is the migration reversible with a non-destructive `downgrade()`?
- [ ] **Type Integrity**: Are request/response payloads strictly validated with Pydantic v2 (`extra="forbid"`) on the backend and TypeScript interfaces on the frontend?

---

### 3. Step-by-Step Feature Implementation Workflow

When asked to create a new feature or endpoint, follow this exact sequence:

```
┌────────────────────────────────────────────────────────┐
│ 1. Database Model & Migration                          │
│    (app/domains/<domain>/models.py + Alembic revision) │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. Pydantic v2 DTOs & Schemas                          │
│    (app/domains/<domain>/schemas.py)                   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Repository Layer (Data Access)                      │
│    (app/domains/<domain>/repositories.py)              │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. Domain & Application Services (Use Cases)           │
│    (app/domains/<domain>/services.py & use_cases.py)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 5. FastAPI Route & Security Dependency                 │
│    (app/domains/<domain>/router.py)                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 6. Frontend Module & Declarative Guards                │
│    (frontend/src/modules/<domain>/ + <Can /> component)│
└────────────────────────────────────────────────────────┘
```

#### Step 3.1: Seed Database-Driven Permissions
Never assume permissions exist out of thin air. When introducing a new capability, define it in a database migration:
```python
# In Alembic migration upgrade():
def upgrade():
    # Insert permission into 'permissions' table
    op.execute(
        """
        INSERT INTO permissions (id, code, module, resource, action, description, is_active)
        VALUES (
            gen_random_uuid(),
            'inventory.warehouse.transfer',
            'inventory',
            'warehouse',
            'transfer',
            'Permission to transfer stock between warehouses',
            true
        )
        ON CONFLICT (code) DO NOTHING;
        """
    )
```

#### Step 3.2: FastAPI Route & Guard
```python
# backend/app/domains/inventory/router.py
from fastapi import APIRouter, Depends, status
from app.domains.authorization.dependencies import require_permission
from app.domains.identity.entities import AuthenticatedUser
from app.domains.identity.dependencies import get_current_user
from app.domains.inventory.schemas import StockTransferRequest, StockTransferResponse
from app.domains.inventory.use_cases import StockTransferUseCase

router = APIRouter(prefix="/inventory/transfers", tags=["Inventory"])

@router.post(
    "",
    response_model=StockTransferResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory.warehouse.transfer"))],
)
async def transfer_stock(
    payload: StockTransferRequest,
    actor: AuthenticatedUser = Depends(get_current_user),
    use_case: StockTransferUseCase = Depends(get_stock_transfer_use_case),
):
    return await use_case.execute(payload, actor=actor)
```

#### Step 3.3: Frontend Declarative UI Guard
```tsx
// frontend/src/modules/inventory/components/TransferStockButton.tsx
import React from "react";
import { Can } from "@/shared/components/Can";
import { Button } from "@/shared/components/Button";

interface TransferStockButtonProps {
  onOpenModal: () => void;
}

export const TransferStockButton: React.FC<TransferStockButtonProps> = ({ onOpenModal }) => {
  return (
    <Can permission="inventory.warehouse.transfer">
      <Button variant="primary" onClick={onOpenModal}>
        Transfer Stock
      </Button>
    </Can>
  );
};
```

---

### 4. Self-Audit Verification Script

Before declaring any task complete, an AI agent must mentally or programmatically scan its changes for red flags.

#### Red Flag Scanner (Immediate Rejection Criteria):

```bash
# Verify no role-based hardcoding exists in code:
grep -rn "user.role ==" backend/ frontend/
grep -rn "user.role ===" backend/ frontend/
grep -rn "ALLOWED_ROLES" backend/ frontend/
grep -rn 'role == "admin"' backend/ frontend/

# Verify no legacy SQLAlchemy 1.x queries:
grep -rn "session.query(" backend/

# Verify no direct cross-domain model imports inside repositories:
# (e.g., InventoryRepository importing BillingModel)
```

If any search yields results, **you must refactor immediately** before presenting the solution to the user.

---

### 5. Standard Error Handling Pattern (RFC 7807)

Never return ad-hoc error dicts like `{"error": "something went wrong"}`. All errors must use standardized Problem Details:

```json
{
  "type": "https://api.domain.com/errors/insufficient-stock",
  "title": "Insufficient Stock Available",
  "status": 409,
  "detail": "Warehouse WH-01 has 4 units of item SKU-999, but 10 were requested.",
  "instance": "/api/v1/inventory/transfers",
  "invalid_params": [
    {
      "name": "quantity",
      "reason": "Requested quantity exceeds available stock balance"
    }
  ]
}
```

---

### 6. Definition of Done (DoD)

An AI coding agent may only mark a task as completed when:
1. **Architectural Compliance**: The code resides in the proper domain directory matching the DDD specifications in `ANTIGRAVITY.md`.
2. **Zero RBAC Hardcoding**: Every route and UI component checks dynamic, database-backed permissions.
3. **Database Migration Present**: Any schema or permission modification includes a valid, reversible Alembic migration.
4. **Audit Logging Configured**: Any mutation or state transition emits an immutable audit event with actor context.
5. **No Broken Tests**: Unit and integration test suites pass without regression.
6. **Documentation Updated**: If new domain capabilities, configuration flags, or entities were introduced, their schemas and permissions are documented in the domain's README or migration notes.
