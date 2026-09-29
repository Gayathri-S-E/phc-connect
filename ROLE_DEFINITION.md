# ROLE_DEFINITION.md — Canonical 13-Role Definition Catalog
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Architectural Authority:** This document provides the authoritative definition for the exact 13 canonical roles established in `main.md` §1.1 and `app/core/role_catalog.py`.
> Authorization is strictly enforced at the database and API level using granular permission codes (`module.resource.action`) and contextual scope hierarchy (`GLOBAL > STATE > DISTRICT > FACILITY > SELF`).

---

## 1. Role Summary Matrix

| # | Role Code | Role Name | Default Scope | Primary Domain | Core Workflow Responsibility |
|---|---|---|---|---|---|
| **01** | `PATIENT` | Citizen / Patient | `SELF` | Public Healthcare | Appointment booking, personal records, prescriptions, feedback, AI wellness. |
| **02** | `DOCTOR` | Medical Officer | `FACILITY` | Clinical Care | Consultations, vitals assessment, ICD-10 diagnoses, e-prescriptions, lab orders, referrals. |
| **03** | `NURSE` | Nurse / Healthcare Staff | `FACILITY` | Clinical Operations | Patient intake, triage vitals (EWS), lab sample collection, cold chain logging, duty roster. |
| **04** | `PHC_IN_CHARGE` | PHC In-charge / Facility Manager | `FACILITY` | Facility Management | Facility operations, staff attendance oversight, cold chain assets, outreach camps, grievances, monthly reports. |
| **05** | `PHARMACIST` | Pharmacist / PHC Storekeeper | `FACILITY` | Pharmacy & Inventory | Prescription dispensing with FEFO batch deduction, expiry alerts, supply requests, receipt verification. |
| **06** | `DISTRICT_HEALTH_OFFICER` | District Health Officer (DHO) | `DISTRICT` | Health Governance | Aggregated district health dashboard, PHC comparative metrics, administrative directives, alert review. |
| **07** | `DISTRICT_SUPPLY_OFFICER` | District Supply Chain Officer | `DISTRICT` | Supply Chain Resilience | Review facility supply requests, redistribution rebalancing, transfer approvals, state shortage escalation. |
| **08** | `DISTRICT_EMERGENCY_COORDINATOR` | District Emergency Coordinator | `DISTRICT` | Emergency Response | Incident command, affected facility tracking, rapid task allocation, emergency resource dispatch. |
| **09** | `STATE_HEALTH_ADMIN` | State Health Administrator | `STATE` | State Governance | Statewide district monitoring, inter-district approvals, state health schemes oversight, formal report sign-off. |
| **10** | `STATE_SUPPLY_MANAGER` | State Supply Chain / Warehouse Manager | `STATE` | State Warehousing | Central warehouse inventory, bulk procurement purchase orders, supplier management, shipment dispatches. |
| **11** | `STATE_PUBLIC_HEALTH_ANALYST` | State Public Health Analyst | `STATE` | Health Intelligence | Health indicators, surveillance aggregate validation, data quality anomaly detection, statistical analysis. |
| **12** | `NATIONAL_HEALTH_AUTHORITY` | National Health Authority / Central Admin | `GLOBAL` | National Oversight | Pan-India health index, inter-state coordination, national health mission targets, central policy summaries. |
| **13** | `SUPER_ADMIN` | National Platform Administrator / Super Admin | `GLOBAL` | Technical Platform | Platform telemetry, user provisioning, dynamic RBAC role/permission management, immutable audit logs. |

---

## 2. Granular Role Specifications

### Role 01 — Patient (`PATIENT`)
* **Role Name:** Citizen / Patient
* **Purpose:** Public-facing access to primary healthcare services, personal medical history, and preventive wellness advice.
* **Scope:** `SELF` (strictly restricted to records where `patient_id == current_user.id`).
* **Main Responsibility:** Book and manage consultation appointments, access verified diagnostic test results and prescriptions, submit facility feedback, and interact with the AI Wellness Assistant.
* **Primary Users:** Citizens and patients registered at a PHC.
* **Main Dashboard:** Patient Health Portal (`/patient`).
* **Allowed Modules:** `patient_portal`, `auth`, `appointments`, `prescriptions` (read-only self), `wellness_assistant`.
* **Allowed Actions:**
  * View personal profile and update contact details.
  * Schedule, reschedule, or cancel personal clinic appointments.
  * View personal consultation history, clinical diagnoses, and vitals history.
  * View issued prescriptions and medicine dispensing status.
  * Submit facility feedback, ratings, and grievances.
  * Chat with the AI Wellness Assistant in English or Tamil.
