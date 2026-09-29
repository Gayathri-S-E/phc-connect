# CROSS_ROLE_CONNECTION_MATRIX.md — End-to-End Cross-Role Connection Matrix
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Architectural Standard:** Every user action that creates work, responsibility, clinical information, or supply allocation for a downstream role must deterministically update the backend state, deliver targeted notifications, and present actionable work items in the target role's queue.

---

### 🌐 Cross-Role Connection Matrix (All 13 Canonical Roles)

| # | Source Role | Action | Target Role | Target Work Item | Notification Delivered | Target Action | Result Returned | Status |
|---|:---|:---|:---|:---|:---|:---|:---|:---|
| **1** | **PATIENT** (`Role 01`) | Books consultation slot | **DOCTOR** (`Role 02`) / **NURSE** (`Role 03`) | Sequential OPD Queue (`/doctor/queue`) | Patient In-App Confirmation (`APPOINTMENT`) | Nurse Triage / Doctor Starts Consultation | Allocated Token # (e.g. `#501`), `SCHEDULED` status | **CONNECTED** |
| **2** | **NURSE** (`Role 03`) | Records triage vitals & early warning score | **DOCTOR** (`Role 02`) | Priority OPD Queue (`/doctor/queue`) | Triage Priority Badge (`EMERGENCY` / `PRIORITY` / `ROUTINE`) | Doctor opens encounter with pre-populated vitals | `CHECKED_IN` status, latest vitals attached | **CONNECTED** |
| **3** | **DOCTOR** (`Role 02`) | Starts clinical encounter & diagnoses ICD-10 | **PATIENT** (`Role 01`) | Patient Health Records Timeline (`/patients/me/records`) | In-App Status Update (`IN_CONSULTATION`) | Patient views encounter progress | `IN_CONSULTATION` status | **CONNECTED** |
| **4** | **DOCTOR** (`Role 02`) | Orders diagnostic lab test (CBC, Dengue, etc.) | **LAB TECHNICIAN** (`Role 05`) | Diagnostic Lab Worklist (`/lab/worklist`) | Worklist Order Entry (`ORDERED`) | Sample Accessioning & Result Entry | `ORDERED` / `SAMPLE_COLLECTED` status | **CONNECTED** |
| **5** | **LAB TECHNICIAN** (`Role 05`) | Enters panel results & Pathologist verifies | **DOCTOR** (`Role 02`) & **PATIENT** (`Role 01`) | Doctor Encounter View & Patient Lab Portal | Patient In-App Alert (`LAB_RESULT`) | Doctor reviews lab findings; Patient views report | `COMPLETED` lab order status | **CONNECTED** |
| **6** | **DOCTOR** (`Role 02`) | Authors electronic prescription | **PHARMACIST** (`Role 04`) | Pharmacist FEFO Dispense Queue (`/pharmacist/prescriptions/pending`) | Pending Dispense Item | Pharmacist verifies FEFO batch allocation | `ISSUED` / `PENDING_DISPENSING` status | **CONNECTED** |
| **7** | **PHARMACIST** (`Role 04`) | Dispenses medications via FEFO allocation | **PATIENT** (`Role 01`) | Patient Prescription Fulfillment View | Patient In-App Alert (`PRESCRIPTION`) | Patient views completed medication details | `COMPLETED` / `PARTIALLY_DISPENSED` status | **CONNECTED** |
| **8** | **PHARMACIST** (`Role 04`) | Raises medicine indent / supply request | **DISTRICT SUPPLY OFFICER** (`Role 07`) | District Supply Requests Queue (`/supply-requests`) | District Supply Alert | Officer reviews stock availability and approves/allocates | `PENDING_DISTRICT_REVIEW` status | **CONNECTED** |
| **9** | **DISTRICT SUPPLY OFFICER** (`Role 07`) | Approves supply request & allocates stock | **PHARMACIST** (`Role 04`) | Inbound Stock Transfer Queue (`/pharmacy/transfers`) | Transfer Dispatch Notice | Pharmacist inspects & completes receipt verification | `APPROVED` -> `DISPATCHED` -> `RECEIVED` status | **CONNECTED** |
| **10** | **DISTRICT SUPPLY OFFICER** (`Role 07`) | Escalates shortage to state warehouse | **STATE SUPPLY MANAGER** (`Role 10`) | State Supply Dashboard & Escalation Queue | State Shortage Escalation Alert | State Manager allocates from central stock | `ESCALATED_TO_STATE` status | **CONNECTED** |
| **11** | **DISTRICT EMERGENCY COORDINATOR** (`Role 08`) | Declares emergency incident & tasks role | **FACILITY IN-CHARGE** (`Role 04`) / **STAFF** | Emergency Incident Tasking (`/emergencies/{id}`) | Incident Directive Alert | Staff executes task and updates progress | `ACTIVE` incident, task `IN_PROGRESS` | **CONNECTED** |
| **12** | **DISTRICT HEALTH OFFICER** (`Role 06`) | Issues operational directive / action item | **FACILITY IN-CHARGE** (`Role 04`) | Governance Action Items (`/governance/actions`) | Action Item Notice | Facility In-Charge responds with resolution evidence | `OPEN` -> `RESOLVED` status | **CONNECTED** |
| **13** | **STATE PUBLIC HEALTH ANALYST** (`Role 11`) | Runs disease surveillance & trend analysis | **STATE HEALTH ADMIN** (`Role 09`) & **NATIONAL AUTHORITY** (`Role 12`) | Governance Insights & Disease Surveillance Portal | Strategic Epidemiological Notice | Authorities review outbreak trends and allocate resources | Verified outbreak analytics & alert flags | **CONNECTED** |
| **14** | **SUPER ADMIN** (`Role 13`) | Manages dynamic RBAC, roles & security | **ALL ROLES** (`Roles 01-12`) | System Audit Logs & Platform Governance | Security & Session Log | Platform monitoring & role enforcement | Audit-verified system changes | **CONNECTED** |

---

### 🔒 Security, RBAC & Scope Invariants Preserved
- **Multi-Tenancy Scoping**: `SELF`, `FACILITY`, `DISTRICT`, `STATE`, and `GLOBAL` authorization boundaries strictly enforced.
- **IDOR Defense**: All patient endpoints validate caller identity against `patient.user_id`.
- **Zero Hardcoding**: 100% database-driven role permission lookups and dynamic RBAC evaluators.
