# RBAC.md — Role-Based Access Control Architecture & Matrix
## Smart Health & Supply Chain Resilience Platform

> **Guiding Principle:** Authorization is 100% database-driven. Code never references static role names like `"admin"` or `"doctor"` for authorization decisions. Instead, endpoints and services strictly enforce granular, database-backed permission codes (`module.resource.action`) evaluated against the authenticated user's active assignments, tenant/facility scope, and resource ownership.

---

### 1. Architectural Model

The platform uses a contextual, scoped RBAC model:

```
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│      User       │       │      UserRole        │       │      Role       │
├─────────────────┤       ├──────────────────────┤       ├─────────────────┤
│ id (UUID)       │───┐   │ user_id (FK)         │   ┌───│ id (UUID)       │
│ email           │   └──▶│ role_id (FK)         │◀──┘   │ name            │
│ is_active       │       │ organization_id (FK) │       │ code (slug)     │
│ is_verified     │       │ facility_id (FK)     │       │ description     │
└─────────────────┘       │ scope_level          │       │ is_system       │
                          │ granted_at           │       │ is_active       │
                          └──────────────────────┘       └─────────────────┘
                                                                   │
                                                                   ▼
┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│   Permission    │       │    RolePermission    │       │ RolePermission  │
├─────────────────┤       ├──────────────────────┤       ├─────────────────┤
│ id (UUID)       │◀──────│ role_id (FK)         │       │ (Junction)      │
│ code (UQ)       │       │ permission_id (FK)   │───────┘                 │
│ module          │       │ granted_at           │
│ resource        │       └──────────────────────┘
│ action          │
│ description     │
│ is_active       │
└─────────────────┘
```

#### Scope Hierarchy
A user's role assignment can be scoped at different administrative levels:
1. **GLOBAL**: Unrestricted across all entities (platform administrators, national oversight).
2. **STATE**: Scoped to health facilities and warehouses in a specific state.
3. **DISTRICT**: Scoped to district headquarters, district warehouses, and community health centers.
4. **FACILITY**: Scoped to an individual Primary Health Centre (PHC), clinic, or warehouse.
5. **SELF**: Restricted to records where `patient_id == current_user.id` or `created_by == current_user.id`.

---

### 2. Standardized Role Definitions (Approved Matrix)

| Role Code | Display Name | Domain | Default Scope Level | Description |
| :--- | :--- | :--- | :--- | :--- |
| `SUPER_ADMIN` | Super Administrator | Governance | GLOBAL | Platform root manager; requires step-up MFA for privileged changes. |
| `SYSTEM_ADMIN` | System Administrator | Governance | GLOBAL | Manages users, organizations, facilities, and dynamic system configurations. |
| `AUDITOR` | Compliance & Security Auditor | Governance | STATE / GLOBAL | Read-only access to audit logs, compliance reports, and system telemetry. |
| `PHC_ADMIN` | PHC Administrator | Healthcare | FACILITY | Manages day-to-day operations, staff assignments, and facility schedules. |
| `DOCTOR` | Medical Officer | Healthcare | FACILITY | Clinical consultations, diagnoses, prescription writing, lab test orders. |
| `NURSE` | Clinical Staff / Nurse | Healthcare | FACILITY | Patient intake, vital checks, triage, care notes, referral dispatch. |
| `PHARMACIST` | Pharmacist / Dispensary Manager | Pharmacy & Supply | FACILITY | Medicine dispensing, batch verification, FEFO management, local inventory. |
| `LAB_TECHNICIAN` | Laboratory Technician | Healthcare | FACILITY | Lab sample intake, test execution, lab result entry and validation. |
| `PATIENT` | Citizen / Patient | Healthcare | SELF | Views personal health records, prescriptions, test results, appointments. |
| `INVENTORY_OFFICER` | Facility Storekeeper | Supply Chain | FACILITY | Manages stock receipts, physical counts, stock movements, and issue slips. |
| `DISTRICT_SUPPLY_OFFICER` | District Supply Chain Officer | Supply Chain | DISTRICT | Oversees district inventory, approves facility transfers, monitors shortages. |
| `STATE_SUPPLY_OFFICER` | State Supply Chain Director | Supply Chain | STATE | State-level allocation, emergency buffer stock management, bulk procurement. |
| `PROCUREMENT_OFFICER` | Procurement Officer | Supply Chain | DISTRICT / STATE | Issues purchase requests, solicits bids, drafts purchase orders. |
| `SUPPLIER` | Vendor / Supplier | Supply Chain | SELF / ORG | Reviews purchase orders, submits shipping manifests, manages item catalogs. |
| `LOGISTICS_COORDINATOR` | Logistics & Fleet Coordinator | Supply Chain | DISTRICT / STATE | Coordinates transport, assigns drivers, updates transit status & milestone events. |

---

### 3. Granular Permission Catalog

Permissions adhere strictly to the format: `<module>.<resource>.<action>`.

#### 3.1 Identity & Governance Module (`identity`, `admin`, `audit`)
- `identity.user.create` — Provision new user accounts
- `identity.user.read` — View user profiles and directory listings
- `identity.user.update` — Edit user demographic and contact details
- `identity.user.deactivate` — Suspend or deactivate user accounts
- `identity.role.assign` — Assign roles to users
- `identity.role.manage` — Create, edit, and toggle roles and permissions
- `identity.facility.manage` — Create and configure PHCs, warehouses, and health posts
- `audit.log.read` — View immutable audit logs
- `system.config.manage` — Update dynamic thresholds, feature flags, and policies