* **Restricted Actions:**
  * Cannot view or modify clinical notes or diagnoses.
  * Cannot issue, alter, or dispense prescriptions.
  * Cannot view or access other patients' records or appointments (IDOR protection enforced).
  * Cannot view facility stock levels, supply chain, or administrative dashboards.
* **Relevant APIs:**
  * `GET /api/v1/patient-portal/profile`
  * `PATCH /api/v1/patient-portal/profile`
  * `GET /api/v1/patient-portal/appointments`
  * `POST /api/v1/patient-portal/appointments/book`
  * `GET /api/v1/patient-portal/clinical-records`
  * `GET /api/v1/patient-portal/prescriptions`
  * `POST /api/v1/patient-portal/feedback`
  * `POST /api/v1/patient-portal/wellness-assistant/chat`
  * `GET /api/v1/patient-portal/awareness`
  * `GET /api/v1/patient-portal/notifications`

---

### Role 02 — Doctor / Medical Officer (`DOCTOR`)
* **Role Name:** Medical Officer / Primary Care Physician
* **Purpose:** Conduct clinical consultations, record medical diagnoses, prescribe pharmaceuticals, order diagnostic tests, and initiate referrals.
* **Scope:** `FACILITY` (scoped to assigned Primary Health Centre or Community Health Centre).
* **Main Responsibility:** Manage the daily outpatient queue, evaluate triage vitals, conduct structured consultations, prescribe essential medicines, order lab panels, and report clinical emergencies.
* **Primary Users:** Medical Officers, General Practitioners, and Specialists stationed at PHCs.
* **Main Dashboard:** Doctor Clinical Portal (`/clinical/queue`).
* **Allowed Modules:** `clinical`, `patients`, `consultations`, `prescriptions`, `labs`, `referrals`, `attendance`, `clinical_ai`.
* **Allowed Actions:**
  * View the daily OPD consultation queue for the assigned facility.
  * Access comprehensive clinical histories, vitals trends, and past consultations of queued patients.
  * Record clinical examination notes and select ICD-10 diagnostic codes.
  * Create multi-item electronic prescriptions from the facility formulary.
  * Order diagnostic laboratory tests and review completed test results.
  * Generate facility referrals with clinical notes and specialty routing.
  * Record daily duty attendance (check-in / check-out with timestamp).
  * Consult the Clinical AI Advisory Assistant for drug interactions and guideline summaries.
  * File emergency incident reports directly to the District Emergency Coordinator.
* **Restricted Actions:**
  * Cannot dispense medications or modify physical pharmacy inventory batches.
  * Cannot approve supply chain transfers or modify facility stock balances.
  * Cannot alter system RBAC permissions or create user accounts.
  * Cannot view records of patients outside assigned facility scope without active referral.
* **Relevant APIs:**
  * `GET /api/v1/doctor-portal/queue`
  * `GET /api/v1/patients/{id}/clinical-history`
  * `POST /api/v1/consultations`
  * `PATCH /api/v1/consultations/{id}/finalize`
  * `POST /api/v1/prescriptions`
  * `POST /api/v1/labs/orders`
  * `GET /api/v1/labs/orders`
  * `POST /api/v1/doctor-portal/referrals`
  * `POST /api/v1/doctor-portal/attendance/check-in`
  * `POST /api/v1/doctor-portal/attendance/check-out`
  * `POST /api/v1/doctor-portal/clinical-assistant/advise`
  * `POST /api/v1/doctor-portal/emergency-reports`

---

