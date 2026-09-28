# API.md — RESTful API Specification & Inventory
## Smart Health & Supply Chain Resilience Platform

> **Base URL:** `/api/v1`  
> **Documentation URL:** `/docs` (Swagger UI) and `/redoc` (ReDoc)  
> **Security Protocol:** Bearer JWT in `Authorization` header (`Bearer <access_token>`)  
> **Standard Envelope:**
> - Singular Resource: `{ "data": { ... } }`
> - Collections: `{ "data": [ ... ], "pagination": { "page": 1, "page_size": 20, "total": 100, "total_pages": 5 } }`
> - Errors: RFC 7807 Problem Details `{ "type": "...", "title": "...", "status": 400, "detail": "..." }`

---

### 1. Authentication & Session APIs (`/api/v1/auth`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register citizen/patient account |
| `POST` | `/api/v1/auth/login` | Public | Authenticate with email/password; returns JWT pair |
| `POST` | `/api/v1/auth/refresh` | Public (Refresh Token) | Rotate refresh token and issue new access token |
| `POST` | `/api/v1/auth/logout` | Authenticated | Revoke refresh token and invalidate active session |
| `GET` | `/api/v1/auth/me` | Authenticated | Retrieve profile, active scopes, and granted permissions |
| `POST` | `/api/v1/auth/change-password` | Authenticated | Update user password with current password verification |

---

### 2. User & RBAC Management APIs (`/api/v1/users`, `/roles`, `/permissions`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | `identity.user.read` | List paginated users (filtered by facility/organization) |
| `POST` | `/api/v1/users` | `identity.user.create` | Provision new healthcare or supply-chain staff member |
| `GET` | `/api/v1/users/{id}` | `identity.user.read` | Retrieve user details and role assignments |
| `PATCH` | `/api/v1/users/{id}` | `identity.user.update` | Update staff profile, contact info, or assigned facility |
| `POST` | `/api/v1/users/{id}/roles` | `identity.role.assign` | Assign scoped role (FACILITY / DISTRICT / STATE) to user |
| `DELETE` | `/api/v1/users/{id}/roles/{role_id}`| `identity.role.assign` | Revoke a role from a user |
| `GET` | `/api/v1/roles` | `identity.role.manage` | List all dynamic roles and their active status |
| `POST` | `/api/v1/roles` | `identity.role.manage` | Create a new customizable role |
| `PATCH` | `/api/v1/roles/{id}` | `identity.role.manage` | Update role name or active status |
| `POST` | `/api/v1/roles/{id}/permissions` | `identity.role.manage` | Assign atomic permissions to a role |
| `GET` | `/api/v1/permissions` | `identity.role.manage` | List all system permission codes |

---

### 3. Facilities & Organization APIs (`/api/v1/facilities`, `/organizations`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/facilities` | Authenticated | List health centers (PHC, CHC, Warehouses) |
| `POST` | `/api/v1/facilities` | `identity.facility.manage` | Provision a new PHC, clinic, or distribution center |
| `GET` | `/api/v1/facilities/{id}` | Authenticated | Get detailed facility profile, coordinates, and contact |
| `PATCH` | `/api/v1/facilities/{id}` | `identity.facility.manage` | Update facility operational metadata |

---

### 4. Healthcare Core APIs (`/api/v1/patients`, `/appointments`, `/consultations`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/patients` | `patients.profile.create` | Register a new patient at a PHC |
| `GET` | `/api/v1/patients` | `patients.profile.read` | Search patients by identifier, phone, or name |
| `GET` | `/api/v1/patients/{id}` | `patients.profile.read` | View patient demographic record (or Self) |
| `GET` | `/api/v1/patients/{id}/clinical-history` | `patients.records.read` | Comprehensive medical history (vitals, diagnoses, consults) |
| `POST` | `/api/v1/appointments` | `appointments.manage` | Schedule a consultation appointment |
| `GET` | `/api/v1/appointments` | `appointments.view` | List appointments filtered by facility, doctor, or status |
| `PATCH` | `/api/v1/appointments/{id}/status` | `appointments.manage` | Update appointment status (CHECKED_IN, CANCELLED) |
| `POST` | `/api/v1/consultations` | `consultations.conduct` | Initiate clinical consultation with vitals & notes |
| `PATCH` | `/api/v1/consultations/{id}/finalize` | `consultations.conduct` | Conclude consultation, finalize diagnosis & notes |

---

### 5. Prescriptions & Laboratory APIs (`/api/v1/prescriptions`, `/labs`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/prescriptions` | `prescriptions.create` | Create prescription with line items linked to consultation |
| `GET` | `/api/v1/prescriptions` | `prescriptions.read` | Search prescriptions by patient, doctor, or facility |
| `GET` | `/api/v1/prescriptions/{id}` | `prescriptions.read` | Get prescription detail and dispensing status |
| `POST` | `/api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense`| Dispense prescribed items, deducting batch inventory |
| `POST` | `/api/v1/labs/orders` | `labs.order.create` | Order diagnostic lab panel for a patient |
| `GET` | `/api/v1/labs/orders` | `labs.order.read` | List lab orders pending collection or testing |
| `POST` | `/api/v1/labs/orders/{id}/results` | `labs.result.record` | Enter test values, reference ranges, and flag abnormals |
| `POST` | `/api/v1/labs/orders/{id}/verify` | `labs.result.verify` | Clinical sign-off and verification of lab results |