#### 3.2 Healthcare Module (`patients`, `clinical`, `labs`)
- `patients.profile.create` — Register new patients
- `patients.profile.read` — View patient registration and demographic data
- `patients.profile.update` — Update patient records
- `patients.records.read` — Access clinical history, consultation notes, and diagnoses
- `patients.vitals.record` — Record triage vitals (blood pressure, temperature, SpO2)
- `appointments.manage` — Schedule, reschedule, or cancel patient appointments
- `appointments.view` — View clinic schedules and appointment rosters
- `consultations.conduct` — Start, conduct, and finalize doctor consultations
- `prescriptions.create` — Prescribe medications, dosage, and durations
- `prescriptions.read` — View prescription details
- `prescriptions.dispense` — Mark prescriptions as dispensed and verify batch codes
- `labs.order.create` — Order diagnostic laboratory tests
- `labs.order.read` — View pending and completed lab orders
- `labs.result.record` — Enter diagnostic test findings and attach reports
- `labs.result.verify` — Formally approve and release lab test results

#### 3.3 Inventory & Warehouse Module (`inventory`, `warehouse`)
- `inventory.item.read` — View stock levels and batch details
- `inventory.item.create` — Register new stock items or batch lots
- `inventory.stock.adjust` — Perform physical count reconciliations and shrinkage write-offs
- `inventory.movement.record` — Record stock receipts, internal issues, and disposals
- `inventory.transfer.request` — Initiate inter-facility stock transfer requests
- `inventory.transfer.approve` — Approve pending stock transfer requests
- `inventory.transfer.dispatch` — Dispatch stock transfer shipments
- `inventory.transfer.receive` — Acknowledge and accept incoming stock transfers
- `warehouse.manage` — Configure warehouse zones, bins, and storage capacities

#### 3.4 Procurement & Supply Chain Resilience Module (`procurement`, `logistics`, `shortages`)
- `procurement.request.create` — Raise purchase requisitions for medicines or equipment
- `procurement.request.approve` — Authorize purchase requisitions
- `procurement.order.create` — Create purchase orders to suppliers
- `procurement.order.approve` — Final approval of purchase orders (segregation of duties enforced)
- `procurement.order.read` — View purchase orders and status
- `suppliers.manage` — Onboard, rate, and manage supplier profiles
- `shipments.create` — Generate shipping manifests and consignments
- `shipments.update` — Log tracking milestones (IN_TRANSIT, DELAYED, DELIVERED)
- `shipments.read` — Track shipments and view bills of lading
- `shortages.incident.report` — Log stockout or critical shortage incidents
- `shortages.incident.escalate` — Escalate shortages to district/state emergency pool
- `shortages.incident.resolve` — Mark shortage incidents resolved with fulfillment links

#### 3.5 Intelligence & Analytics Module (`ai`, `dashboards`)
- `dashboards.clinical.view` — View clinical metrics (patient volumes, disease patterns)
- `dashboards.supply.view` — View supply chain metrics (stock levels, burn rates, stockout risks)
- `ai.forecast.view` — View consumption forecasts and replenishment recommendations
- `ai.risk.analyze` — Run proactive stockout and supply chain disruption risk models
- `alerts.read` — View operational alerts
- `alerts.acknowledge` — Acknowledge and assign alerts

---

### 4. Role × Permission Mapping Matrix (Baseline Configuration)

| Module / Resource | Action | Super Admin | System Admin | Doctor | Nurse | Pharmacist | Lab Tech | Inv. Officer | District Supply | State Supply | Patient |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `identity.user` | `create / update` |  |  |  |  |  |  |  |  |  |  |
| `identity.role` | `assign / manage` |  |  |  |  |  |  |  |  |  |  |
| `patients.profile` | `create / update` |  |  |  |  |  |  |  |  |  |  |
| `patients.profile` | `read` |  |  |  |  |  |  |  |  |  |  (Self) |
| `patients.vitals` | `record` |  |  |  |  |  |  |  |  |  |  |
| `consultations` | `conduct` |  |  |  |  |  |  |  |  |  |  |
| `prescriptions` | `create` |  |  |  |  |  |  |  |  |  |  |
| `prescriptions` | `dispense` |  |  |  |  |  |  |  |  |  |  |
| `labs.order` | `create` |  |  |  |  |  |  |  |  |  |  |
| `labs.result` | `record / verify` |  |  |  |  |  |  |  |  |  |  |
| `inventory.item` | `read` |  |  |  |  |  |  |  |  |  |  |
| `inventory.stock` | `adjust` |  |  |  |  |  |  |  |  |  |  |
| `inventory.transfer` | `request` |  |  |  |  |  |  |  |  |  |  |
| `inventory.transfer` | `approve` |  |  |  |  |  |  |  |  |  |  |
| `procurement.order` | `create` |  |  |  |  |  |  |  |  |  |  |
| `procurement.order` | `approve` |  |  |  |  |  |  |  |  |  |  |
| `shortages.incident` | `report / escalate`|  |  |  |  |  |  |  |  |  |  |
| `audit.log` | `read` |  |  |  |  |  |  |  |  |  |  |

*(Legend:  = Granted by default; Empty = Forbidden)*

---

### 5. Runtime Enforcement Engine

All authorization queries pass through the central `AuthorizationService`:

```python
async def check_permission(
    user_id: UUID,
    required_permission: str,
    target_facility_id: UUID | None = None,
    target_organization_id: UUID | None = None,
) -> bool:
    """
    1. Fetches user's active UserRoles joined with RolePermissions and Permissions.
    2. Validates permission.code == required_permission and is_active is True.
    3. Evaluates scope hierarchy (GLOBAL > STATE > DISTRICT > FACILITY > SELF).
    4. If target_facility_id is supplied, verifies user's facility assignment matches.
    """
```