### Role 03 — Nurse / Healthcare Staff (`NURSE`)
* **Role Name:** Nurse / Healthcare Staff / ANM / GNM
* **Purpose:** Patient intake, triage assessments, vital sign recording, specimen collection, cold chain monitoring, and clinic roster management.
* **Scope:** `FACILITY` (assigned PHC / health sub-centre).
* **Main Responsibility:** Perform rapid patient intake, evaluate Early Warning Scores (EWS), collect and log laboratory samples, monitor vaccine refrigerator temperatures, and manage the clinic floor schedule.
* **Primary Users:** Staff Nurses, Auxiliary Nurse Midwives (ANMs), and General Nursing Midwives (GNMs).
* **Main Dashboard:** Nurse Operations Portal (`/clinical/triage`).
* **Allowed Modules:** `patients`, `triage`, `vitals`, `labs_sample`, `cold_chain`, `attendance`, `appointments`.
* **Allowed Actions:**
  * Register new walk-in patients or search existing patient profiles.
  * Record vital signs: Blood Pressure (Systolic/Diastolic), Heart Rate, Respiratory Rate, Temperature (°C/°F), SpO2, and Random Blood Sugar.
  * Compute triage priority score and trigger urgent clinician routing.
  * Collect laboratory specimens (blood, urine, sputum) and transition lab order status.
  * Log twice-daily cold chain refrigerator temperature readings.
  * Manage appointment rosters and check in arriving patients.
  * Record staff shift attendance (check-in / check-out).
* **Restricted Actions:**
  * Cannot make final medical diagnoses or conclude consultations.
  * Cannot author or authorize new prescription orders.
  * Cannot dispense controlled drugs or perform inventory stock write-offs.
  * Cannot approve inter-facility stock transfers.
* **Relevant APIs:**
  * `GET /api/v1/nurse-portal/queue`
  * `POST /api/v1/patients`
  * `POST /api/v1/nurse-portal/vitals`
  * `POST /api/v1/nurse-portal/triage-assistant/score`
  * `GET /api/v1/nurse-portal/samples`
  * `POST /api/v1/nurse-portal/samples/{id}/collect`
  * `GET /api/v1/nurse-portal/cold-chain`
  * `POST /api/v1/nurse-portal/cold-chain/log`
  * `PATCH /api/v1/appointments/{id}/status`
  * `POST /api/v1/nurse-portal/attendance/check-in`
  * `POST /api/v1/nurse-portal/attendance/check-out`

---

### Role 04 — PHC In-charge / Facility Manager (`PHC_IN_CHARGE`)
* **Role Name:** PHC In-charge / Medical Officer In-charge / Facility Administrator
* **Purpose:** Overall day-to-day administrative oversight of PHC operations, staff duty deployment, cold chain infrastructure, field camps, grievances, and facility compliance.
* **Scope:** `FACILITY` (assigned PHC and linked sub-centres).
* **Main Responsibility:** Supervise clinical and administrative staff, monitor absenteeism and duty rosters, oversee vaccine cold chain integrity, plan village outreach camps, resolve patient complaints, and generate monthly operational reports.
* **Primary Users:** Senior Medical Officers, PHC Superintendents, and Health Facility Administrators.
* **Main Dashboard:** Facility Administration Dashboard (`/facility`).
* **Allowed Modules:** `facility_admin`, `staff_attendance`, `cold_chain`, `outreach`, `complaints`, `reports`, `inventory_read`, `dashboards`.
* **Allowed Actions:**
  * Monitor facility operational KPIs (OPD volume, bed occupancy, doctor roster, medicine stock warnings).
  * Review staff attendance ledger across all doctors, nurses, and technicians by date range.
  * Manage cold chain assets, register equipment, and investigate temperature excursions.
  * Plan, schedule, and track village health outreach camps.
  * Review, triage, and resolve patient complaints and facility grievances.
  * Generate aggregate monthly facility operational reports for district submission.
  * Review facility-level alerts and acknowledge notifications.
* **Restricted Actions:**
  * Cannot alter clinical diagnoses or patient medical charts of other clinicians.
  * Cannot directly dispense medications from pharmacy stock.
  * Cannot create platform users or grant administrative privileges.
  * Cannot access or modify other PHCs' confidential administrative records.
* **Relevant APIs:**
  * `GET /api/v1/dashboards/phc`
  * `GET /api/v1/facility-admin/staff-attendance`
  * `GET /api/v1/facility-admin/cold-chain/equipment`
  * `POST /api/v1/facility-admin/cold-chain/equipment`
  * `GET /api/v1/facility-admin/cold-chain/logs`
  * `GET /api/v1/facility-admin/outreach-camps`
  * `POST /api/v1/facility-admin/outreach-camps`
  * `PATCH /api/v1/facility-admin/outreach-camps/{id}`
  * `GET /api/v1/facility-admin/complaints`
  * `PATCH /api/v1/facility-admin/complaints/{id}/status`
  * `GET /api/v1/facility-admin/reports/monthly`

