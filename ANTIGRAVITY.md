# ANTIGRAVITY.md
## Architectural Constitution & Engineering Standards

> **Status:** Canonical Architecture Reference  
> **Target Audience:** All AI Coding Agents, Software Architects, and Engineers  
> **Core Tenet:** Database-driven, Domain-driven, Configuration-driven, Security-first. Hardcoding dynamic business rules, static roles, or static permissions is strictly prohibited.

---

### Table of Contents
1. [Core Architectural Philosophy](#1-core-architectural-philosophy)
2. [Domain-Driven Design (DDD) Architecture](#2-domain-driven-design-ddd-architecture)
3. [Database-Driven Role-Based Access Control (RBAC)](#3-database-driven-role-based-access-control-rbac)
4. [Dynamic System Configuration & Navigation](#4-dynamic-system-configuration--navigation)
5. [Workflow & State Machine Engine](#5-workflow--state-machine-engine)
6. [Audit Logging & Security Controls](#6-audit-logging--security-controls)
7. [Backend Standards (FastAPI + SQLAlchemy 2.0)](#7-backend-standards-fastapi--sqlalchemy-20)
8. [Frontend Standards (React + TypeScript)](#8-frontend-standards-react--typescript)
9. [Database & Migration Standards (PostgreSQL + Alembic)](#9-database--migration-standards-postgresql--alembic)
10. [Strict Anti-Patterns & Prohibitions](#10-strict-anti-patterns--prohibitions)

---

### 1. Core Architectural Philosophy

This repository is built for multi-tenant, enterprise-grade scalability. Every agent and contributor must adhere to four immutable pillars:

1. **Database as the Source of Truth**: All roles, permissions, navigation trees, module enablement, workflow states, and business thresholds live in the database. Code defines *mechanisms*; data defines *policy*.
2. **Domain-Driven Boundaries**: Business logic is partitioned into strictly isolated business domains. Technical cross-cutting concerns live exclusively in `shared/`.
3. **Zero Hardcoded Authorization**: Neither frontend UI nor backend endpoints may gate actions using string role names like `"admin"` or `"manager"`. Every check evaluates granular, database-backed permission codes (`resource.action`).
4. **Defense in Depth**: Every layer (database constraints, domain invariants, application use cases, API dependencies, and frontend UI) independently validates authorization and business constraints.

---

### 2. Domain-Driven Design (DDD) Architecture

#### 2.1 Directory Structure
The backend repository must strictly follow this domain-partitioned structure:

```
backend/
├── alembic/                      # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── domains/                  # Isolated business domains
│   │   ├── identity/             # User accounts, credentials, MFA, sessions
│   │   ├── organization/         # Tenants, organizational units, memberships
│   │   ├── authorization/        # Roles, permissions, assignments, policies
│   │   ├── workflow/             # Dynamic state machines, transitions, approvals
│   │   ├── audit/                # Immutable change logs, access logs, compliance
│   │   ├── system_config/        # Feature flags, dynamic settings, limits
│   │   └── <business_domains>/   # Product-specific functional domains
│   │
│   ├── shared/                   # Cross-cutting infrastructural concerns ONLY
│   │   ├── database/             # Engine, session factory, base model, Unit of Work
│   │   ├── security/             # Password hashing, token signing/verification
│   │   ├── exceptions/           # Core domain & HTTP exception handlers
│   │   ├── logging/              # Structured JSON logging, correlation IDs
│   │   ├── middleware/           # Request ID, audit capture, CORS, rate limiting
│   │   └── pagination/           # Standardized offset/cursor pagination DTOs
│   │
│   ├── config.py                 # Pydantic BaseSettings (Environment variables)
│   └── main.py                   # FastAPI application factory and route assembly
├── tests/
│   ├── unit/                     # Domain & unit tests (no live DB required)
│   ├── integration/              # Real DB & repository tests
│   └── api/                      # End-to-end API test suites
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

#### 2.2 Domain Anatomy
Every folder under `app/domains/<domain_name>/` must be structured into explicit DDD layers:

```
app/domains/<domain_name>/
├── models.py         # SQLAlchemy ORM Entities & Table Mappings
├── schemas.py        # Pydantic v2 Request/Response DTOs
├── entities.py       # (Optional) Pure Domain Entities & Value Objects with invariants
├── repositories.py   # Database query abstraction (async session operations)
├── services.py       # Domain Services (pure domain business logic)
├── use_cases.py      # Application Services (orchestrates repo, UoW, events)
├── router.py         # FastAPI APIRouter (HTTP transport, request validation)
├── exceptions.py     # Domain-specific exceptions
└── events.py         # Domain Events emitted by this domain
```

#### 2.3 Cross-Domain Interaction Rules
- **No Direct Table Mutations**: Domain A must NEVER execute direct `INSERT`, `UPDATE`, or `DELETE` queries against Domain B's database tables.
- **Service/Event Interfaces**: Cross-domain actions must occur via Domain Services/Use Cases or Domain Event dispatchers.
- **Foreign Keys**: Direct foreign keys across distinct domain aggregates are permitted only at the database schema level for relational integrity, but ORM relationship cascades across domain boundaries must be avoided.

---

### 3. Database-Driven Role-Based Access Control (RBAC)

#### 3.1 Relational RBAC Schema
Authorization is completely decoupled from code. The database schema forms the authoritative graph:

```
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│      users       │       │      user_roles      │       │      roles       │
├──────────────────┤       ├──────────────────────┤       ├──────────────────┤
│ id (PK, UUID)    │───┐   │ user_id (FK)         │   ┌───│ id (PK, UUID)    │
│ organization_id  │   └──▶│ role_id (FK)         │◀──┘   │ organization_id  │
│ email            │       │ scope / context_id   │       │ name             │
│ is_active        │       │ assigned_at          │       │ code             │
└──────────────────┘       └──────────────────────┘       │ is_system / active│
                                                          └──────────────────┘
                                                                    │
                                                                    ▼
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│   permissions    │       │   role_permissions   │       │ role_permissions │
├──────────────────┤       ├──────────────────────┤       ├──────────────────┤
│ id (PK, UUID)    │◀──────│ role_id (FK)         │       │ (Junction table) │
│ code (UQ)        │       │ permission_id (FK)   │───────┘                  │
│ module           │       │ granted_at           │
│ resource         │       └──────────────────────┘
│ action           │
│ is_active        │
└──────────────────┘
```

#### 3.2 Permission Code Convention
Permissions are atomic, dot-delimited strings: `<module>.<resource>.<action>`.
- `users.profile.read`
- `billing.invoice.create`
- `billing.invoice.void`
- `inventory.warehouse.transfer`
- `workflow.transition.execute`

#### 3.3 Runtime Enforcement in FastAPI

```python
# CORRECT: Declarative, granular permission dependency
from fastapi import APIRouter, Depends, status
from app.domains.authorization.dependencies import require_permission
from app.domains.identity.entities import AuthenticatedUser

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("billing.invoice.create"))],
)
async def create_invoice(
    payload: InvoiceCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    use_case: CreateInvoiceUseCase = Depends(get_create_invoice_use_case),
):
    return await use_case.execute(payload, actor=current_user)
```

#### 3.4 Authorization Cache & Invalidation
- At login or token verification, user permissions are resolved from `user_roles` ➔ `role_permissions` ➔ `permissions`.
- Permissions may be cached in Redis or in a fast cryptographic session token.
- **Cache Invalidation**: Whenever an administrator updates a role, adds a permission, or revokes a role, the authorization cache for affected users must be immediately invalidated.

---

### 4. Dynamic System Configuration & Navigation

#### 4.1 Dynamic Navigation Contract
The frontend MUST NOT declare a hardcoded navigation menu or sidebar hierarchy with role checks. The backend provides the user's authorized navigation graph based on their database-stored permissions and tenant-enabled modules.

**Backend Schema (`app/domains/system_config/`):**
- `modules`: `id`, `code`, `name`, `is_enabled`, `sort_order`
- `menu_items`: `id`, `module_id`, `parent_id`, `title`, `route_path`, `icon_key`, `required_permission_code`, `sort_order`, `is_active`

**API Endpoint (`GET /api/v1/navigation/me`):**
Returns a pre-filtered tree containing only items where `user.has_permission(menu_item.required_permission_code)` evaluates to true and the parent module is enabled.

#### 4.2 Dynamic Settings & Feature Flags
All runtime thresholds (e.g., `max_file_upload_mb`, `session_timeout_minutes`, `enable_beta_workflows`) must be retrieved from the `system_settings` or `feature_flags` database tables, exposed via a caching service with fallback defaults.

---

### 5. Workflow & State Machine Engine

Business workflows (e.g., orders, approvals, escalations, claims) must be driven by database state machines:

1. **Workflow Definitions**: `workflow_definitions` table (`code`, `name`, `entity_type`).
2. **Workflow States**: `workflow_states` table (`workflow_id`, `state_code`, `is_initial`, `is_terminal`).
3. **State Transitions**: `workflow_transitions` table:
   - `from_state_id`
   - `to_state_id`
   - `action_code` (e.g., `APPROVE`, `REJECT`, `ESCALATE`)
   - `required_permission_code` (e.g., `orders.approval.execute`)
   - `guard_condition_json` (optional dynamic threshold rules)
4. **Transition Execution**: The workflow engine checks current state, verifies actor permission, tests guard conditions, updates state, and generates an audit entry atomically in a single transaction.

---

### 6. Audit Logging & Security Controls

#### 6.1 Audit Contract
Every state-changing HTTP request (`POST`, `PUT`, `PATCH`, `DELETE`) and sensitive data access (`EXPORT`, `BULK_READ`) must trigger an immutable audit event in `app/domains/audit/`.

**Audit Log Schema (`audit_logs`):**
- `id` (UUID, Primary Key)
- `organization_id` (UUID, Nullable for system events)
- `actor_id` (UUID, User ID who initiated action)
- `actor_ip` (INET / String)
- `actor_user_agent` (String)
- `action` (String, e.g., `USER_ROLE_ASSIGNED`, `INVOICE_VOIDED`)
- `resource_type` (String, e.g., `invoice`, `role`)
- `resource_id` (String / UUID)
- `old_state` (JSONB, Nullable)
- `new_state` (JSONB, Nullable)
- `timestamp` (TIMESTAMPTZ, default `clock_timestamp()`)

#### 6.2 Security Invariants
- Passwords must be hashed using `Argon2id` or `Bcrypt` (cost factor ≥ 12).
- Session tokens / JWTs must use asymmetric signing (`RS256` or `EdDSA`) or secure HS256 with cryptographically random secrets ≥ 256 bits.
- Tokens must be transmitted via `HttpOnly`, `Secure`, `SameSite=Strict` cookies or bearer headers with strict short expiration (e.g., 15m access, 7d refresh with rotation).
- Protection against OWASP Top 10: Automatic parameterized queries via SQLAlchemy, input sanitization via Pydantic v2, CORS restricted to trusted origins, CSP headers enabled.

---

### 7. Backend Standards (FastAPI + SQLAlchemy 2.0)

#### 7.1 Modern SQLAlchemy 2.0 Rules
- **Explicit 2.0 Syntax Only**: Never use legacy `session.query(Model)`. Always use `select(Model).where(...)`.
- **Async Execution**: Use `AsyncSession` with `create_async_engine("postgresql+asyncpg://...")`.
- **Unit of Work Pattern**: Use context-managed database sessions. Commits must occur at the Use Case / Application Service boundary, never inside repositories.

```python
# CORRECT SQLAlchemy 2.0 Repository pattern
from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.authorization.models import Role

class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, role_id: UUID) -> Role | None:
        stmt = select(Role).where(Role.id == role_id, Role.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_organization(self, organization_id: UUID) -> Sequence[Role]:
        stmt = select(Role).where(Role.organization_id == organization_id).order_by(Role.name)
        result = await self._session.execute(stmt)
        return result.scalars().all()
```

#### 7.2 Pydantic v2 DTOs
- All schemas must use `pydantic.BaseModel` with `model_config = ConfigDict(from_attributes=True, extra="forbid")`.
- Input validation (regex, bounds, data types) belongs in schemas before touching domain services.

#### 7.3 Exception Handling
- Domain exceptions must be defined in `app/domains/<domain>/exceptions.py`.
- Map domain exceptions to standardized HTTP responses using custom FastAPI exception handlers in `app/shared/exceptions/handlers.py` adhering to **RFC 7807 (Problem Details for HTTP APIs)**.

---

### 8. Frontend Standards (React + TypeScript)

#### 8.1 Modular Frontend Structure
```
frontend/
├── src/
│   ├── app/                      # App root, router, provider composition
│   ├── modules/                  # Feature modules corresponding to domains
│   │   ├── auth/                 # Login, MFA, password reset
│   │   ├── admin-rbac/           # Role builder, permission assigner
│   │   ├── navigation/           # Dynamic menu builder, header, sidebar
│   │   └── <feature_module>/     # Business UI, components, hooks, api
│   │
│   ├── shared/                   # Cross-cutting UI components and utilities
│   │   ├── components/           # Button, Modal, DataTable, Input, Card
│   │   ├── hooks/                # useAuth, usePermission, useDebounce
│   │   ├── api/                  # Axios/Fetch client, interceptors, error formatters
│   │   └── types/                # Standard API response & error types
│   │
│   └── main.tsx
```

#### 8.2 Declarative Permission Guards
The frontend must gate UI components using granular permission checks:

```tsx
// CORRECT: Declarative permission checking component
import React from "react";
import { useAuth } from "@/modules/auth/hooks/useAuth";

interface CanProps {
  permission: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const Can: React.FC<CanProps> = ({ permission, fallback = null, children }) => {
  const { hasPermission } = useAuth();
  
  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
};

// Usage Example in a Component
export const InvoiceToolbar = ({ invoiceId }: { invoiceId: string }) => {
  return (
    <div className="flex gap-2">
      <Can permission="billing.invoice.read">
        <button onClick={() => viewPdf(invoiceId)}>View PDF</button>
      </Can>
      <Can permission="billing.invoice.void">
        <button className="btn-danger" onClick={() => voidInvoice(invoiceId)}>
          Void Invoice
        </button>
      </Can>
    </div>
  );
};
```

---

### 9. Database & Migration Standards (PostgreSQL + Alembic)

- **PostgreSQL Specifics**: Use `UUID` primary keys (`uuid_generate_v4()` or `gen_random_uuid()`), `TIMESTAMPTZ` for dates, and `JSONB` for flexible workflow metadata.
- **Alembic Reversibility**: Every migration script must implement both `upgrade()` and `downgrade()` without loss of schema integrity.
- **Zero Raw Unchecked SQL**: Always generate DDL via Alembic revisions. Never modify live tables manually.
- **Index Constraints**: Every foreign key and queried code/slug column must be explicitly indexed.

---

### 10. Strict Anti-Patterns & Prohibitions

Any AI coding agent introducing the following patterns will be considered in direct violation of project guidelines:

| Anti-Pattern | Violation Type | Correct Replacement |
| :--- | :--- | :--- |
| `if user.role == "admin":` | Hardcoded RBAC | Query evaluated permissions: `if user.has_permission("users.manage"):` |
| `<AdminSidebar />` | Hardcoded UI | Render dynamic navigation tree fetched from `/api/v1/navigation/me` |
| `ALLOWED_ROLES = ["admin", "superadmin"]` | Role Whitelisting | Enforce granular permission: `Depends(require_permission("module.action"))` |
| `session.query(User).all()` | Legacy SQLAlchemy | `await session.execute(select(User))` (SQLAlchemy 2.0 async) |
| In-memory workflow state checks | Static Workflow | State transition graph stored and queried from database tables |
| Cross-domain table mutations | DDD Boundary Leak | Call target domain's Use Case or emit a Domain Event |
| Silent error catching `except: pass` | Audit / Reliability Failure | Re-throw domain exception or log structured error with trace ID |