---

### 6. Medications & Inventory Management APIs (`/api/v1/medications`, `/inventory`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/medications` | Authenticated | Browse medication formulary, categories, and cold-chain rules |
| `POST` | `/api/v1/medications` | `inventory.item.create` | Add new medication formulation to national formulary |
| `GET` | `/api/v1/inventory` | `inventory.item.read` | Query current stock levels per facility with low-stock alerts |
| `POST` | `/api/v1/inventory/batches` | `inventory.item.create` | Register received batch lot with manufacture & expiry dates |
| `GET` | `/api/v1/inventory/batches/expiring` | `inventory.item.read` | Query batches nearing expiry (dynamic FEFO threshold) |
| `POST` | `/api/v1/inventory/movements` | `inventory.movement.record`| Record auditable stock movement (RECEIPT, ISSUE, LOSS) |
| `POST` | `/api/v1/inventory/adjustments` | `inventory.stock.adjust`| Physical count reconciliation / stock write-off |

---

### 7. Inter-Facility Stock Transfers (`/api/v1/inventory/transfers`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/inventory/transfers` | `inventory.transfer.request`| Initiate replenishment transfer request between facilities |
| `GET` | `/api/v1/inventory/transfers` | `inventory.item.read` | List incoming and outgoing transfer requests |
| `POST` | `/api/v1/inventory/transfers/{id}/approve` | `inventory.transfer.approve`| Authorize transfer at district / warehouse level |
| `POST` | `/api/v1/inventory/transfers/{id}/dispatch` | `inventory.transfer.dispatch`| Deduct source stock and dispatch transit consignment |
| `POST` | `/api/v1/inventory/transfers/{id}/receive` | `inventory.transfer.receive`| Acknowledge delivery and credit destination facility stock |

---

### 8. Procurement & Suppliers (`/api/v1/procurement`, `/suppliers`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/suppliers` | `suppliers.manage` | List registered pharmaceutical suppliers and vendor ratings |
| `POST` | `/api/v1/suppliers` | `suppliers.manage` | Onboard new approved medicine or logistics vendor |
| `POST` | `/api/v1/procurement/requests` | `procurement.request.create`| Raise purchase requisition for clinic / warehouse |
| `POST` | `/api/v1/procurement/orders` | `procurement.order.create` | Issue purchase order (PO) to supplier |
| `GET` | `/api/v1/procurement/orders` | `procurement.order.read` | Track purchase orders and delivery timelines |
| `POST` | `/api/v1/procurement/orders/{id}/approve`| `procurement.order.approve`| Executive sign-off on purchase order (SoD enforced) |

---

### 9. Logistics, Shipments & Shortages (`/api/v1/shipments`, `/shortages`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/shipments` | `shipments.create` | Generate shipment consignment for transfer or PO |
| `GET` | `/api/v1/shipments` | `shipments.read` | Track in-transit consignments with carrier details |
| `POST` | `/api/v1/shipments/{id}/events` | `shipments.update` | Log milestone checkpoint or cold-chain temperature reading |
| `POST` | `/api/v1/shortages` | `shortages.incident.report` | Report stockout or critical stock depletion at a PHC |
| `GET` | `/api/v1/shortages` | `inventory.item.read` | View active shortage incidents by district and severity |
| `POST` | `/api/v1/shortages/{id}/escalate` | `shortages.incident.escalate`| Escalate shortage to district or state buffer reserve |
| `POST` | `/api/v1/shortages/{id}/resolve` | `shortages.incident.resolve` | Link fulfillment transfer and close shortage incident |

---

### 10. Intelligence, Alerts & Dashboards (`/api/v1/ai`, `/alerts`, `/dashboards`)

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/alerts` | `alerts.read` | List active alerts (stockout risk, cold-chain breach) |
| `POST` | `/api/v1/alerts/{id}/ack` | `alerts.acknowledge` | Acknowledge alert and log resolution action |
| `POST` | `/api/v1/ai/forecast` | `ai.forecast.view` | Generate 30/60/90-day medicine consumption forecast |
| `POST` | `/api/v1/ai/risk-analysis` | `ai.risk.analyze` | Compute facility vulnerability and stockout risk score |
| `GET` | `/api/v1/dashboards/phc` | `dashboards.clinical.view` | PHC operational summary (patient volume, stock warnings) |
| `GET` | `/api/v1/dashboards/supply-chain` | `dashboards.supply.view` | District/State supply pipeline (stock on hand, shortages) |

---

### 11. System Health & Observability

| Method | Endpoint | Required Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Liveness probe (HTTP 200) |
| `GET` | `/health/ready` | Public | Readiness probe (verifies PostgreSQL async connection) |
| `GET` | `/api/v1/audit-logs` | `audit.log.read` | View immutable audit trail with actor, action, and changes |