---

### Role 05 — Pharmacist / PHC Storekeeper (`PHARMACIST`)
* **Role Name:** Pharmacist / Dispensary Manager / PHC Storekeeper
* **Purpose:** Pharmacy dispensing operations, First-Expiring-First-Out (FEFO) batch tracking, inventory management, supply requisitions, and delivery verification.
* **Scope:** `FACILITY` (assigned PHC dispensary and drug store).
* **Main Responsibility:** Review doctor prescriptions, verify patient identity, allocate batches using automated FEFO sequencing, confirm medicine dispensing, manage local stock balances, raise supply requests, and verify receipt of incoming shipments.
* **Primary Users:** Registered Pharmacists and Pharmacy Officers at PHCs.
* **Main Dashboard:** Pharmacy & Dispensing Portal (`/pharmacy/dispense`).
* **Allowed Modules:** `pharmacy`, `inventory`, `prescriptions`, `supply_requests`, `transfers`, `alerts`.
* **Allowed Actions:**
  * View pending prescription queue generated by clinic consultations.
  * Inspect available medication batches sorted strictly by expiration date (FEFO preview).
  * Execute dispensing transactions, atomically decrementing inventory batch balances.
  * Inspect real-time facility stock on hand, safety stock thresholds, and stockout warnings.
  * Review batches nearing expiration (30/60/90-day alert horizons).
  * Raise supply requests to the District Drug Warehouse for replenishment.
  * Inspect incoming stock transfer consignments and record physical receipt verification.
  * Record physical stock count adjustments and shrinkage write-offs with audit reasons.
  * Record pharmacist shift attendance.
* **Restricted Actions:**
  * Cannot create or edit clinical prescriptions or alter prescribed dosages.
  * Cannot conduct consultations or author diagnoses.
  * Cannot approve district-level stock transfers between external facilities.
  * Cannot issue purchase orders to external pharmaceutical manufacturers.
* **Relevant APIs:**
  * `GET /api/v1/pharmacist-portal/queue`
  * `GET /api/v1/prescriptions/{id}`
  * `POST /api/v1/prescriptions/{id}/dispense`
  * `GET /api/v1/inventory`
  * `GET /api/v1/inventory/batches/expiring`
  * `POST /api/v1/supply-requests`
  * `GET /api/v1/supply-requests`
  * `POST /api/v1/supply-requests/{id}/receipts/{transfer_id}/verify`
  * `POST /api/v1/inventory/adjustments`
  * `POST /api/v1/pharmacist-portal/attendance/check-in`

---

### Role 06 — District Health Officer (`DISTRICT_HEALTH_OFFICER`)
* **Role Name:** District Health Officer (DHO) / Chief Medical Officer (District)
* **Purpose:** District-level public health administration, service delivery oversight, administrative action coordination, and disease alert management across all PHCs.
* **Scope:** `DISTRICT` (restricted to healthcare facilities located within the assigned district).
* **Main Responsibility:** Monitor aggregated district healthcare metrics (footfalls, disease trends, high-risk cases), compare PHC operational readiness, issue binding administrative action directives, review health alerts, and track national health scheme indicators.
* **Primary Users:** District Health Officers, Deputy DHOs, and District Program Managers.
* **Main Dashboard:** District Governance Dashboard (`/district`).
* **Allowed Modules:** `governance`, `district_oversight`, `actions`, `alerts`, `schemes`, `reports`, `dho_ai`.
* **Allowed Actions:**
  * View real-time district health overview (total OPD volume, critical referral rate, facility readiness).
  * Compare facility-level performance without exposing individual patient identities.
  * Create, assign, and track administrative action items with mandatory due dates.
  * Review and acknowledge district-level health alerts and outbreak indicators.
  * Monitor progress of National and State Health Mission schemes across the district.
  * Generate formal district monthly and quarterly health administrative reports.
  * Query the District AI Governance Assistant for aggregated trends and policy summaries.
* **Restricted Actions:**
  * Cannot access individual patient medical histories, clinical charts, or identifiable data.
  * Cannot modify clinical consultation notes or diagnostic conclusions.
  * Cannot approve financial purchase orders (owned by procurement / state supply).
  * Cannot access or manage facilities located in other districts.
