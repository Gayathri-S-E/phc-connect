# CROSS_ROLE_WORKFLOW_MATRIX.md — Real-World Cross-Role Workflow Connection Matrix
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

This matrix documents the end-to-end connections between all 13 canonical roles across clinical, diagnostic, pharmacy, inventory, logistics, governance, emergency, and platform operations.

---

### 🌐 Cross-Role Workflow Connection Matrix

| Source Role | Action | Backend Entity | Target Role | Target Queue/Page | Status Change | Return Flow | Working? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Patient** (`Role 01`) | Book appointment | `Appointment` | **Doctor** (`Role 02`) / **Nurse** (`Role 03`) | OPD Consultation Queue (`/clinical/queue`, `/doctor/queue`) | `SCHEDULED` | Doctor → Patient (`PatientNotification`, status update) | **YES (PASS)** |
| **Patient** (`Role 01`) | Check-in at PHC | `Appointment` | **Nurse** (`Role 03`) | Triage Worklist (`/clinical/triage`) | `CHECKED_IN` | Nurse → Doctor (Priority queue float) | **YES (PASS)** |
| **Nurse** (`Role 03`) | Record triage & vitals | `PatientVitals`, `Appointment` | **Doctor** (`Role 02`) | OPD Consultation Queue (`/clinical/queue`) | Early warning priority (`EMERGENCY` / `PRIORITY` / `ROUTINE`) | Doctor → Patient (Encounter notes) | **YES (PASS)** |
| **Doctor** (`Role 02`) | Order diagnostic lab panel | `LabOrder`, `LabOrderItem` | **Lab Technician** / **Facility Admin** (`Role 04`) | Diagnostic Lab Worklist (`/clinical/labs`, `/lab/worklist`) | `ORDERED` | Lab → Doctor & Patient (Verified results) | **YES (PASS)** |
| **Lab Technician** | Verify & release lab results | `LabOrder`, `LabResult` | **Doctor** (`Role 02`) & **Patient** (`Role 01`) | Doctor Encounter Review & Patient Health Records | `COMPLETED` | Patient in-app notification & clinical record timeline | **YES (PASS)** |
| **Doctor** (`Role 02`) | Issue electronic prescription | `Prescription`, `PrescriptionItem` | **Pharmacist** (`Role 05`) | FEFO Dispense Queue (`/pharmacy/dispense`) | `ISSUED` | Pharmacy → Patient (Fulfilled medication alert) | **YES (PASS)** |
| **Pharmacist** (`Role 05`) | Dispense prescription via FEFO | `Prescription`, `InventoryBatch`, `StockMovement` | **Patient** (`Role 01`) | Patient Prescription Fulfillment View (`/patient/records`) | `COMPLETED` / `PARTIALLY_DISPENSED` | Stock ledger deducted; patient receives dispensing notification | **YES (PASS)** |
| **Pharmacist** (`Role 05`) / **Facility Admin** (`Role 04`) | Raise medicine supply request / indent | `SupplyRequest`, `SupplyRequestItem` | **District Supply Officer** (`Role 07`) | District Supply Requests Queue (`/supply/requests`) | `PENDING_DISTRICT_REVIEW` | District → Facility (Approval & transfer dispatch) | **YES (PASS)** |
| **District Supply Officer** (`Role 07`) | Approve & allocate stock transfer | `SupplyRequest`, `StockTransfer` | **Pharmacist** (`Role 05`) / **Facility Admin** | Inbound Stock Receipts (`/pharmacy/receipts`) | `APPROVED` → `DISPATCHED` | Facility receives & verifies batch quantities into stock | **YES (PASS)** |
| **District Supply Officer** (`Role 07`) | Escalate shortage to state warehouse | `SupplyRequest` | **State Supply Manager** (`Role 10`) | State Supply Dashboard & Escalations (`/supply`) | `PENDING_STATE_REVIEW` | State → District (Central allocation) | **YES (PASS)** |
| **District Emergency Coordinator** (`Role 08`) | Declare emergency & assign task | `EmergencyIncident`, `EmergencyTask` | **Facility In-Charge** (`Role 04`) / **Staff** | Emergency Response Workspace (`/emergency`) | `ACTIVE` incident, task `ASSIGNED` → `IN_PROGRESS` | Staff completes task → Incident coordinator tracks | **YES (PASS)** |
| **District Emergency Coordinator** (`Role 08`) | Emergency resource requisition | `EmergencyResourceRequest` | **District Supply Officer** (`Role 07`) | District Supply Indents & Resource Allocation | `REQUESTED` → `ALLOCATED` | District supply dispatches emergency stock | **YES (PASS)** |
| **District Health Officer** (`Role 06`) | Issue operational directive / action item | `GovernanceAction` | **Facility In-Charge** (`Role 04`) | Facility Governance & Action Items (`/facility`) | `OPEN` | Facility submits evidence → DHO resolves (`RESOLVED`) | **YES (PASS)** |
| **State Health Admin** (`Role 09`) | Cross-district oversight & scheme allocation | `GovernanceScheme`, `GovernanceApproval` | **District Health Officer** (`Role 06`) | District Governance Oversight Portal (`/district`) | `APPROVED` | District receives program funding & targets | **YES (PASS)** |
| **State Public Health Analyst** (`Role 11`) | Disease surveillance & outbreak detection | `AIAnalysisJob`, `OutbreakAlert` | **State Health Admin** (`Role 09`) & **National Authority** (`Role 12`) | Epidemiological Analytics Dashboard (`/analytics`) | Analytical alert flagged | High-level authorities review trends & issue advisories | **YES (PASS)** |
| **National Health Authority** (`Role 12`) | National resilience benchmark review | `GovernanceMetricAggregate` | **State Health Admin** (`Role 09`) | National Executive Dashboard (`/national`) | Strategic guideline issued | State aligns district health indicators | **YES (PASS)** |
| **Super Admin** (`Role 13`) | RBAC management, audit log inspection | `AuditLog`, `Role`, `UserPermission` | **All Roles** (`Roles 01-12`) | Platform Administration Portal (`/platform`) | Security policy enforced | Immutable audit ledger guarantees compliance | **YES (PASS)** |

---

### 🔒 RBAC & Scope Authorization Invariants
- **Multi-Tenancy Boundaries**: `SELF`, `FACILITY`, `DISTRICT`, `STATE`, and `GLOBAL` scopes strictly enforced at the database query layer.
- **IDOR Defense**: All patient records and notifications enforce ownership verification against `user_id`.
- **Zero Hardcoding**: Role permissions dynamically resolved through database-backed RBAC policies.
