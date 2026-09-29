# ROLE_FEATURE_MATRIX.md — Master 13-Role Feature & Permission Matrix
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Authority & Segregation of Duties:**
> Every capability across the platform is mapped to exactly one of three classifications:
> - **MUST HAVE:** Core workflow feature required for the role to complete daily operational responsibilities.
> - **SHOULD HAVE:** Supplementary feature enhancing usability, insights, or reporting.
> - **MUST NOT HAVE:** Explicitly forbidden capability. Access is strictly blocked at the backend API layer and concealed in the UI.

---

## 1. Master Feature Classification Table

| Role Code | Feature Name | Purpose | Action Type | Endpoint | Permission Code | Scope | Priority |
|:---|:---|:---|:---|:---|:---|:---|:---:|
| **PATIENT** | Profile Management | Manage personal demographic and emergency details | View / Update | `GET /api/v1/patient-portal/profile`<br>`PATCH /api/v1/patient-portal/profile` | `patients.profile.read`<br>`patients.profile.update` | SELF | **MUST HAVE** |
| **PATIENT** | Appointment Booking | Search clinic availability and book OPD token slot | Create / View | `POST /api/v1/patient-portal/appointments/book`<br>`GET /api/v1/patient-portal/appointments` | `patients.awareness.read`<br>`appointments.view` | SELF | **MUST HAVE** |
| **PATIENT** | Clinical Records View | Access verified diagnoses, vitals, and physician notes | View | `GET /api/v1/patient-portal/clinical-records` | `patients.records.read` | SELF | **MUST HAVE** |
| **PATIENT** | Prescriptions History | Track prescribed medications and fulfillment state | View | `GET /api/v1/patient-portal/prescriptions` | `prescriptions.read` | SELF | **MUST HAVE** |
| **PATIENT** | Grievance & Feedback | Submit rating and grievances regarding PHC care | Create / View | `POST /api/v1/patient-portal/feedback` | `patients.feedback.submit` | SELF | **MUST HAVE** |
| **PATIENT** | AI Wellness Assistant | Conversational lifestyle and health advice (EN/TA) | View / Chat | `POST /api/v1/patient-portal/wellness-assistant/chat` | `patients.ai.wellness.chat` | SELF | **SHOULD HAVE** |
| **PATIENT** | Health Awareness Bulletins | Preventive community health advisories | View | `GET /api/v1/patient-portal/awareness` | `patients.awareness.read` | SELF | **SHOULD HAVE** |
| **PATIENT** | Write Clinical Diagnoses | Author medical diagnoses or modify clinician charts | Create / Update | `POST /api/v1/consultations` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **PATIENT** | Dispense Medications | Dispense medicines from facility inventory | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **PATIENT** | Access Other Patient Records | View records of other citizens (IDOR) | View | `GET /api/v1/patients/{id}` | `patients.records.read` | SELF | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **DOCTOR** | Outpatient Daily Queue | Manage queued patients and token arrivals | View | `GET /api/v1/doctor-portal/queue` | `appointments.view` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Patient Clinical History | Review past consultations, allergies, and vitals | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Consultation & Diagnosis | Record examination findings, assign ICD-10 codes | Create / Update | `POST /api/v1/consultations`<br>`PATCH /api/v1/consultations/{id}/finalize` | `consultations.conduct` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Electronic Prescription | Author medication prescription with dosages | Create | `POST /api/v1/prescriptions` | `prescriptions.create` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Diagnostic Lab Order | Order laboratory panels with indications | Create | `POST /api/v1/labs/orders` | `labs.order.create` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Specialty Referral | Refer patient to Community Health Centre / District Hospital | Create / Update | `POST /api/v1/doctor-portal/referrals` | `referrals.create` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Daily Duty Attendance | Record shift check-in and check-out timestamps | Create / View | `POST /api/v1/doctor-portal/attendance/check-in`<br>`POST /api/v1/doctor-portal/attendance/check-out` | `staff.attendance.record` | FACILITY | **MUST HAVE** |
| **DOCTOR** | Clinical AI Advisory | Consult AI for drug contraindications and guidelines | Query | `POST /api/v1/doctor-portal/clinical-assistant/advise` | `clinical.ai.advisory` | FACILITY | **SHOULD HAVE** |
| **DOCTOR** | Emergency Incident Report | Report disease outbreak or mass casualty directly to DEC | Create | `POST /api/v1/doctor-portal/emergency-reports` | `emergency.incident.report` | FACILITY | **SHOULD HAVE** |
| **DOCTOR** | Dispense Medicines | Physically dispense pharmaceutical stock | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **DOCTOR** | Adjust Inventory Counts | Reconcile or write off warehouse stock | Update | `POST /api/v1/inventory/adjustments` | `inventory.stock.adjust` | — | **MUST NOT HAVE** |
| **DOCTOR** | User & RBAC Management | Provision accounts or modify system roles | Manage | `POST /api/v1/users` | `identity.user.create` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **NURSE** | Patient Registration & Intake | Register walk-in citizens or retrieve profiles | Create / View | `POST /api/v1/patients`<br>`GET /api/v1/patients` | `patients.profile.create`<br>`patients.profile.read` | FACILITY | **MUST HAVE** |
| **NURSE** | Triage Vitals Recording | Capture BP, Pulse, Temp, SpO2, Resp, Blood Sugar | Create | `POST /api/v1/nurse-portal/vitals` | `patients.vitals.record` | FACILITY | **MUST HAVE** |
| **NURSE** | Early Warning Score (EWS) | Automated clinical triage severity calculation | Compute / View | `POST /api/v1/nurse-portal/triage-assistant/score` | `clinical.ai.advisory` | FACILITY | **MUST HAVE** |
| **NURSE** | Lab Sample Collection | Collect specimen (blood, urine, sputum) & log status | Update | `POST /api/v1/nurse-portal/samples/{id}/collect` | `labs.sample.collect` | FACILITY | **MUST HAVE** |
| **NURSE** | Cold Chain Temperature Log | Record morning/evening ILR vaccine temperatures | Create / View | `POST /api/v1/nurse-portal/cold-chain/log` | `cold_chain.log` | FACILITY | **MUST HAVE** |
| **NURSE** | Clinic Roster Management | Check in arriving appointments, update queue | Update | `PATCH /api/v1/appointments/{id}/status` | `appointments.manage` | FACILITY | **MUST HAVE** |
| **NURSE** | Nurse Shift Attendance | Record duty check-in and check-out | Create / View | `POST /api/v1/nurse-portal/attendance/check-in`<br>`POST /api/v1/nurse-portal/attendance/check-out` | `staff.attendance.record` | FACILITY | **MUST HAVE** |
| **NURSE** | Finalize Clinical Diagnosis | Conclude doctor consultation and set ICD-10 | Finalize | `PATCH /api/v1/consultations/{id}/finalize` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **NURSE** | Prescribe Medications | Create doctor prescription orders | Create | `POST /api/v1/prescriptions` | `prescriptions.create` | — | **MUST NOT HAVE** |
| **NURSE** | Approve Stock Transfers | Authorize inter-facility medicine transfers | Approve | `POST /api/v1/inventory/transfers/{id}/approve` | `inventory.transfer.approve` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **PHC_IN_CHARGE** | Facility Overview Dashboard | Real-time OPD volume, bed occupancy, doctor roster | View | `GET /api/v1/dashboards/phc` | `facility.report.view` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Staff Attendance Ledger | Inspect attendance matrix of all doctors and staff | View / Admin | `GET /api/v1/facility-admin/staff-attendance` | `staff.attendance.admin` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Cold Chain Assets | Register ILR/deep freezers, track excursions | Create / View | `GET /api/v1/facility-admin/cold-chain/equipment`<br>`POST /api/v1/facility-admin/cold-chain/equipment` | `cold_chain.manage` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Outreach Camp Operations | Schedule village health camps and field staff | Create / Update | `GET /api/v1/facility-admin/outreach-camps`<br>`POST /api/v1/facility-admin/outreach-camps` | `outreach.camp.manage` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Grievance Redressal | Triage, respond to, and resolve patient complaints | Update / Resolve | `GET /api/v1/facility-admin/complaints`<br>`PATCH /api/v1/facility-admin/complaints/{id}/status` | `facility.complaint.manage` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Facility Monthly HMIS Report | Generate aggregate facility operational report | View / Generate | `GET /api/v1/facility-admin/reports/monthly` | `facility.report.view` | FACILITY | **MUST HAVE** |
| **PHC_IN_CHARGE** | Emergency Incident Escalation| Log and escalate emergency incidents at facility | Create | `POST /api/v1/doctor-portal/emergency-reports` | `emergency.incident.report` | FACILITY | **SHOULD HAVE** |
| **PHC_IN_CHARGE** | Alter Other Doctor Records | Change clinical diagnoses authored by other staff | Update | `PATCH /api/v1/consultations/{id}/finalize` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **PHC_IN_CHARGE** | Dispense Controlled Stock | Directly dispense drugs from dispensary | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **PHC_IN_CHARGE** | Modify District Allocations | Change district-level replenishment decisions | Approve | `POST /api/v1/supply-requests/{id}/allocate` | `supply.allocation.manage` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **PHARMACIST** | Dispensing Queue | View verified prescriptions pending medicine release | View | `GET /api/v1/pharmacist-portal/queue` | `prescriptions.read` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | FEFO Stock Dispensing | Deduct earliest-expiring batch, record fulfillment | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Facility Stock on Hand | Query real-time medicine inventory and stock alerts | View | `GET /api/v1/inventory` | `inventory.item.read` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Batch Expiry Monitor | Track batches expiring within 30, 60, 90 days | View | `GET /api/v1/inventory/batches/expiring` | `inventory.item.read` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Replenishment Supply Request | Raise purchase requisitions to District Warehouse | Create / View | `POST /api/v1/supply-requests`<br>`GET /api/v1/supply-requests` | `supply.request.create`<br>`supply.request.read` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Consignment Receipt Verify | Inspect and accept incoming transfer shipments | Receive / Verify | `POST /api/v1/supply-requests/{id}/receipts/{transfer_id}/verify` | `supply.receipt.verify` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Physical Stock Adjustment | Reconcile physical counts and log breakage/losses | Update | `POST /api/v1/inventory/adjustments` | `inventory.stock.adjust` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Duty Attendance | Record daily shift check-in and check-out | Create / View | `POST /api/v1/pharmacist-portal/attendance/check-in` | `staff.attendance.record` | FACILITY | **MUST HAVE** |
| **PHARMACIST** | Alter Medical Prescriptions | Change prescribed medicines or patient dosages | Update | `POST /api/v1/prescriptions` | `prescriptions.create` | — | **MUST NOT HAVE** |
| **PHARMACIST** | Author Clinical Notes | Record patient diagnoses or clinical assessments | Create | `POST /api/v1/consultations` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **PHARMACIST** | Approve District Transfers | Authorize transfer requests from other facilities | Approve | `POST /api/v1/inventory/transfers/{id}/approve` | `inventory.transfer.approve` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **DISTRICT_HEALTH_OFFICER** | District Health Dashboard | Live aggregate patient volumes, referrals, and alerts | View | `GET /api/v1/district/dashboard` | `governance.district.view` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | PHC Comparative Analytics | Facility-by-facility service delivery benchmarks | View | `GET /api/v1/district/facilities/{facility_id}`<br>`GET /api/v1/district/analytics` | `governance.district.view` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Directives & Action Items | Issue binding administrative directives with due dates | Create / Update | `GET /api/v1/governance/actions`<br>`POST /api/v1/governance/actions` | `governance.action.create`<br>`governance.action.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Public Health Alert Oversight | Review, investigate, and acknowledge health alerts | Update / Resolve | `GET /api/v1/governance/alerts`<br>`POST /api/v1/governance/alerts/{id}/transition` | `governance.alert.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Health Mission Schemes | Monitor district performance on state/national schemes | View | `GET /api/v1/governance/schemes` | `governance.scheme.read` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Supply Impact Assessment | Review drug shortage clinical impact shared by DSCO | View | `GET /api/v1/supply-requests/health-impacts` | `supply.impact.read` | DISTRICT | **MUST HAVE** |
| **DISTRICT_HEALTH_OFFICER** | District AI Governance Assist| Grounded AI summary of district epidemiological data | Query | `POST /api/v1/governance/ai-assistant` | `governance.ai.assist` | DISTRICT | **SHOULD HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Access Identifiable Patients | View individual citizen medical records or charts | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | — | **MUST NOT HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Purchase Order Approvals | Financial and commercial vendor approvals | Approve | `POST /api/v1/procurement/orders/{id}/approve` | `procurement.order.approve` | — | **MUST NOT HAVE** |
| **DISTRICT_HEALTH_OFFICER** | Oversee Other Districts | View or issue directives to outside jurisdictions | Manage | `GET /api/v1/district/dashboard` | `governance.district.view` | DISTRICT | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **DISTRICT_SUPPLY_OFFICER** | Supply Requisition Review | Evaluate medicine requests from all district PHCs | View / Decide | `GET /api/v1/supply-requests`<br>`POST /api/v1/supply-requests/{id}/decision` | `supply.request.review` | DISTRICT | **MUST HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Redistribution & Allocation | Rebalance stock from surplus PHCs to stockout PHCs | Allocate | `POST /api/v1/supply-requests/{id}/allocate` | `supply.allocation.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Transfer Approval & Dispatch | Authorize inter-facility medicine transfers | Approve / Dispatch | `POST /api/v1/inventory/transfers/{id}/approve`<br>`POST /api/v1/inventory/transfers/{id}/dispatch` | `inventory.transfer.approve`<br>`inventory.transfer.dispatch` | DISTRICT | **MUST HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | State Shortage Escalation | Escalate unresolvable shortages to State Warehouse | Escalate | `POST /api/v1/supply-requests/{id}/escalate`<br>`POST /api/v1/shortages/{id}/escalate` | `shortages.incident.escalate` | DISTRICT | **MUST HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Share Clinical Health Impact | Notify DHO of critical medicine stockout consequences | Create | `POST /api/v1/supply-requests/{id}/health-impact` | `supply.impact.share` | DISTRICT | **MUST HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | AI Forecast & Disruption Risk | 30/60/90-day predictive demand curves & risk index | Compute / View | `POST /api/v1/ai/forecast`<br>`POST /api/v1/ai/risk-analysis` | `ai.forecast.view`<br>`ai.risk.analyze` | DISTRICT | **SHOULD HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Direct Patient Dispensing | Dispense medications directly to walk-in patients | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Clinical Chart Access | View patient clinical histories or diagnoses | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | — | **MUST NOT HAVE** |
| **DISTRICT_SUPPLY_OFFICER** | Issue State Purchase Orders | Issue commercial purchase orders to manufacturers | Create | `POST /api/v1/procurement/orders` | `procurement.order.create` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **DISTRICT_EMERGENCY_COORDINATOR** | Emergency Command Dashboard | Live situational awareness, active incidents & sites | View | `GET /api/v1/emergencies/dashboard` | `emergency.incident.read` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Incident Lifecycle Manager | Declare emergency, set priority, resolve incidents | Create / Update | `POST /api/v1/emergencies`<br>`PATCH /api/v1/emergencies/{id}/status` | `emergency.incident.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Affected Facilities Mapping | Link impacted PHCs, sub-centres, and relief camps | Update | `PUT /api/v1/emergencies/{id}/facilities` | `emergency.incident.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Emergency Task Board | Assign, prioritize, and track emergency response tasks | Create / Update | `POST /api/v1/emergencies/{id}/tasks`<br>`PATCH /api/v1/emergencies/{id}/tasks/{task_id}` | `emergency.incident.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Rapid Resource Mobilization | Request emergency trauma kits, antivenom, ambulances | Create / View | `POST /api/v1/emergencies/{id}/resources` | `emergency.incident.manage` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Incident Resolution | Author formal post-incident resolution closure | Resolve | `POST /api/v1/emergencies/{id}/resolve` | `emergency.incident.resolve` | DISTRICT | **MUST HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | State Emergency Escalation | Escalate multi-district disaster to State Cell | Escalate | `POST /api/v1/emergencies/{id}/escalate` | `emergency.incident.manage` | DISTRICT | **SHOULD HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Alter Routine Dispensary Stock| Direct adjustment of everyday pharmacy inventories | Update | `POST /api/v1/inventory/adjustments` | `inventory.stock.adjust` | — | **MUST NOT HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Conduct Clinical Consultations| Examine patients or author medical diagnoses | Create | `POST /api/v1/consultations` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **DISTRICT_EMERGENCY_COORDINATOR** | Manage Systems RBAC | Alter platform permissions or create system users | Manage | `POST /api/v1/users` | `identity.user.create` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **STATE_HEALTH_ADMIN** | State Health Overview | Statewide aggregates, disease trends, district ranks | View | `GET /api/v1/state/dashboard`<br>`GET /api/v1/state/analytics` | `governance.state.view` | STATE | **MUST HAVE** |
| **STATE_HEALTH_ADMIN** | Executive Approval Engine | Decide on cross-district reallocations and tenders | Decide | `GET /api/v1/governance/approvals`<br>`POST /api/v1/governance/approvals/{id}/decision` | `governance.approval.decide` | STATE | **MUST HAVE** |
| **STATE_HEALTH_ADMIN** | State Health Schemes Config | Define schemes, assign district targets and quotas | Create / Manage | `GET /api/v1/governance/schemes`<br>`POST /api/v1/governance/schemes` | `governance.scheme.manage` | STATE | **MUST HAVE** |
| **STATE_HEALTH_ADMIN** | Official Governance Reports | Review, annotate, and approve monthly state reports | Review / Sign-off | `GET /api/v1/governance/reports`<br>`POST /api/v1/governance/reports/{id}/review` | `governance.report.review` | STATE | **MUST HAVE** |
| **STATE_HEALTH_ADMIN** | State AI Governance Assistant | Macro-level state health and supply insights | Query | `POST /api/v1/governance/ai-assistant` | `governance.ai.assist` | STATE | **SHOULD HAVE** |
| **STATE_HEALTH_ADMIN** | View Identifiable Patients | Access raw patient medical files or names | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | — | **MUST NOT HAVE** |
| **STATE_HEALTH_ADMIN** | Direct Physical Dispensing | Physically dispense medicines | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **STATE_HEALTH_ADMIN** | System Architecture Config | Configure technical server parameters or DB | Manage | `POST /api/v1/roles` | `identity.role.manage` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **STATE_SUPPLY_MANAGER** | State Central Warehouse Stock | Central pharmaceutical stockpiles & buffer margins | View | `GET /api/v1/supply-requests/state/dashboard`<br>`GET /api/v1/supply-requests/state/overview` | `inventory.item.read`<br>`dashboards.supply.view` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | District Request Allocation | Authorize bulk replenishment to district depots | Allocate | `POST /api/v1/supply-requests/{id}/allocate` | `supply.allocation.manage` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | Commercial Procurement Orders | Issue bulk Purchase Orders (PO) to pharma vendors | Create / View | `GET /api/v1/procurement/orders`<br>`POST /api/v1/procurement/orders` | `procurement.order.create`<br>`procurement.order.read` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | Supplier Directory & Ratings | Onboard manufacturers, rate quality and delivery | Create / View | `GET /api/v1/suppliers`<br>`POST /api/v1/suppliers` | `suppliers.manage` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | Logistics & Shipment Tracking | Generate consignments, update transit milestones | Create / Update | `GET /api/v1/shipments`<br>`POST /api/v1/shipments`<br>`POST /api/v1/shipments/{id}/events` | `shipments.create`<br>`shipments.update` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | Shortage Incident Closure | Close escalated shortage incidents post-dispatch | Resolve | `POST /api/v1/shortages/{id}/resolve` | `shortages.incident.resolve` | STATE | **MUST HAVE** |
| **STATE_SUPPLY_MANAGER** | Statewide Demand Forecast | Run AI consumption projections and risk models | Compute | `POST /api/v1/ai/forecast`<br>`POST /api/v1/ai/risk-analysis` | `ai.forecast.view` | STATE | **SHOULD HAVE** |
| **STATE_SUPPLY_MANAGER** | Author Prescriptions | Write prescriptions or modify clinical treatments | Create | `POST /api/v1/prescriptions` | `prescriptions.create` | — | **MUST NOT HAVE** |
| **STATE_SUPPLY_MANAGER** | Self-Approve Purchase Orders | Approve own POs without Segregation of Duties | Approve | `POST /api/v1/procurement/orders/{id}/approve` | `procurement.order.approve` | — | **MUST NOT HAVE** |
| **STATE_SUPPLY_MANAGER** | Direct Patient Care | Examine patients or access patient medical charts | View / Create | `POST /api/v1/consultations` | `consultations.conduct` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **STATE_PUBLIC_HEALTH_ANALYST** | Epidemiological Indicators | Monitor disease incidence, immunization coverage | View | `GET /api/v1/public-health/dashboard`<br>`GET /api/v1/public-health/indicators` | `analytics.indicator.read` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Configure Indicators | Create and calibrate public health metric definitions | Create | `POST /api/v1/public-health/indicators` | `analytics.indicator.manage` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Surveillance Aggregates | Submit, inspect, and validate monthly aggregates | Create / Validate | `GET /api/v1/public-health/aggregates`<br>`POST /api/v1/public-health/aggregates/validate` | `analytics.aggregate.submit` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Data Quality Audit Engine | Detect anomalous reporting spikes, missing submissions | View / Action | `GET /api/v1/public-health/data-quality`<br>`POST /api/v1/public-health/data-quality/{issue_id}/action` | `analytics.data_quality.manage` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Automated Analytics Jobs | Execute statistical modeling and trend predictions | Create / View | `POST /api/v1/public-health/analysis/run`<br>`GET /api/v1/public-health/analysis/jobs/{job_id}` | `analytics.insight.review` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Scientific Insights & Policy | Publish evidence-based policy recommendation notes | View / Create | `GET /api/v1/public-health/insights` | `analytics.insight.review` | STATE | **MUST HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Individual Patient Records | Access identifiable individual citizen medical charts | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | — | **MUST NOT HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Issue Executive Directives | Issue binding operational instructions to PHC staff | Create | `POST /api/v1/governance/actions` | `governance.action.create` | — | **MUST NOT HAVE** |
| **STATE_PUBLIC_HEALTH_ANALYST** | Stock Movements | Modify physical pharmacy or warehouse balances | Update | `POST /api/v1/inventory/adjustments` | `inventory.stock.adjust` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **NATIONAL_HEALTH_AUTHORITY** | Pan-India Health Cockpit | Comparative state performance, national health index | View | `GET /api/v1/national/dashboard`<br>`GET /api/v1/national/analytics` | `governance.national.view` | GLOBAL | **MUST HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | National Mission Schemes | Track execution of flagship health programs by state | View | `GET /api/v1/governance/schemes` | `governance.scheme.read` | GLOBAL | **MUST HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | Inter-State Coordination | Review multi-state resource sharing and deployments | View / Coordinate | `GET /api/v1/governance/actions`<br>`POST /api/v1/governance/actions` | `governance.action.create` | GLOBAL | **MUST HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | National Health Reports | Generate consolidated nationwide policy reviews | Generate / Review | `GET /api/v1/governance/reports`<br>`POST /api/v1/governance/reports/generate` | `governance.report.generate` | GLOBAL | **MUST HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | National AI Assistant | Synthesize multi-state health trends and analytics | Query | `POST /api/v1/governance/ai-assistant` | `governance.ai.assist` | GLOBAL | **SHOULD HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | Facility Identifiable Records | View identifiable patient medical history records | View | `GET /api/v1/patients/{id}/clinical-history` | `patients.records.read` | — | **MUST NOT HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | Override State Tenders | Unilaterally modify state warehouse purchasing | Approve | `POST /api/v1/procurement/orders/{id}/approve` | `procurement.order.approve` | — | **MUST NOT HAVE** |
| **NATIONAL_HEALTH_AUTHORITY** | Technical Platform Admin | Provision developer accounts or reconfigure servers | Manage | `POST /api/v1/users` | `identity.user.create` | — | **MUST NOT HAVE** |
|---|---|---|---|---|---|---|:---:|
| **SUPER_ADMIN** | Platform Health Telemetry | Server latency, database pool, worker jobs, sessions | View | `GET /api/v1/platform/dashboard` | `platform.dashboard.view` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | User Identity Provisioning | Provision, edit, and deactivate system staff users | Create / Update | `GET /api/v1/users`<br>`POST /api/v1/users`<br>`PATCH /api/v1/users/{id}` | `identity.user.create`<br>`identity.user.read`<br>`identity.user.update` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Scoped RBAC Assignment | Assign and revoke roles with explicit scope bounds | Create / Delete | `POST /api/v1/users/{id}/roles`<br>`DELETE /api/v1/users/{id}/roles/{role_id}` | `identity.role.assign` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Dynamic Role & Permission Mgmt | Define roles, toggle atomic permissions | Create / Update | `GET /api/v1/roles`<br>`POST /api/v1/roles`<br>`POST /api/v1/roles/{id}/permissions` | `identity.role.manage` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Facility Hierarchy Registry | Register and configure PHCs, Warehouses, Depots | Create / Update | `GET /api/v1/facilities`<br>`POST /api/v1/facilities`<br>`PATCH /api/v1/facilities/{id}` | `identity.facility.manage` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Security Audit Trail Explorer | Search immutable, tamper-evident audit logs | View | `GET /api/v1/audit-logs` | `audit.log.read` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Security Incident Telemetry | Inspect failed logins, privilege changes, attacks | View | `GET /api/v1/platform/security-events` | `platform.security.read` | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Dynamic Navigation Contract | Fetch authorized menu items based on permissions | View | `GET /api/v1/navigation/me` | Authenticated | GLOBAL | **MUST HAVE** |
| **SUPER_ADMIN** | Conduct Medical Consultations| Examine patients or author medical diagnoses | Create | `POST /api/v1/consultations` | `consultations.conduct` | — | **MUST NOT HAVE** |
| **SUPER_ADMIN** | Dispense Pharmaceuticals | Dispense drugs or modify active inventory stock | Dispense | `POST /api/v1/prescriptions/{id}/dispense` | `prescriptions.dispense` | — | **MUST NOT HAVE** |
| **SUPER_ADMIN** | Truncate Immutable Audit Logs| Delete or modify security audit log records | Delete | `DELETE /api/v1/audit-logs` | — | — | **MUST NOT HAVE** |