* **Relevant APIs:**
  * `GET /api/v1/district/dashboard`
  * `GET /api/v1/district/facilities/{facility_id}`
  * `GET /api/v1/district/analytics`
  * `GET /api/v1/governance/actions`
  * `POST /api/v1/governance/actions`
  * `PATCH /api/v1/governance/actions/{id}/transition`
  * `GET /api/v1/governance/alerts`
  * `POST /api/v1/governance/alerts/{id}/transition`
  * `GET /api/v1/governance/schemes`
  * `GET /api/v1/governance/reports`
  * `POST /api/v1/governance/reports/generate`
  * `POST /api/v1/governance/ai-assistant`

---

### Role 07 — District Supply Chain Officer (`DISTRICT_SUPPLY_OFFICER`)
* **Role Name:** District Supply Chain Officer (DSCO) / District Drug Store Manager
* **Purpose:** District pharmaceutical supply chain management, replenishment review, inter-facility stock redistribution, and shortage escalation.
* **Scope:** `DISTRICT` (district drug depot and all healthcare facilities within the district).
* **Main Responsibility:** Review medicine requisitions from PHC pharmacists, allocate transfers from the District Drug Warehouse, orchestrate inter-facility redistribution from surplus to deficit clinics, approve transfer dispatches, escalate severe stockouts to the State Central Warehouse, and evaluate AI risk forecasts.
* **Primary Users:** District Supply Officers, Pharmacists Grade-I, and Logistics Managers.
* **Main Dashboard:** District Supply Operations Portal (`/supply/requests`).
* **Allowed Modules:** `supply_chain`, `supply_requests`, `transfers`, `inventory`, `shortages`, `ai_forecast`.
* **Allowed Actions:**
  * Review all pending supply requests raised by PHCs across the district.
  * Generate redistribution plans between surplus facilities and stock-depleted facilities.
  * Approve and authorize inter-facility stock transfer shipments.
  * Escalate unresolvable district shortages to the State Central Medical Warehouse.
  * Share clinical health impact assessments of drug stockouts with the District Health Officer.
  * View predictive AI 30/60/90-day consumption forecasts and facility disruption scores.
  * Track transit shipments of allocated medicines across the district.
* **Restricted Actions:**
  * Cannot dispense medications directly to patients.
  * Cannot create or issue purchase orders directly to commercial manufacturers without state approval.
  * Cannot modify clinical consultation records or access identifiable patient charts.
  * Cannot reallocate inventory belonging to facilities in other districts.
* **Relevant APIs:**
  * `GET /api/v1/supply-requests`
  * `POST /api/v1/supply-requests/{id}/decision`
  * `POST /api/v1/supply-requests/{id}/allocate`
  * `POST /api/v1/supply-requests/{id}/escalate`
  * `POST /api/v1/supply-requests/{id}/health-impact`
  * `GET /api/v1/inventory/transfers`
  * `POST /api/v1/inventory/transfers/{id}/approve`
  * `POST /api/v1/inventory/transfers/{id}/dispatch`
  * `POST /api/v1/shortages/{id}/escalate`
  * `POST /api/v1/ai/forecast`
  * `POST /api/v1/ai/risk-analysis`

---

### Role 08 — District Emergency Coordinator (`DISTRICT_EMERGENCY_COORDINATOR`)
* **Role Name:** District Emergency Coordinator / Disaster Management Officer
* **Purpose:** Command, coordinate, and monitor public health emergency response, disease outbreaks, disaster incidents, and rapid medical mobilization.
* **Scope:** `DISTRICT` (all facilities, mobile units, and emergency teams in the district).
* **Main Responsibility:** Declare and manage emergency incidents (floods, epidemics, mass casualties), map affected facilities, assign and track emergency response tasks, coordinate rapid medicine/personnel deployment, and escalate cross-district resource needs.
* **Primary Users:** District Emergency Coordinators, Disaster Response Officers, and Public Health Rapid Response Officers.
* **Main Dashboard:** Emergency Operations Command Center (`/emergency`).
* **Allowed Modules:** `emergency`, `facilities_affected`, `emergency_tasks`, `rapid_resources`, `incident_reports`.
* **Allowed Actions:**
  * View live emergency command dashboard with active incident summary and affected sites.
  * Declare new emergency incidents with category, severity, and response goals.
  * Map affected Primary Health Centres and emergency field health posts.
  * Create, assign, and track priority tasks for medical response teams.
  * Submit emergency resource requisitions (ORS kits, antivenoms, trauma sets, extra doctors).
  * Update incident severity and transition lifecycle status (ACTIVE, CONTAINED, RESOLVED).
  * Escalate emergency support requests to the State Disaster Management cell.
* **Restricted Actions:**
  * Cannot modify routine outpatient queues or clinical consultations.
  * Cannot alter baseline routine pharmacy inventory or change pricing.
  * Cannot access non-emergency clinical patient charts.
  * Cannot declare emergencies in other districts without state authorization.
* **Relevant APIs:**
  * `GET /api/v1/emergencies/dashboard`
  * `GET /api/v1/emergencies`
  * `POST /api/v1/emergencies`
  * `GET /api/v1/emergencies/{id}`
  * `PATCH /api/v1/emergencies/{id}/status`
  * `PATCH /api/v1/emergencies/{id}/priority`
  * `PUT /api/v1/emergencies/{id}/facilities`
  * `POST /api/v1/emergencies/{id}/tasks`
  * `PATCH /api/v1/emergencies/{id}/tasks/{task_id}`
  * `POST /api/v1/emergencies/{id}/resources`
  * `POST /api/v1/emergencies/{id}/escalate`
  * `POST /api/v1/emergencies/{id}/resolve`

---

### Role 09 — State Health Administrator (`STATE_HEALTH_ADMIN`)
* **Role Name:** State Health Administrator / Director of Public Health
* **Purpose:** Statewide public health administration, inter-district resource approvals, health scheme enforcement, and executive policy direction.
* **Scope:** `STATE` (all districts, Community Health Centres, PHCs, and state medical facilities).
* **Main Responsibility:** Monitor statewide public health KPIs, compare district performance benchmarks, review and decide on high-value emergency approvals, manage state health mission programs, and review official governance reports.
* **Primary Users:** Directors of Public Health, State Health Secretaries, and State Program Directors.
* **Main Dashboard:** State Health Governance Cockpit (`/state`).
* **Allowed Modules:** `governance`, `state_oversight`, `approvals`, `schemes_manage`, `reports_review`.
* **Allowed Actions:**
  * View statewide health overview aggregating patient volume, maternal/child care, and disease burdens.
  * Compare district performance rankings and review facilities requiring urgent attention.
  * Formally approve or reject high-value procurement requests and cross-district resource shifts.
  * Configure state health schemes, set district target quotas, and monitor compliance metrics.
  * Review, annotate, and officially sign off on monthly/quarterly state health reports.
  * Direct state-level health alerts and instructions to District Health Officers.
  * Consult State AI Governance Assistant for macro epidemiological and supply patterns.
* **Restricted Actions:**
  * Cannot access individual patient identifiable records (HIPAA/DISHA compliance).
  * Cannot author doctor consultations or dispense medicines.
  * Cannot perform direct warehouse physical stock movements.
  * Cannot oversee or modify data outside the state boundary.
* **Relevant APIs:**
  * `GET /api/v1/state/dashboard`
  * `GET /api/v1/state/analytics`
  * `GET /api/v1/governance/approvals`
  * `POST /api/v1/governance/approvals/{id}/decision`
  * `GET /api/v1/governance/schemes`
  * `POST /api/v1/governance/schemes`
  * `POST /api/v1/governance/schemes/{id}/targets`
  * `GET /api/v1/governance/reports`
  * `POST /api/v1/governance/reports/{id}/review`
  * `POST /api/v1/governance/ai-assistant`

---

### Role 10 — State Supply Chain / Warehouse Manager (`STATE_SUPPLY_MANAGER`)
* **Role Name:** State Supply Chain / Warehouse Manager / State Drug Logistics Director
* **Purpose:** State Central Medical Warehouse operations, bulk procurement, supplier onboarding, and district inventory replenishment.
* **Scope:** `STATE` (State Central Warehouse, Regional Depots, and District Warehouses).
* **Main Responsibility:** Oversee central pharmaceutical inventory, maintain strategic buffer stock reserves, review escalated district medicine requests, allocate bulk supplies, create purchase orders to approved manufacturers, and track logistics shipments.
* **Primary Users:** State Warehouse Managers, Logistics Directors, and Medical Services Corporation Officers.
* **Main Dashboard:** State Supply Chain Command Center (`/supply`).
* **Allowed Modules:** `supply_chain`, `warehouse_state`, `procurement`, `suppliers`, `shipments`, `shortages`.
* **Allowed Actions:**
  * Monitor State Central Warehouse inventory levels, safety margins, and expiring stock lots.
  * Review district supply escalations and allocate shipments from the central stockpile.
  * Author and manage purchase requisitions and purchase orders (POs) to suppliers.
  * Onboard approved pharmaceutical suppliers, update catalogs, and record vendor delivery ratings.
  * Dispatch bulk consignments and update logistics milestone events (IN_TRANSIT, DELAYED, DELIVERED).
  * Resolve escalated shortage incidents once fulfillment shipments are dispatched.
  * Run statewide AI replenishment risk models and consumption forecast projections.
* **Restricted Actions:**
  * Cannot author clinical prescriptions or examine patients.
  * Cannot approve purchase orders authored by themselves without Segregation of Duties (SoD) enforcement.
  * Cannot directly dispense unit-dose medicines to citizens.
  * Cannot access facilities or warehouses outside the assigned state.
* **Relevant APIs:**
  * `GET /api/v1/supply-requests/state/dashboard`
  * `GET /api/v1/supply-requests/state/overview`
  * `POST /api/v1/supply-requests/{id}/allocate`
  * `GET /api/v1/procurement/orders`
  * `POST /api/v1/procurement/orders`
  * `POST /api/v1/procurement/orders/{id}/approve`
  * `GET /api/v1/suppliers`
  * `POST /api/v1/suppliers`
  * `GET /api/v1/shipments`
  * `POST /api/v1/shipments`
  * `POST /api/v1/shipments/{id}/events`
  * `POST /api/v1/shortages/{id}/resolve`

---

### Role 11 — State Public Health Analyst (`STATE_PUBLIC_HEALTH_ANALYST`)
* **Role Name:** State Public Health Analyst / Epidemiologist
* **Purpose:** Epidemiological analytics, public health indicator surveillance, data quality auditing, and scientific trend forecasting.
* **Scope:** `STATE` (statewide surveillance data and epidemiological registers).
* **Main Responsibility:** Track key public health indicators (maternal mortality, communicable disease spikes, immunization coverage), audit data quality across district submissions, trigger automated analytical modeling jobs, and formulate evidence-based policy insights.
* **Primary Users:** State Epidemiologists, Biostatisticians, and Public Health Analysts.
* **Main Dashboard:** Public Health Analytics Workspace (`/analytics`).
* **Allowed Modules:** `public_health`, `indicators`, `aggregates`, `data_quality`, `analysis_jobs`, `insights`.
* **Allowed Actions:**
  * View epidemiological indicator dashboard (communicable outbreaks, immunization rates, chronic disease).
  * Configure and maintain canonical public health indicator definitions.
  * Validate and submit monthly epidemiological surveillance aggregates.
  * Run automated data quality audits to detect missing data, anomalous reporting, or outliers.
  * Dispatch data quality correction notices to responsible reporting districts.
  * Launch asynchronous statistical trend analysis jobs and review epidemiological models.
  * Author, review, and publish scientific public health insights and policy advisories.
* **Restricted Actions:**
  * Cannot access raw individual patient charts or identifiable medical records.
  * Cannot modify clinical consultations, prescriptions, or laboratory tests.
  * Cannot modify inventory stock levels or alter supply chain transfers.
  * Cannot issue binding executive directives (reserved for State Health Admin).
* **Relevant APIs:**
  * `GET /api/v1/public-health/dashboard`
  * `GET /api/v1/public-health/indicators`
  * `POST /api/v1/public-health/indicators`
  * `GET /api/v1/public-health/aggregates`
  * `POST /api/v1/public-health/aggregates`
  * `POST /api/v1/public-health/aggregates/validate`
  * `GET /api/v1/public-health/trends`
  * `POST /api/v1/public-health/analysis/run`
  * `GET /api/v1/public-health/analysis/jobs/{job_id}`
  * `GET /api/v1/public-health/data-quality`
  * `POST /api/v1/public-health/data-quality/{issue_id}/action`
  * `GET /api/v1/public-health/insights`

---

### Role 12 — National Health Authority (`NATIONAL_HEALTH_AUTHORITY`)
* **Role Name:** National Health Authority / Central Health Administrator (MoHFW)
* **Purpose:** National macro-level healthcare monitoring, inter-state coordination, central scheme progress tracking, and national policy leadership.
* **Scope:** `GLOBAL` (read access across all states and national health entities).
* **Main Responsibility:** Review pan-India health metrics and comparative state health indices, monitor national health missions, coordinate emergency resource mobilization across states, and review national health bulletins.
* **Primary Users:** Ministry of Health & Family Welfare (MoHFW) Officers, National Health Mission (NHM) Directors.
* **Main Dashboard:** National Health Command Portal (`/national`).
* **Allowed Modules:** `governance`, `national_oversight`, `schemes_national`, `inter_state_coordination`, `reports_national`.
* **Allowed Actions:**
  * View the Pan-India National Health Dashboard with state-by-state comparisons.
  * Monitor progress of national health flagship schemes across all participating states.
  * Review and coordinate inter-state emergency resource sharing requests.
  * Review aggregate nationwide maternal health, immunization, and disease burden indices.
  * Generate high-level national policy synthesis reports and executive summaries.
  * Consult the National AI Assistant for multi-state trend syntheses.
* **Restricted Actions:**
  * Cannot access individual patient records or clinic-level identifiable charts.
  * Cannot override state-level operational decisions without statutory authority.
  * Cannot dispense drugs, conduct consultations, or perform facility store counts.
  * Cannot alter platform system infrastructure or user credentials (held by Super Admin).
* **Relevant APIs:**
  * `GET /api/v1/national/dashboard`
  * `GET /api/v1/national/analytics`
  * `GET /api/v1/governance/schemes`
  * `GET /api/v1/governance/reports`
  * `POST /api/v1/governance/reports/generate`
  * `POST /api/v1/governance/reports/{id}/review`
  * `POST /api/v1/governance/ai-assistant`

---

### Role 13 — National Platform Administrator / Super Admin (`SUPER_ADMIN`)
* **Role Name:** National Platform Administrator / Super Administrator
* **Purpose:** Technical governance, identity and access management (IAM), dynamic RBAC configuration, facility registry, platform security telemetry, and audit log auditing.
* **Scope:** `GLOBAL` (unrestricted technical management across all platform tenants).
* **Main Responsibility:** Maintain platform availability and infrastructure uptime, provision user accounts and assign scoped roles, manage facility and organization hierarchies, monitor system security and failed login telemetry, and inspect immutable audit logs.
* **Primary Users:** Chief Technology Officers, Platform Administrators, and Systems Security Engineers.
* **Main Dashboard:** Platform Administration & Governance Cockpit (`/platform`).
* **Allowed Modules:** `platform`, `identity`, `users`, `roles`, `permissions`, `facilities`, `audit`, `security`.
* **Allowed Actions:**
  * View technical system health, database latency, active worker jobs, and session counts.
  * Provision, update, and suspend staff user accounts across all facilities and organizations.
  * Dynamically assign roles with explicit administrative scopes (`GLOBAL`, `STATE`, `DISTRICT`, `FACILITY`).
  * Create, edit, and toggle dynamic custom roles and assign atomic permission codes.
  * Register and manage the national facility hierarchy (PHCs, CHCs, Warehouses, Depots).
  * Inspect the tamper-evident, append-only security audit log with full actor provenance.
  * Monitor platform security events (failed logins, privilege assignments, password rotations).
* **Restricted Actions:**
  * **Strict Segregation of Duties:** Holds no clinical authority; cannot write prescriptions, conduct doctor consultations, or alter patient medical records.
  * Cannot dispense medications or execute commercial procurement transactions.
  * Cannot delete or truncate immutable audit log entries.
* **Relevant APIs:**
  * `GET /api/v1/platform/dashboard`
  * `GET /api/v1/platform/security-events`
  * `GET /api/v1/navigation/me`
  * `GET /api/v1/users`
  * `POST /api/v1/users`
  * `PATCH /api/v1/users/{id}`
  * `POST /api/v1/users/{id}/roles`
  * `DELETE /api/v1/users/{id}/roles/{role_id}`
  * `GET /api/v1/roles`
  * `POST /api/v1/roles`
  * `POST /api/v1/roles/{id}/permissions`
  * `GET /api/v1/permissions`
  * `GET /api/v1/facilities`
  * `POST /api/v1/facilities`
  * `PATCH /api/v1/facilities/{id}`
  * `GET /api/v1/audit-logs`
