# ROLE_FLOWS.md — End-to-End Feature Flows Across All 13 Roles
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Execution Standard:** Every feature across all 13 roles adheres strictly to the authoritative flow:
> `USER OPENS FEATURE -> PAGE LOAD -> DATA FETCH -> USER SEES INFORMATION -> USER TAKES ACTION -> FRONTEND VALIDATION -> API REQUEST -> BACKEND AUTHORIZATION -> BUSINESS LOGIC -> DATABASE CHANGE -> AUDIT LOG -> API RESPONSE -> UI SUCCESS/ERROR -> UPDATED STATUS -> NEXT ACTION`
> No feature is treated as static UI or dummy cards.

---

# ROLE 01: CITIZEN / PATIENT (`PATIENT`)

### 1. LOGIN FLOW
- **Credential Entry:** Citizen opens `/login`, inputs registered email/phone and password (e.g. `patient@demo.smarthealth.local` / `Demo@Health2026`).
- **Client Validation:** Email format checked, password required (>6 chars).
- **API Request:** `POST /api/v1/auth/login` with `{ "email": "...", "password": "..." }`.
- **Backend Action:** Verifies hashed bcrypt password, loads user roles, verifies `PATIENT` role and `SELF` scope. Generates access JWT and SHA-256 hashed refresh token. Logs `AUTH_LOGIN_SUCCESS`.
- **Success State:** Access token stored in memory/session, user directed to `/patient`.
- **Error State:** Invalid credentials returns RFC 7807 401 with alert banner "Invalid email or password".

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/patient`.
- **Data Fetch:** Parallel calls to:
  1. `GET /api/v1/patient-portal/profile`
  2. `GET /api/v1/patient-portal/appointments`
  3. `GET /api/v1/patient-portal/prescriptions`
  4. `GET /api/v1/patient-portal/awareness`
- **What User Sees:** Patient header with UHID and demographic badge; upcoming appointment cards with token numbers; active prescription alerts; quick action buttons ("Book Appointment", "Ask AI Wellness", "View Records").
- **Empty State:** Friendly banner: "No upcoming appointments. Book a consultation below."

### 3. FEATURE 1: APPOINTMENT BOOKING
- **Purpose:** Schedule a consultation slot at the assigned PHC.
- **Who Can Access:** Authenticated Patient (`SELF` scope).
- **What User Sees:** Date picker, department/specialty selector, list of available doctors and token slots for the chosen day.
- **User Action:** Selects date, chooses department (General Medicine, ANC, Pediatrics), picks slot, clicks "Confirm Booking".
- **Input:** `{ "facility_id": "UUID", "appointment_date": "2026-09-30", "slot_time": "10:00:00", "reason_for_visit": "Persistent cough" }`.
- **Validation:** Date must be today or future; reason must not exceed 255 chars; all fields mandatory.
- **API:** `POST /api/v1/patient-portal/appointments/book`.
- **Backend Action:** Verifies user identity, checks slot capacity, allocates incremental token number atomically.
- **Database Effect:** Inserts row into `appointments` with status `SCHEDULED`.
- **Audit:** Records audit log `APPOINTMENT_BOOKED` with `patient_id` and `appointment_id`.
- **Success State:** Displays confirmation modal with allocated Token Number (e.g., `#04`), date, and doctor.
- **Error State:** If slot full (409 Conflict), displays "Selected slot is fully booked. Please pick an alternative time."
- **Empty State:** If clinic closed on selected date, displays "No clinics scheduled on this day."
- **Next Action:** Appointment immediately renders at the top of Upcoming Appointments list; option to download/print slip.

### 4. FEATURE 2: CLINICAL RECORDS & LAB RESULTS VIEW
- **Purpose:** Access past diagnoses, vitals, and physician notes.
- **Who Can Access:** Authenticated Patient (`SELF` scope).
- **What User Sees:** Chronological timeline of clinical encounters, recorded blood pressure/temperature, and verified lab test reports.
- **User Action:** Clicks an encounter item to expand detailed physician notes, vitals table, and lab test values with reference ranges.
- **Input:** None (Read-only query).
- **Validation:** Server ensures `patient_id == current_user.id`.
- **API:** `GET /api/v1/patient-portal/clinical-records`.
- **Backend Action:** Executes filtered join on `consultations`, `vitals`, `lab_orders`, and `diagnoses`.
- **Database Effect:** None (Read query).
- **Audit:** Logs `PATIENT_CLINICAL_RECORDS_ACCESSED`.
- **Success State:** Renders timeline with status badges (e.g. `NORMAL`, `OUT_OF_RANGE`).
- **Error State:** Network error shows retry button; 403 Forbidden redirects to login.
- **Empty State:** "No medical records found on file."
- **Next Action:** Ability to print record summary or query the AI Wellness Assistant regarding prescribed lifestyle care.

### 5. FEATURE 3: FEEDBACK & GRIEVANCE SUBMISSION
- **Purpose:** Submit citizen satisfaction ratings and grievances regarding PHC services.
- **Who Can Access:** Authenticated Patient.
- **What User Sees:** Star rating selector (1-5), category dropdown (Cleanliness, Staff Behavior, Medicine Availability, Waiting Time), feedback text area.
- **User Action:** Fills out feedback form, clicks "Submit Feedback".
- **Input:** `{ "facility_id": "UUID", "category": "WAITING_TIME", "rating": 4, "comments": "Quick doctor visit, but pharmacy line took 20 minutes." }`.
- **Validation:** Rating must be 1-5; comments required (>10 chars).
- **API:** `POST /api/v1/patient-portal/feedback`.
- **Backend Action:** Validates facility ID, persists feedback entry, tags high-severity grievances for PHC In-charge triage.
- **Database Effect:** Inserts row into `feedback_complaints` with status `OPEN`.
- **Audit:** Logs `PATIENT_FEEDBACK_SUBMITTED`.
- **Success State:** Green success toast: "Thank you for helping us improve our health services."
- **Error State:** Displays specific validation error message.
- **Empty State:** Prior feedback history list displays "No previous feedback submitted."
- **Next Action:** Feedback entry appears in patient's feedback history list with status `UNDER_REVIEW`.

### 6. FORBIDDEN ACTIONS
- Cannot access clinical notes of any other citizen. Attempting to pass another patient UUID returns 403 Forbidden.
- Cannot issue prescriptions, alter diagnostic ICD-10 codes, or view internal staff rosters.

### 7. NOTIFICATIONS
- Real-time alerts for appointment confirmation, prescription dispensing ready for collection, and lab test verified.

### 8. AI FEATURES
- **Patient AI Wellness Assistant:** Dockable conversational agent responding in English or Tamil. Answers preventive health queries, diet, and lifestyle recommendations. Strictly refuses clinical diagnoses, prescribing, or emergency triage.

### 9. HISTORY
- Persistent record of all past appointments, prescriptions fulfilled, and laboratory reports with date filtering.

### 10. COMPLETE ROLE JOURNEY
- Citizen registers -> Logs in -> Books consultation appointment for tomorrow -> Arrives at PHC -> Nurse logs vitals -> Doctor consults and prescribes -> Pharmacist dispenses -> Citizen receives notification -> Citizen reviews dispensed medications on portal -> Submits 5-star feedback.

---

# ROLE 02: MEDICAL OFFICER / DOCTOR (`DOCTOR`)

### 1. LOGIN FLOW
- **Credential Entry:** Doctor inputs credentials (e.g. `doctor@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Authenticates password, validates `DOCTOR` role, confirms `FACILITY` scope assignment (`PHC-KOV-001`).
- **Success State:** Navigates to `/clinical/queue`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/clinical/queue`.
- **Data Fetch:** Calls `GET /api/v1/doctor-portal/queue` and `GET /api/v1/doctor-portal/attendance/today`.
- **What User Sees:** Attendance badge (Checked In / Out); OPD Queue table split into `WAITING`, `TRIAGED (VITALS RECORDED)`, and `IN_CONSULTATION`; patient search bar; emergency broadcast alert button.
- **Empty State:** "No patients waiting in queue today."

### 3. FEATURE 1: CONDUCT CONSULTATION & DIAGNOSIS
- **Purpose:** Document patient encounter, clinical observations, and ICD-10 diagnosis.
- **Who Can Access:** Authenticated Doctor with `consultations.conduct` permission.
- **What User Sees:** Queued patient's intake vitals (BP, SpO2, Heart Rate, Temp, Blood Sugar), triage score, past medical history, symptoms text editor, searchable ICD-10 diagnosis selector.
- **User Action:** Doctor enters chief complaints, clinical examination findings, selects primary ICD-10 code (e.g., `J18.9 - Pneumonia`), clicks "Save & Prescribe".
- **Input:** `{ "patient_id": "UUID", "chief_complaints": "Fever for 4 days, productive cough", "examination_notes": "Bilateral crepitations in chest", "diagnosis_codes": ["J18.9"] }`.
- **Validation:** Chief complaints required; at least one valid diagnosis code required.
- **API:** `POST /api/v1/consultations`.
- **Backend Action:** Creates consultation record, links to patient, transitions appointment to `IN_PROGRESS`.
- **Database Effect:** Inserts `consultations` row, updates `appointments.status = 'IN_PROGRESS'`.
- **Audit:** Logs `CONSULTATION_INITIATED`.
- **Success State:** Encounter workspace unlocked, prescription and lab order tabs active.
- **Error State:** RFC 7807 422 error rendered next to invalid input fields.
- **Empty State:** N/A.
- **Next Action:** Proceed to author electronic prescription and lab orders.

### 4. FEATURE 2: ELECTRONIC PRESCRIPTION GENERATION
- **Purpose:** Prescribe pharmaceuticals from the facility formulary.
- **Who Can Access:** Authenticated Doctor with `prescriptions.create`.
- **What User Sees:** Formulary drug search, dosage form, strength, frequency dropdown (e.g., TDS - 1-1-1), duration in days, special instructions (After food), real-time facility stock availability badge.
- **User Action:** Selects `Amoxicillin 500mg`, specifies `1 Capsule TDS for 5 days`, adds `Paracetamol 500mg SOS`, clicks "Sign & Submit Prescription".
- **Input:** `{ "consultation_id": "UUID", "items": [{ "medication_id": "UUID", "dosage": "500mg", "frequency": "TDS", "duration_days": 5, "instructions": "After meals" }] }`.
- **Validation:** Duration > 0; medication must exist in master formulary.
- **API:** `POST /api/v1/prescriptions`.
- **Backend Action:** Persists prescription header and item rows; links to consultation and patient; marks status `PENDING_DISPENSING`.
- **Database Effect:** Inserts row into `prescriptions` and `prescription_items`.
- **Audit:** Logs `PRESCRIPTION_ISSUED` with doctor ID, patient ID, and medicine item counts.
- **Success State:** Prescription successfully locked with verification hash. Sent to Pharmacist dispensing queue.
- **Error State:** If drug discontinued or unavailable, alert suggests alternatives.
- **Next Action:** Prompt to order diagnostic lab tests or finalize consultation.

### 5. FEATURE 3: DIAGNOSTIC LAB ORDER
- **Purpose:** Request laboratory tests (Complete Blood Count, Sputum AFB, Widal, Blood Sugar).
- **Who Can Access:** Authenticated Doctor with `labs.order.create`.
- **What User Sees:** Checkbox list of diagnostic test panels, clinical indication field, priority toggle (`ROUTINE` / `URGENT`).
- **User Action:** Checks `Complete Blood Count (CBC)` and `Random Blood Sugar`, enters indication "Suspected bacterial infection", clicks "Order Lab Tests".
- **Input:** `{ "patient_id": "UUID", "consultation_id": "UUID", "tests": ["CBC", "RBS"], "priority": "ROUTINE", "clinical_indication": "Fever investigation" }`.
- **Validation:** At least one test required.
- **API:** `POST /api/v1/labs/orders`.
- **Backend Action:** Creates lab order in `PENDING_COLLECTION` state; routes order to Nurse/Lab Technician portal.
- **Database Effect:** Inserts `lab_orders` row.
- **Audit:** Logs `LAB_ORDER_CREATED`.
- **Success State:** Success toast: "Lab order #LO-8821 dispatched to laboratory queue."
- **Next Action:** Finalize consultation; patient routed to phlebotomy/lab sample collection.

### 6. FORBIDDEN ACTIONS
- Cannot physically deduct or dispense inventory batches from the dispensary.
- Cannot adjust inventory write-offs or shrinkage.
- Cannot alter user accounts, assign roles, or access other PHC clinical records.

### 7. NOTIFICATIONS
- Urgent alert badge when a nurse records a high Early Warning Score (EWS >= 5) for a waiting patient.
- Notification when a critical lab result is reported by the lab technician.

### 8. AI FEATURES
- **Clinical AI Advisory Assistant:** Provides drug interaction analysis, standard treatment guideline summaries, and pediatric dosage calculators based on grounded clinical protocols.

### 9. HISTORY
- Searchable archive of all consultations finalized by the doctor, filterable by date and diagnosis category.

### 10. COMPLETE ROLE JOURNEY
- Doctor checks in attendance -> Opens OPD queue -> Selects next triaged patient -> Reviews vitals -> Conducts examination -> Records ICD-10 diagnosis -> Prescribes antibiotics -> Orders CBC lab test -> Finalizes consultation -> Patient automatically moves to lab and pharmacy queues.

---

# ROLE 03: NURSE / HEALTHCARE STAFF (`NURSE`)

### 1. LOGIN FLOW
- **Credential Entry:** Nurse inputs credentials (e.g. `nurse@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Verifies credentials, confirms `NURSE` role, validates facility scope.
- **Success State:** Navigates to `/clinical/triage`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/clinical/triage`.
- **Data Fetch:** Calls `GET /api/v1/nurse-portal/queue`, `GET /api/v1/nurse-portal/samples`, and `GET /api/v1/nurse-portal/cold-chain`.
- **What User Sees:** Triage intake queue; sample collection counter; morning/evening cold chain temperature status; "New Patient Intake" button.
- **Empty State:** "No arriving patients awaiting triage."

### 3. FEATURE 1: PATIENT INTAKE & TRIAGE VITALS (EWS)
- **Purpose:** Rapid patient intake, recording physiological vital signs, and calculating Early Warning Score (EWS).
- **Who Can Access:** Authenticated Nurse with `patients.vitals.record`.
- **What User Sees:** Patient search/registration form; numeric inputs for Systolic/Diastolic BP (mmHg), Heart Rate (bpm), Respiratory Rate (/min), Body Temp (°C/°F), SpO2 (%), Random Blood Sugar (mg/dL).
- **User Action:** Enters measured values (e.g. BP 140/90, Temp 101.4°F, Pulse 98, SpO2 96%), clicks "Calculate EWS & Save Vitals".
- **Input:** `{ "patient_id": "UUID", "systolic_bp": 140, "diastolic_bp": 90, "heart_rate": 98, "temperature": 101.4, "spo2": 96, "blood_sugar": 140 }`.
- **Validation:** Numbers must be within physiological limits (e.g. SpO2 50-100%, Systolic BP 50-260).
- **API:** `POST /api/v1/nurse-portal/vitals`.
- **Backend Action:** Persists vitals record; calculates Early Warning Score; if score >= 5, flags patient as `HIGH_PRIORITY_TRIAGE`.
- **Database Effect:** Inserts `vitals` row; updates appointment triage status.
- **Audit:** Logs `PATIENT_VITALS_RECORDED` with computed EWS score.
- **Success State:** Vitals badge turns green (or red alert if EWS critical); patient prioritized in Doctor queue.
- **Next Action:** Patient instructed to take a seat outside Doctor consultation room.

### 4. FEATURE 2: LAB SAMPLE COLLECTION
- **Purpose:** Acknowledge physical specimen collection (blood, urine, swab) for pending lab orders.
- **Who Can Access:** Authenticated Nurse / Phlebotomist with `labs.sample.collect`.
- **What User Sees:** Pending sample collection list with patient name, token, test name, and tube type (EDTA, Serum, Fluoride).
- **User Action:** Collects specimen, checks patient label barcode, clicks "Mark Sample Collected".
- **Input:** `{ "sample_type": "BLOOD", "collection_notes": "Sample drawn without hemolysis" }`.
- **Validation:** Sample type required.
- **API:** `POST /api/v1/nurse-portal/samples/{id}/collect`.
- **Backend Action:** Transitions lab order status from `PENDING_COLLECTION` to `SAMPLE_COLLECTED`.
- **Database Effect:** Updates `lab_orders.status = 'SAMPLE_COLLECTED'` and timestamps `collected_at`.
- **Audit:** Logs `LAB_SAMPLE_COLLECTED`.
- **Success State:** Order shifts to "Awaiting Lab Processing" column.
- **Next Action:** Specimen transported to PHC lab technician for testing.

### 5. FEATURE 3: VACCINE COLD CHAIN TEMPERATURE LOGGING
- **Purpose:** Record daily morning and evening temperatures of vaccine refrigerators (ILR).
- **Who Can Access:** Authenticated Nurse with `cold_chain.log`.
- **What User Sees:** Registered refrigerator list, current status, last recorded temperature, excursion alert indicator.
- **User Action:** Reads thermometer on ILR #1, inputs `+4.2°C`, selects shift `MORNING`, clicks "Log Temperature".
- **Input:** `{ "equipment_id": "UUID", "temperature_celsius": 4.2, "log_shift": "MORNING" }`.
- **Validation:** Temperature must be valid decimal; required shift (`MORNING` / `EVENING`).
- **API:** `POST /api/v1/nurse-portal/cold-chain/log`.
- **Backend Action:** Persists reading. Checks if outside safe range (+2°C to +8°C). If breached, automatically raises `COLD_CHAIN_EXCURSION` alert.
- **Database Effect:** Inserts `cold_chain_logs` row.
- **Audit:** Logs `COLD_CHAIN_TEMPERATURE_LOGGED`.
- **Success State:** Log displayed in 30-day compliance chart with green checkmark.
- **Next Action:** ILR status verified safe for today's vaccination outreach.

### 6. FORBIDDEN ACTIONS
- Cannot author clinical prescriptions or finalize ICD-10 medical diagnoses.
- Cannot approve inter-facility stock transfers or modify warehouse inventory.

### 7. NOTIFICATIONS
- Alert when an arriving patient has severe symptoms or high triage score.

### 8. AI FEATURES
- **Triage Priority AI Assistant:** Analyzes vital signs and symptoms to compute Early Warning Score and suggest immediate triage escalation.

### 9. HISTORY
- Complete daily intake log and sample collection ledger.

### 10. COMPLETE ROLE JOURNEY
- Nurse checks in shift -> Receives arriving patient -> Takes vitals & logs in system -> EWS calculated normal -> Patient routed to Doctor queue -> Doctor orders blood test -> Nurse collects blood sample in EDTA tube -> Marks collected -> Logs morning refrigerator temp (+4°C) -> Checks out shift.

---

# ROLE 04: PHC IN-CHARGE / FACILITY MANAGER (`PHC_IN_CHARGE`)

### 1. LOGIN FLOW
- **Credential Entry:** In-charge logs in (e.g. `phc_in_charge@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Validates credentials, verifies `PHC_IN_CHARGE` role, scopes to facility `PHC-KOV-001`.
- **Success State:** Navigates to `/facility`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/facility`.
- **Data Fetch:** Calls `GET /api/v1/dashboards/phc`, `GET /api/v1/facility-admin/staff-attendance`, and `GET /api/v1/facility-admin/complaints`.
- **What User Sees:** Operational summary cards (Today's OPD Count, Staff on Duty, Active Grievances, Low Stock Items, Cold Chain Excursions); outreach camp calendar; monthly report generation button.
- **Empty State:** N/A (Standard operational baseline).

### 3. FEATURE 1: STAFF ATTENDANCE OVERSIGHT & ROSTER
- **Purpose:** Monitor attendance compliance, late arrivals, and duty deployments across all doctors, nurses, and lab staff.
- **Who Can Access:** Authenticated In-Charge with `staff.attendance.admin`.
- **What User Sees:** Date range selector, attendance matrix listing each staff member, check-in time, check-out time, duty station (OPD, Ward, Outreach), and attendance status (`PRESENT`, `LATE`, `ON_LEAVE`, `ABSENT`).
- **User Action:** Filters by today's date, reviews absenteeism, clicks staff member to view monthly compliance percentage.
- **API:** `GET /api/v1/facility-admin/staff-attendance?from_date=2026-09-01&to_date=2026-09-29`.
- **Backend Action:** Retrieves attendance logs joined with user profiles for the assigned facility.
- **Audit:** Logs `FACILITY_ATTENDANCE_LEDGER_REVIEWED`.
- **Success State:** Displays clear tabular overview with summary statistics (% Present: 92%).
- **Next Action:** Assign relief staff to duty stations if short-staffed.

### 4. FEATURE 2: PATIENT GRIEVANCE & COMPLAINT REDRESSAL
- **Purpose:** Triage, investigate, and formally resolve complaints submitted by patients.
- **Who Can Access:** Authenticated In-Charge with `facility.complaint.manage`.
- **What User Sees:** List of complaints categorized by status (`OPEN`, `INVESTIGATING`, `RESOLVED`), patient feedback rating, timestamp, and incident description.
- **User Action:** Clicks open grievance, reads details, investigates with pharmacy staff, types resolution remarks: "Additional dispensing counter opened to reduce wait time", changes status to `RESOLVED`.
- **Input:** `{ "status": "RESOLVED", "resolution_notes": "Additional dispensing counter opened." }`.
- **Validation:** Status must be valid enum; resolution notes mandatory (>10 chars).
- **API:** `PATCH /api/v1/facility-admin/complaints/{id}/status`.
- **Backend Action:** Updates complaint status and resolution notes; sends notification to patient portal.
- **Database Effect:** Updates `feedback_complaints` row.
- **Audit:** Logs `FACILITY_COMPLAINT_RESOLVED` with in-charge ID.
- **Success State:** Complaint badge updates to green `RESOLVED` with resolution timestamp.
- **Next Action:** Resolved complaint archived; grievance metrics updated on monthly HMIS report.

### 5. FEATURE 3: MONTHLY HMIS FACILITY OPERATIONAL REPORT
- **Purpose:** Generate aggregated monthly performance indicators for district submission.
- **Who Can Access:** Authenticated In-Charge with `facility.report.view`.
- **What User Sees:** Year/Month selector, pre-compiled statistics on Total OPD Patients, Ante-Natal Care (ANC) Visits, Lab Tests Executed, Prescriptions Dispensed, Cold Chain Breaches, and Resolved Grievances.
- **User Action:** Selects September 2026, reviews computed metrics, clicks "Generate & Sign Report".
- **API:** `GET /api/v1/facility-admin/reports/monthly?year=2026&month=9`.
- **Backend Action:** Aggregates live database records for the month, calculates clinical and supply KPIs.
- **Database Effect:** Records snapshot entry in `facility_reports`.
- **Audit:** Logs `FACILITY_MONTHLY_REPORT_GENERATED`.
- **Success State:** Displays formatted monthly report ready for download/print and transmission to District Health Officer.
- **Next Action:** Report accessible by District Health Officer in district oversight portal.

### 6. FORBIDDEN ACTIONS
- Cannot alter medical charts or clinical conclusions of medical officers.
- Cannot bypass FEFO batch allocation in the pharmacy.
- Cannot modify platform configurations or create platform-level roles.

### 7. NOTIFICATIONS
- Alert on cold chain temperature breach (>8°C) or severe stockout of life-saving medicines.

### 8. AI FEATURES
- Facility KPI Summary Generator: Summarizes monthly operational bottlenecks and suggests staff reallocation plans.

### 9. HISTORY
- Archive of past monthly facility operational reports and resolution records.

### 10. COMPLETE ROLE JOURNEY
- In-charge logs in -> Inspects morning facility dashboard -> Checks staff attendance roster (1 doctor on leave, assigns relief) -> Inspects cold chain logs (normal) -> Reviews patient complaint regarding wait times -> Adds resolution notes -> Generates monthly HMIS report -> Dispatches to DHO.

---

# ROLE 05: PHARMACIST / PHC STOREKEEPER (`PHARMACIST`)

### 1. LOGIN FLOW
- **Credential Entry:** Pharmacist logs in (e.g. `pharmacist@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Validates credentials, verifies `PHARMACIST` role and facility scope.
- **Success State:** Navigates to `/pharmacy/dispense`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/pharmacy/dispense`.
- **Data Fetch:** Calls `GET /api/v1/pharmacist-portal/queue`, `GET /api/v1/inventory`, and `GET /api/v1/inventory/batches/expiring`.
- **What User Sees:** Live prescription dispensing queue; inventory stock search bar; batches expiring in 30 days alert card; "Raise Supply Request" button.
- **Empty State:** "No prescriptions pending dispensing."

### 3. FEATURE 1: PRESCRIPTION DISPENSING WITH AUTOMATED FEFO
- **Purpose:** Review doctor's electronic prescription and dispense pharmaceuticals using First-Expiring-First-Out batch sequence.
- **Who Can Access:** Authenticated Pharmacist with `prescriptions.dispense`.
- **What User Sees:** Patient name, token number, prescribed medicines, required quantity, system-allocated batch number, batch expiry date, available quantity.
- **User Action:** Verifies patient identity, retrieves physical medication from designated shelf matching batch code, clicks "Confirm & Dispense".
- **Input:** `{ "prescription_id": "UUID", "dispensed_items": [{ "medication_id": "UUID", "quantity": 10, "batch_id": "UUID" }] }`.
- **Validation:** Quantity must match prescription; batch must not be expired (`expiry_date > today`); batch stock must be sufficient.
- **API:** `POST /api/v1/prescriptions/{id}/dispense`.
- **Backend Action:** Executes transactional database lock: decrements `inventory_batches.current_quantity`, decrements `inventory_items.quantity_on_hand`, inserts `stock_movements` record (`DISPENSATION`), updates `prescriptions.status = 'DISPENSED'`.
- **Database Effect:** Atomic update to inventory batches and prescription status.
- **Audit:** Logs `PRESCRIPTION_DISPENSED` with batch numbers, quantities, and pharmacist ID.
- **Success State:** Green checkmark: "Prescription #RX-1092 dispensed successfully. Inventory updated."
- **Error State:** If insufficient batch stock (409 Conflict), displays "Selected batch depleted. FEFO engine reallocating alternate batch."
- **Next Action:** Prescription moves to fulfilled list; patient receives SMS/portal notification that medication is dispensed.

### 4. FEATURE 2: REPLENISHMENT SUPPLY REQUEST
- **Purpose:** Request medicine replenishment from District Drug Warehouse when stock approaches reorder level.
- **Who Can Access:** Authenticated Pharmacist with `supply.request.create`.
- **What User Sees:** Low-stock items table with current quantity on hand, minimum reorder threshold, suggested reorder quantity.
- **User Action:** Clicks "Raise Request", selects medication, inputs quantity needed (e.g. 500 tablets Amoxicillin), specifies urgency (`ROUTINE` or `EMERGENCY`), clicks "Submit Request".
- **Input:** `{ "medication_id": "UUID", "requested_quantity": 500, "priority": "ROUTINE", "clinical_justification": "Stock below safety buffer of 50 units" }`.
- **Validation:** Quantity > 0; justification required for EMERGENCY requests.
- **API:** `POST /api/v1/supply-requests`.
- **Backend Action:** Creates supply request in `PENDING_REVIEW` state linked to destination District Drug Depot.
- **Database Effect:** Inserts `supply_requests` row.
- **Audit:** Logs `SUPPLY_REQUEST_RAISED`.
- **Success State:** Banner: "Supply request #SR-401 submitted to District Supply Officer."
- **Next Action:** Request visible in District Supply Officer portal for allocation.

### 5. FEATURE 3: INCOMING TRANSFER RECEIPT VERIFICATION
- **Purpose:** Inspect physical delivery of medicines from warehouse and accept stock into facility inventory.
- **Who Can Access:** Authenticated Pharmacist with `supply.receipt.verify`.
- **What User Sees:** List of incoming transfer shipments with status `DISPATCHED` or `IN_TRANSIT`, manifest details, expected batch numbers, and dispatched quantities.
- **User Action:** Physically inspects delivery boxes, verifies batch numbers and expiration dates match manifest, checks tamper seals, inputs verified quantity, clicks "Acknowledge & Accept Stock".
- **Input:** `{ "verified_quantity": 500, "batch_number": "BAT-2026-X9", "expiry_date": "2027-08-31", "verification_status": "ACCEPTED", "discrepancy_notes": null }`.
- **Validation:** Verified quantity must be entered; verification status must be ACCEPTED, REJECTED, or DISCREPANCY.
- **API:** `POST /api/v1/supply-requests/{id}/receipts/{transfer_id}/verify`.
- **Backend Action:** Increments destination facility inventory items and batches; marks transfer `RECEIVED`; creates `stock_movements` record (`TRANSFER_RECEIPT`).
- **Database Effect:** Atomic update to local inventory balances.
- **Audit:** Logs `TRANSFER_RECEIPT_VERIFIED`.
- **Success State:** Green toast: "500 units credited to facility stock. Transfer completed."
- **Next Action:** Stock immediately available for clinic dispensing.

### 6. FORBIDDEN ACTIONS
- Cannot modify clinical prescriptions or change dosages.
- Cannot approve district redistribution transfers between external health centers.
- Cannot delete inventory movement records.

### 7. NOTIFICATIONS
- Alert on newly arrived prescription from consultation room.
- Alert when an inventory batch reaches within 30 days of expiry.

### 8. AI FEATURES
- **Pharmacy Replenishment Forecast:** Calculates estimated days of stock remaining based on 30-day burn rate.

### 9. HISTORY
- Complete audit trail of all dispensing events, receipt verifications, and physical stock adjustments.

### 10. COMPLETE ROLE JOURNEY
- Pharmacist checks in -> Opens dispensing queue -> Selects waiting patient's prescription -> Reviews FEFO batch allocated -> Picks medication from shelf -> Confirms dispensing -> Stock decrements atomically -> Reviews low stock alert -> Submits replenishment request to district -> Inspects arriving shipment -> Accepts stock.

---

# ROLE 06: DISTRICT HEALTH OFFICER (`DISTRICT_HEALTH_OFFICER`)

### 1. LOGIN FLOW
- **Credential Entry:** DHO logs in (e.g. `dho@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Authenticates credentials, validates `DISTRICT_HEALTH_OFFICER` role, verifies `DISTRICT` scope (`Chengalpattu`).
- **Success State:** Navigates to `/district`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/district`.
- **Data Fetch:** Calls `GET /api/v1/district/dashboard`, `GET /api/v1/governance/actions`, and `GET /api/v1/governance/alerts`.
- **What User Sees:** District health overview cards (Total District OPD Volume, Severe Referrals, Active Health Alerts, Overdue Directives, Supply Impact Notices); PHC operational comparison matrix; interactive map/list of district facilities.
- **Empty State:** N/A (District aggregate view).

### 3. FEATURE 1: PHC COMPARATIVE PERFORMANCE MONITORING
- **Purpose:** Benchmark healthcare service delivery and operational readiness across all district health facilities without exposing individual patient identities.
- **Who Can Access:** Authenticated DHO with `governance.district.view`.
- **What User Sees:** Table of all PHCs in the district with OPD volume, doctor attendance rate, critical stockout status, and referral rate. Facilities flagged as `NEEDS_ATTENTION` highlighted in amber/red.
- **User Action:** Clicks a facility (e.g. "Primary Health Centre Kovalam") to inspect 7-day trend curves of patient footfall, maternal checkups, and disease patterns.
- **API:** `GET /api/v1/district/facilities/{facility_id}`.
- **Backend Action:** Aggregates facility metrics over date range; suppresses all personal patient identifiers.
- **Audit:** Logs `DISTRICT_FACILITY_METRICS_VIEWED`.
- **Success State:** Displays granular comparative charts and trend analysis.
- **Next Action:** Issue administrative action item if facility metrics indicate performance bottlenecks.

### 4. FEATURE 2: ADMINISTRATIVE DIRECTIVES & ACTION ITEMS
- **Purpose:** Issue binding administrative directives to PHC In-Charges with mandatory compliance dates.
- **Who Can Access:** Authenticated DHO with `governance.action.create`.
- **What User Sees:** Active directives board categorized by status (`PENDING`, `IN_PROGRESS`, `RESPONDED`, `CLOSED`).
- **User Action:** Clicks "New Directive", selects target facility ("PHC Kovalam"), enters title: "Deploy additional nurse for fever surveillance", sets priority `HIGH`, sets due date 3 days out, clicks "Issue Directive".
- **Input:** `{ "title": "Deploy additional nurse for fever surveillance", "description": "Spike in viral fever cases requires second triage desk.", "facility_id": "UUID", "priority": "HIGH", "due_at": "2026-10-02T18:00:00Z" }`.
- **Validation:** Title, description, facility, and due date mandatory; due date must be in the future.
- **API:** `POST /api/v1/governance/actions`.
- **Backend Action:** Creates governance action item with status `PENDING`, tags target facility in-charge.
- **Database Effect:** Inserts `governance_actions` row.
- **Audit:** Logs `GOVERNANCE_ACTION_CREATED` with DHO ID.
- **Success State:** Action item appears on district tracking board and triggers alert on target PHC In-Charge portal.
- **Next Action:** Monitor facility compliance response before due date.

### 5. FEATURE 3: HEALTH ALERTS & SUPPLY IMPACT OVERSIGHT
- **Purpose:** Review clinical impact notices shared by District Supply Officer regarding medicine stockouts.
- **Who Can Access:** Authenticated DHO with `supply.impact.read`.
- **What User Sees:** List of supply health impact notifications detailing affected PHCs, depleted medication, estimated affected patient volume, and clinical risk level (`CRITICAL`, `MODERATE`).
- **User Action:** Reviews impact assessment, clicks "Acknowledge Notice", inputs administrative instructions: "Authorize local emergency purchase quota for Oral Rehydration Salts".
- **API:** `POST /api/v1/supply-requests/health-impacts/{id}/acknowledge`.
- **Backend Action:** Updates health impact record with acknowledgment timestamp and DHO instructions.
- **Database Effect:** Updates `supply_health_impacts` row.
- **Audit:** Logs `SUPPLY_HEALTH_IMPACT_ACKNOWLEDGED`.
- **Success State:** Impact notice marked acknowledged; instructions dispatched to District Supply Officer.
- **Next Action:** Coordinate emergency replenishment with DSCO.

### 6. FORBIDDEN ACTIONS
- Cannot view individual citizen identifiable medical records or charts.
- Cannot approve commercial financial tenders (owned by state procurement).
- Cannot issue directives to facilities outside the assigned district.

### 7. NOTIFICATIONS
- High-priority notification on disease outbreak alert or critical medicine stockout affecting >100 patients.

### 8. AI FEATURES
- **District AI Governance Assistant:** Answers questions on district disease incidence, comparative PHC performance, and immunization coverage. Strictly grounded in live database aggregates.

### 9. HISTORY
- Historical archive of completed administrative directives, monthly district health reports, and closed alerts.

### 10. COMPLETE ROLE JOURNEY
- DHO logs in -> Views district dashboard -> Identifies PHC with fever surge and antibiotic stockout -> Reviews DSCO supply impact note -> Acknowledges note -> Issues directive to PHC In-charge to open second triage desk -> Queries AI Assistant for 30-day fever trend -> Generates district health report.

---

# ROLE 07: DISTRICT SUPPLY CHAIN OFFICER (`DISTRICT_SUPPLY_OFFICER`)

### 1. LOGIN FLOW
- **Credential Entry:** DSCO logs in (e.g. `dsco@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Verifies credentials, confirms `DISTRICT_SUPPLY_OFFICER` role, scopes to district warehouse.
- **Success State:** Navigates to `/supply/requests`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/supply/requests`.
- **Data Fetch:** Calls `GET /api/v1/supply-requests`, `GET /api/v1/inventory/transfers`, and `GET /api/v1/supply-requests/health-impacts`.
- **What User Sees:** Pending supply requests table from PHCs; district warehouse stock balances; active inter-facility transfers; AI redistribution recommendations; "Escalate to State" button.
- **Empty State:** "No pending supply requests from facilities."

### 3. FEATURE 1: SUPPLY REQUEST REVIEW & ALLOCATION
- **Purpose:** Review medicine requisitions from PHCs and allocate stock from District Warehouse or surplus clinics.
- **Who Can Access:** Authenticated DSCO with `supply.request.review`.
- **What User Sees:** Requisition details: requesting PHC, medication name, requested quantity, current facility stock, monthly consumption rate, priority badge.
- **User Action:** Clicks request, reviews district warehouse availability (e.g. 2,000 units on hand), approves full allocation of 500 units, clicks "Authorize Transfer Shipment".
- **Input:** `{ "supply_request_id": "UUID", "decision": "APPROVED", "allocated_quantity": 500, "source_facility_id": "DISTRICT_WAREHOUSE_UUID" }`.
- **Validation:** Quantity allocated cannot exceed source available stock; source facility must be in district.
- **API:** `POST /api/v1/supply-requests/{id}/allocate`.
- **Backend Action:** Creates `stock_transfers` record in `APPROVED` status; reserves stock at source facility; updates supply request to `ALLOCATED`.
- **Database Effect:** Inserts `stock_transfers` row; increments `inventory_items.quantity_reserved`.
- **Audit:** Logs `SUPPLY_REQUEST_ALLOCATED` with transfer ID.
- **Success State:** Request status updates to `ALLOCATED`; transfer dispatch slip generated.
- **Next Action:** Warehouse storekeeper dispatches transit shipment.

### 4. FEATURE 2: INTER-FACILITY REDISTRIBUTION REBALANCING
- **Purpose:** Resolve facility stockouts by transferring surplus stock from a nearby PHC rather than waiting for central warehouse replenishment.
- **Who Can Access:** Authenticated DSCO with `supply.allocation.manage`.
- **What User Sees:** Automated redistribution matrix pairing deficit facility (PHC Kovalam: 0 units Amoxicillin) with surplus facility (PHC Kelambakkam: 400 units, 45 days supply).
- **User Action:** Approves transfer of 150 units from PHC Kelambakkam to PHC Kovalam, clicks "Create Redistribution Transfer".
- **Input:** `{ "source_facility_id": "PHC_KEL_UUID", "destination_facility_id": "PHC_KOV_UUID", "medication_id": "UUID", "quantity": 150 }`.
- **Validation:** Quantity cannot exceed source safety stock margin; both facilities must be in district.
- **API:** `POST /api/v1/inventory/transfers`.
- **Backend Action:** Initiates inter-facility transfer in `PENDING_APPROVAL` -> `APPROVED` state.
- **Database Effect:** Inserts `stock_transfers` row.
- **Audit:** Logs `REDISTRIBUTION_TRANSFER_CREATED`.
- **Success State:** Transfer generated; notification dispatched to source facility storekeeper.
- **Next Action:** Track transit delivery.

### 5. FEATURE 3: SHORTAGE ESCALATION TO STATE CENTRAL WAREHOUSE
- **Purpose:** Escalate district-wide medicine stockouts to the State Central Medical Warehouse when district depot has zero buffer stock.
- **Who Can Access:** Authenticated DSCO with `shortages.incident.escalate`.
- **What User Sees:** Shortage incident report card indicating zero stock in district depot and 3 PHCs depleted.
- **User Action:** Clicks "Escalate to State", specifies requested state quota (5,000 units), selects urgency `CRITICAL`, enters clinical risk notes, clicks "Submit Escalation".
- **Input:** `{ "medication_id": "UUID", "requested_quantity": 5000, "priority": "EMERGENCY", "escalation_notes": "District depot stock depleted. Multiple PHC stockouts." }`.
- **API:** `POST /api/v1/supply-requests/{id}/escalate`.
- **Backend Action:** Transitions supply request to `ESCALATED_STATE` level; creates alert on State Supply Manager portal.
- **Database Effect:** Updates `supply_requests.level = 'STATE'`.
- **Audit:** Logs `SHORTAGE_ESCALATED_TO_STATE`.
- **Success State:** Confirmation badge: "Escalated to State Central Medical Warehouse."
- **Next Action:** State Supply Manager reviews and allocates bulk shipment from central buffer.

### 6. FORBIDDEN ACTIONS
- Cannot dispense medications directly to patients.
- Cannot issue commercial purchase orders directly to pharmaceutical companies.
- Cannot reallocate stock from facilities outside the assigned district.

### 7. NOTIFICATIONS
- Alert when a PHC reports a critical zero-stock stockout of life-saving drugs.

### 8. AI FEATURES
- **Predictive AI Consumption Forecast:** Computes 30/60/90-day medicine consumption trends and disruption risk scores across district facilities.

### 9. HISTORY
- Searchable ledger of all supply requests, transfer approvals, and dispatch manifests.

### 10. COMPLETE ROLE JOURNEY
- DSCO logs in -> Reviews pending requests -> PHC Kovalam urgently needs Amoxicillin -> District warehouse has low stock -> DSCO triggers redistribution from surplus PHC Kelambakkam -> Approves transfer -> Notifies DHO of temporary supply impact -> Escalate remaining district deficit to State Warehouse.

---

# ROLE 08: DISTRICT EMERGENCY COORDINATOR (`DISTRICT_EMERGENCY_COORDINATOR`)

### 1. LOGIN FLOW
- **Credential Entry:** DEC logs in (e.g. `dec@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Validates credentials, verifies `DISTRICT_EMERGENCY_COORDINATOR` role, scopes to district.
- **Success State:** Navigates to `/emergency`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/emergency`.
- **Data Fetch:** Calls `GET /api/v1/emergencies/dashboard` and `GET /api/v1/emergencies`.
- **What User Sees:** Active emergency command center; live incident count by severity (`CRITICAL`, `MAJOR`, `MODERATE`); affected PHC count; deployed medical tasks board; "Declare Incident" button.
- **Empty State:** "No active emergency incidents in district. All operations normal."

### 3. FEATURE 1: EMERGENCY INCIDENT LIFECYCLE MANAGEMENT
- **Purpose:** Formally declare, categorize, monitor, and resolve public health disaster incidents.
- **Who Can Access:** Authenticated DEC with `emergency.incident.manage`.
- **What User Sees:** Incident declaration form: Title, Category (Epidemic, Cyclone/Flood, Mass Casualty, Cold Chain Failure), Severity (`CRITICAL`, `MAJOR`, `MODERATE`), geographic zone, description.
- **User Action:** Enters details for "Flood-Induced Diarrheal Outbreak", selects severity `CRITICAL`, attaches affected PHCs, clicks "Declare Emergency".
- **Input:** `{ "title": "Flood-Induced Diarrheal Outbreak", "category": "EPIDEMIC", "severity": "CRITICAL", "description": "Contaminated drinking water in 3 coastal villages.", "affected_facility_ids": ["UUID1", "UUID2"] }`.
- **Validation:** Title, category, severity, and at least one affected facility mandatory.
- **API:** `POST /api/v1/emergencies`.
- **Backend Action:** Creates emergency incident record with status `ACTIVE`; links affected facilities; broadcasts emergency alert to district health portals.
- **Database Effect:** Inserts `emergency_incidents` and `emergency_affected_facilities` rows.
- **Audit:** Logs `EMERGENCY_INCIDENT_DECLARED` with DEC ID.
- **Success State:** Red banner flashes on district command center; incident command tracking workspace activated.
- **Next Action:** Assign emergency response tasks to medical teams.

### 4. FEATURE 2: EMERGENCY TASK DISPATCH & TRACKING
- **Purpose:** Assign rapid response missions to medical teams, doctors, and relief workers.
- **Who Can Access:** Authenticated DEC with `emergency.incident.manage`.
- **What User Sees:** Incident task board with columns (`ASSIGNED`, `IN_PROGRESS`, `COMPLETED`); task creation modal.
- **User Action:** Clicks "Add Task", specifies "Deploy Mobile Medical Unit with 1,000 ORS packets to Kovalam Relief Camp", assigns to Dr. Kumar, sets priority `CRITICAL`, clicks "Dispatch Task".
- **Input:** `{ "incident_id": "UUID", "title": "Deploy Mobile Medical Unit", "assigned_to_user_id": "UUID", "priority": "CRITICAL", "due_at": "2026-09-30T14:00:00Z" }`.
- **API:** `POST /api/v1/emergencies/{id}/tasks`.
- **Backend Action:** Persists task, notifies assigned healthcare provider on their portal.
- **Database Effect:** Inserts `emergency_tasks` row.
- **Audit:** Logs `EMERGENCY_TASK_DISPATCHED`.
- **Success State:** Task card appears on live emergency board.
- **Next Action:** Track real-time milestone updates from field team.

### 5. FEATURE 3: RAPID RESOURCE MOBILIZATION
- **Purpose:** Expedite emergency requisitions for trauma kits, antivenom, vaccines, and extra ambulances.
- **Who Can Access:** Authenticated DEC with `emergency.incident.manage`.
- **What User Sees:** Emergency resource request form linked to active incident.
- **User Action:** Selects resource type `MEDICINE_KIT`, inputs quantity `500 ORS + IV Fluids`, specifies target relief post, clicks "Request Emergency Mobilization".
- **API:** `POST /api/v1/emergencies/{id}/resources`.
- **Backend Action:** Routes high-priority emergency supply request directly to District Supply Officer and State Supply Manager.
- **Database Effect:** Inserts `emergency_resource_requests` row.
- **Audit:** Logs `EMERGENCY_RESOURCE_REQUESTED`.
- **Success State:** Status badge: `MOBILIZATION_APPROVED` - Shipments prioritized over routine orders.
- **Next Action:** Verify field arrival.

### 6. FORBIDDEN ACTIONS
- Cannot alter routine clinic consultation charts or modify everyday pharmacy pricing.
- Cannot declare emergencies in other districts without state-level authorization.

### 7. NOTIFICATIONS
- High-priority audible and visual alerts when an emergency incident severity escalates or an emergency task is delayed.

### 8. AI FEATURES
- Emergency Situation Briefing: Grounded summary of affected population estimates, hospital bed availability, and resource burn rates.

### 9. HISTORY
- Post-incident incident resolution logs, after-action reviews, and archive of resolved disasters.

### 10. COMPLETE ROLE JOURNEY
- Flood reported -> DEC logs in -> Declares "Flood Diarrheal Outbreak" incident -> Attaches affected PHCs -> Dispatches mobile medical unit task -> Requests 500 IV fluid emergency kits -> Monitors task completion -> Field reports outbreak contained -> DEC formally marks incident `RESOLVED`.

---

# ROLE 09: STATE HEALTH ADMINISTRATOR (`STATE_HEALTH_ADMIN`)

### 1. LOGIN FLOW
- **Credential Entry:** State Admin logs in (e.g. `state_admin@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Authenticates credentials, validates `STATE_HEALTH_ADMIN` role, confirms `STATE` scope (`Tamil Nadu`).
- **Success State:** Navigates to `/state`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/state`.
- **Data Fetch:** Calls `GET /api/v1/state/dashboard`, `GET /api/v1/governance/approvals`, and `GET /api/v1/governance/schemes`.
- **What User Sees:** Statewide health cockpit; district-by-district performance rankings; pending executive approvals counter; state health mission scheme completion rates; formal monthly reports awaiting sign-off.
- **Empty State:** N/A (State aggregate view).

### 3. FEATURE 1: EXECUTIVE APPROVALS & DECISIONS
- **Purpose:** Formally approve or reject high-value financial procurement, emergency quotas, and cross-district resource reallocations.
- **Who Can Access:** Authenticated State Admin with `governance.approval.decide`.
- **What User Sees:** Approvals inbox with requesting district, approval type (Emergency Procurement, Inter-District Transfer, Infrastructure Budget), requested amount/quantity, and justification.
- **User Action:** Opens high-priority approval request (#APP-902), inspects DHO notes, clicks "Approve Request", enters executive authorization code.
- **Input:** `{ "approval_id": "UUID", "decision": "APPROVED", "remarks": "Approved under State Disaster Relief Fund quota." }`.
- **Validation:** Decision must be `APPROVED` or `REJECTED`; remarks required for decisions.
- **API:** `POST /api/v1/governance/approvals/{id}/decision`.
- **Backend Action:** Atomically transitions approval status; unblocks downstream procurement or transfer workflow.
- **Database Effect:** Updates `approval_requests` row with decision, timestamp, and actor ID.
- **Audit:** Logs `GOVERNANCE_APPROVAL_DECIDED`.
- **Success State:** Approval moves to "Approved Decisions" ledger; notification dispatched to requesting district.
- **Next Action:** State Supply Manager executes the approved consignment.

### 4. FEATURE 2: STATE HEALTH SCHEMES TARGET CONFIGURATION
- **Purpose:** Manage flagship health schemes (e.g. Maternal Health Mission, Non-Communicable Disease Screening) and assign district target quotas.
- **Who Can Access:** Authenticated State Admin with `governance.scheme.manage`.
- **What User Sees:** Active schemes table with state target, achieved percentage, and district breakdown.
- **User Action:** Clicks "Configure Scheme", creates "Makkalai Thedi Maruthuvam (Doorstep Healthcare)", sets statewide screening target of 100,000 citizens, allocates district quotas, clicks "Publish Scheme".
- **Input:** `{ "name": "Makkalai Thedi Maruthuvam", "description": "Doorstep NCD screening and medicine delivery", "target_metric": "SCREENED_CITIZENS", "state_target": 100000, "district_quotas": [{ "district": "Chengalpattu", "quota": 15000 }] }`.
- **API:** `POST /api/v1/governance/schemes`.
- **Backend Action:** Persists scheme definition and district target quotas; visible across all district health portals.
- **Database Effect:** Inserts `governance_schemes` and `governance_scheme_targets` rows.
- **Audit:** Logs `GOVERNANCE_SCHEME_CREATED`.
- **Success State:** Scheme active on statewide monitoring cockpit.
- **Next Action:** Monitor real-time screening submissions from field staff.

### 5. FEATURE 3: FORMAL GOVERNANCE REPORT REVIEW & SIGN-OFF
- **Purpose:** Review, annotate, and officially sign off on monthly statewide health administration reports.
- **Who Can Access:** Authenticated State Admin with `governance.report.review`.
- **What User Sees:** Submitted monthly reports from DHOs and Public Health Analysts awaiting review.
- **User Action:** Reviews epidemiological findings, types executive remarks, clicks "Sign & Endorse Report".
- **Input:** `{ "report_id": "UUID", "review_status": "APPROVED", "remarks": "Excellent progress on fever containment." }`.
- **API:** `POST /api/v1/governance/reports/{id}/review`.
- **Backend Action:** Marks report `APPROVED` with digital provenance hash; publishes to National Health Authority portal.
- **Database Effect:** Updates `governance_reports` row.
- **Audit:** Logs `GOVERNANCE_REPORT_REVIEWED`.
- **Success State:** Report archived and transmitted to central national database.
- **Next Action:** Report available on National Health Authority cockpit.

### 6. FORBIDDEN ACTIONS
- Cannot access individual citizen identifiable medical charts.
- Cannot perform physical warehouse inventory receipts or dispatches.
- Cannot modify records of other states.

### 7. NOTIFICATIONS
- Executive alert on emergency disaster declaration or critical state-level stockout.

### 8. AI FEATURES
- **State AI Governance Assistant:** Macro-level trend synthesis across districts for policy decision support.

### 9. HISTORY
- Permanent archive of executive decisions, approved reports, and scheme milestones.

### 10. COMPLETE ROLE JOURNEY
- State Admin logs in -> Reviews statewide health metrics -> Chengalpattu district has emergency request for disaster buffer stock -> Admin reviews and approves -> Configures new NCD screening scheme targets -> Reviews and endorses monthly public health report for MoHFW.

---

# ROLE 10: STATE SUPPLY CHAIN / WAREHOUSE MANAGER (`STATE_SUPPLY_MANAGER`)

### 1. LOGIN FLOW
- **Credential Entry:** State Supply Manager logs in (e.g. `state_supply@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Validates credentials, verifies `STATE_SUPPLY_MANAGER` role, confirms `STATE` warehouse scope.
- **Success State:** Navigates to `/supply`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/supply`.
- **Data Fetch:** Calls `GET /api/v1/supply-requests/state/dashboard`, `GET /api/v1/procurement/orders`, and `GET /api/v1/shipments`.
- **What User Sees:** Central warehouse stock totals; emergency buffer reserves; escalated district requests; active commercial Purchase Orders; transit consignments tracker; "New Purchase Order" button.
- **Empty State:** N/A (Central warehouse operational view).

### 3. FEATURE 1: ESCALATED DISTRICT REQUEST ALLOCATION
- **Purpose:** Allocate bulk medicine consignments from State Central Warehouse to replenish District Drug Depots.
- **Who Can Access:** Authenticated State Supply Manager with `supply.allocation.manage`.
- **What User Sees:** Table of escalated requests from District Supply Officers with requested quantity, stockout severity, and central stockpile balance.
- **User Action:** Selects escalated request from Chengalpattu for 5,000 units Paracetamol, confirms central stock availability (20,000 units on hand), authorizes allocation.
- **Input:** `{ "supply_request_id": "UUID", "allocated_quantity": 5000, "source_warehouse_id": "STATE_CENTRAL_WH_UUID" }`.
- **API:** `POST /api/v1/supply-requests/{id}/allocate`.
- **Backend Action:** Deducts central stockpile, generates shipment consignment, updates request status to `DISPATCHED`.
- **Database Effect:** Updates `inventory_batches` and creates `shipments` row.
- **Audit:** Logs `STATE_SUPPLY_ALLOCATED`.
- **Success State:** Consignment manifest generated; transit tracking activated.
- **Next Action:** Assign carrier and monitor transit milestones.

### 4. FEATURE 2: COMMERCIAL BULK PURCHASE ORDERS (PO)
- **Purpose:** Issue purchase orders to registered pharmaceutical manufacturers to replenish central warehouse reserves.
- **Who Can Access:** Authenticated State Supply Manager with `procurement.order.create`.
- **What User Sees:** Supplier directory, approved contracts, current item balances, PO drafting form.
- **User Action:** Selects supplier ("Tamil Nadu Medical Services Corp / PharmaVendor"), adds line items (50,000 vials Insulin, 100,000 tabs Metformin), enters delivery deadline, clicks "Issue Purchase Order".
- **Input:** `{ "supplier_id": "UUID", "expected_delivery_date": "2026-11-15", "items": [{ "medication_id": "UUID", "quantity": 50000, "unit_price": 45.0 }] }`.
- **Validation:** Supplier must be active; quantity > 0; delivery date must be in the future.
- **API:** `POST /api/v1/procurement/orders`.
- **Backend Action:** Creates PO in `PENDING_APPROVAL` status (enforces Segregation of Duties).
- **Database Effect:** Inserts `procurement_orders` and `procurement_order_items` rows.
- **Audit:** Logs `PROCUREMENT_ORDER_CREATED`.
- **Success State:** PO generated and queued for executive sign-off.
- **Next Action:** Transmitted to supplier upon executive approval.

### 5. FEATURE 3: LOGISTICS CONSIGNMENT & SHIPMENT TRACKING
- **Purpose:** Monitor in-transit pharmaceutical trucks, temperature integrity, and milestone events.
- **Who Can Access:** Authenticated State Supply Manager with `shipments.update`.
- **What User Sees:** Active shipments map/table with tracking ID, carrier, source warehouse, destination district depot, status (`IN_TRANSIT`, `DELAYED`, `DELIVERED`).
- **User Action:** Clicks shipment #SH-771, reviews logged GPS checkpoints, records milestone "Arrived at District Depot Checkpost".
- **Input:** `{ "shipment_id": "UUID", "milestone": "IN_TRANSIT", "location": "Chengalpattu Toll Plaza", "temperature_reading": 5.1 }`.
- **API:** `POST /api/v1/shipments/{id}/events`.
- **Backend Action:** Logs shipment event; validates cold chain reading within tolerance (+2°C to +8°C).
- **Database Effect:** Inserts `shipment_events` row.
- **Audit:** Logs `SHIPMENT_MILESTONE_LOGGED`.
- **Success State:** Timeline updated with timestamp and temperature verification.
- **Next Action:** District storekeeper performs physical receipt verification upon delivery.

### 6. FORBIDDEN ACTIONS
- Cannot author clinical prescriptions or examine patients.
- Cannot approve purchase orders authored by themselves (Segregation of Duties strictly enforced).
- Cannot access warehouses in other states.

### 7. NOTIFICATIONS
- Alert when central warehouse buffer stock drops below 30 days of statewide supply.

### 8. AI FEATURES
- Statewide Replenishment Risk Analyzer: Simulates 60-day stockout probabilities across all 38 districts.

### 9. HISTORY
- Master ledger of all supplier purchase orders, central stock movements, and logistics delivery manifests.

### 10. COMPLETE ROLE JOURNEY
- State Supply Manager logs in -> Inspects central inventory -> Reviews escalated district shortage from Chengalpattu -> Allocates 5,000 units from central buffer -> Dispatches refrigerated transport shipment -> Drafts bulk purchase order to pharma manufacturer -> Monitors shipment milestone.

---

# ROLE 11: STATE PUBLIC HEALTH ANALYST (`STATE_PUBLIC_HEALTH_ANALYST`)

### 1. LOGIN FLOW
- **Credential Entry:** Analyst logs in (e.g. `analyst@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Validates credentials, verifies `STATE_PUBLIC_HEALTH_ANALYST` role, scopes to state surveillance registers.
- **Success State:** Navigates to `/analytics`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/analytics`.
- **Data Fetch:** Calls `GET /api/v1/public-health/dashboard`, `GET /api/v1/public-health/indicators`, and `GET /api/v1/public-health/data-quality`.
- **What User Sees:** Epidemiological surveillance trends (dengue, malaria, acute diarrheal disease, maternal health); data quality scorecards; active analysis modeling jobs; "Run Analysis" button.
- **Empty State:** N/A (Statistical aggregates view).

### 3. FEATURE 1: SURVEILLANCE AGGREGATES & DATA QUALITY AUDIT
- **Purpose:** Audit district health submissions for missing data, anomalous reporting spikes, or statistical outliers.
- **Who Can Access:** Authenticated Analyst with `analytics.data_quality.manage`.
- **What User Sees:** Data quality audit matrix flagging reporting anomalies (e.g. PHC reporting sudden 500% jump in respiratory cases or missing weekly reports).
- **User Action:** Inspects flagged issue (#DQ-104), reviews historical baseline, issues Data Quality Correction Notice to District Health Officer.
- **Input:** `{ "issue_id": "UUID", "action": "REQUEST_CLARIFICATION", "notes": "Reporting spike exceeds 3 standard deviations from 5-year seasonal baseline." }`.
- **API:** `POST /api/v1/public-health/data-quality/{issue_id}/action`.
- **Backend Action:** Logs data quality action, updates issue status to `UNDER_INVESTIGATION`, dispatches notification to district.
- **Database Effect:** Updates `data_quality_issues` row.
- **Audit:** Logs `DATA_QUALITY_ACTION_TAKEN`.
- **Success State:** Issue tagged as investigating; tracked in audit log.
- **Next Action:** Re-audit once district submits reconciled data.

### 4. FEATURE 2: AUTOMATED STATISTICAL ANALYSIS JOBS
- **Purpose:** Execute statistical trend models and epidemiological outbreak forecasting.
- **Who Can Access:** Authenticated Analyst with `analytics.insight.review`.
- **What User Sees:** Job launcher with model options (ARIMA Time Series, Spatial Clustering, Seasonal Decomposition), parameter inputs, recent job history.
- **User Action:** Selects "Spatial Clustering - Viral Fever", chooses timeframe (Last 90 Days), clicks "Execute Analysis Job".
- **Input:** `{ "analysis_type": "SPATIAL_CLUSTER", "indicator_code": "VIRAL_FEVER", "timeframe_days": 90 }`.
- **API:** `POST /api/v1/public-health/analysis/run`.
- **Backend Action:** Spawns asynchronous analysis task; computes cluster centroids and z-scores; stores output artifact.
- **Database Effect:** Inserts `ai_analysis_jobs` row.
- **Audit:** Logs `ANALYTICS_JOB_EXECUTED`.
- **Success State:** Displays computed risk map highlighting high-risk geographic clusters in Chengalpattu district.
- **Next Action:** Formulate scientific policy insight based on findings.

### 5. FEATURE 3: SCIENTIFIC INSIGHTS & POLICY ADVISORIES
- **Purpose:** Publish data-backed policy recommendations for the State Health Administrator and DHOs.
- **Who Can Access:** Authenticated Analyst with `analytics.insight.review`.
- **What User Sees:** Published insights feed; authoring workspace.
- **User Action:** Clicks "Publish Insight", enters title: "Pre-Monsoon Vector-Borne Disease Advisory", attaches cluster analysis results, recommends targeted fogging and antimalarial pre-positioning, clicks "Publish".
- **Input:** `{ "title": "Pre-Monsoon Vector-Borne Disease Advisory", "category": "EPIDEMIOLOGY", "summary": "Spatial cluster indicates high risk in 3 coastal blocks.", "recommendations": "Pre-position antimalarials and intensify larval source reduction." }`.
- **API:** `POST /api/v1/public-health/insights`.
- **Backend Action:** Persists insight and links to relevant indicators; broadcasts to State Health Admin and DHO dashboards.
- **Database Effect:** Inserts `ai_insights` row.
- **Audit:** Logs `PUBLIC_HEALTH_INSIGHT_PUBLISHED`.
- **Success State:** Insight published and visible in governance decision cockpit.
- **Next Action:** State Health Admin incorporates advisory into state action directives.

### 6. FORBIDDEN ACTIONS
- Cannot access raw individual citizen identifiable medical records.
- Cannot issue binding executive directives (held by State Health Administrator).
- Cannot adjust physical inventory or dispense drugs.

### 7. NOTIFICATIONS
- Alert on automated detection of an epidemiological outbreak threshold breach.

### 8. AI FEATURES
- Automated Epidemiological Anomaly Detector: Identifies non-linear spikes in syndromic reporting.

### 9. HISTORY
- Repository of historical surveillance aggregates, validation logs, and published epidemiological papers.

### 10. COMPLETE ROLE JOURNEY
- Analyst logs in -> Inspects statewide disease surveillance trends -> Identifies reporting anomaly in coastal block -> Issues data quality clarification -> Launches spatial clustering model -> Detects pre-monsoon dengue cluster -> Publishes scientific policy advisory to State Health Admin.

---

# ROLE 12: NATIONAL HEALTH AUTHORITY (`NATIONAL_HEALTH_AUTHORITY`)

### 1. LOGIN FLOW
- **Credential Entry:** National Authority logs in (e.g. `nha@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Authenticates credentials, validates `NATIONAL_HEALTH_AUTHORITY` role, verifies `GLOBAL` scope.
- **Success State:** Navigates to `/national`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/national`.
- **Data Fetch:** Calls `GET /api/v1/national/dashboard`, `GET /api/v1/governance/schemes`, and `GET /api/v1/governance/reports`.
- **What User Sees:** Pan-India health dashboard; comparative state health indices; national disease surveillance map; flagship mission progress curves; national policy briefing generator.
- **Empty State:** N/A (Pan-India macro view).

### 3. FEATURE 1: PAN-INDIA COMPARATIVE HEALTH COCKPIT
- **Purpose:** National oversight of state-level healthcare delivery, disease burdens, and operational readiness.
- **Who Can Access:** Authenticated National Authority with `governance.national.view`.
- **What User Sees:** Interactive India map with state color coding by health index; comparative table (Tamil Nadu, Kerala, Maharashtra, etc.) showing OPD volume per capita, institutional delivery rate, and emergency supply readiness.
- **User Action:** Clicks "Tamil Nadu", expands aggregate statewide indicators, reviews comparative trends.
- **API:** `GET /api/v1/national/dashboard`.
- **Backend Action:** Aggregates state-level summaries from database; strictly respects state autonomy while exposing federated metrics.
- **Audit:** Logs `NATIONAL_HEALTH_COCKPIT_ACCESSED`.
- **Success State:** Renders macro trend graphs and state-by-state ranking matrix.
- **Next Action:** Identify states requiring central technical or resource assistance.

### 4. FEATURE 2: NATIONAL HEALTH MISSION TARGET MONITORING
- **Purpose:** Monitor progress of national health flagship schemes across all participating states.
- **Who Can Access:** Authenticated National Authority with `governance.scheme.read`.
- **What User Sees:** National health mission schemes list (e.g. National Tuberculosis Elimination Program, Ayushman Bharat PHC Strengthening), national target versus actual achievement.
- **User Action:** Reviews state-wise compliance, identifies lagging regions, logs central coordination remarks.
- **API:** `GET /api/v1/governance/schemes`.
- **Backend Action:** Returns active national schemes and linked state target achievements.
- **Audit:** Logs `NATIONAL_SCHEME_TARGETS_REVIEWED`.
- **Success State:** Displays comparative progress bars with national target benchmark.
- **Next Action:** Issue central coordination advisory to state health secretaries.

### 5. FEATURE 3: INTER-STATE RESOURCE COORDINATION
- **Purpose:** Facilitate emergency resource sharing between states during national epidemics or natural disasters.
- **Who Can Access:** Authenticated National Authority with `governance.action.create`.
- **What User Sees:** Inter-state emergency coordination board.
- **User Action:** Initiates coordination directive to transfer surplus antivenom/vaccine buffer stocks from State A to flood-affected State B.
- **Input:** `{ "title": "Inter-State Emergency Buffer Mobilization", "description": "Mobilize 10,000 vials antivenom to flood zone.", "priority": "CRITICAL" }`.
- **API:** `POST /api/v1/governance/actions`.
- **Backend Action:** Broadcasts central coordination directive to both State Health Administrators.
- **Database Effect:** Inserts `governance_actions` row at `NATIONAL` level.
- **Audit:** Logs `NATIONAL_COORDINATION_ACTION_CREATED`.
- **Success State:** Directive logged on national coordination registry.
- **Next Action:** State supply managers execute physical logistics transfer.

### 6. FORBIDDEN ACTIONS
- Cannot access individual citizen identifiable clinical charts.
- Cannot unilaterally override state procurement contracts.
- Cannot manage technical server parameters or modify user passwords (held by Super Admin).

### 7. NOTIFICATIONS
- Executive alert on multi-state disease outbreaks or cross-border public health threats.

### 8. AI FEATURES
- **National AI Assistant:** Synthesizes multi-state health trends, disease trajectories, and supply chain readiness indicators.

### 9. HISTORY
- Central archive of national health policy reports, annual reviews, and inter-state coordination agreements.

### 10. COMPLETE ROLE JOURNEY
- National Authority logs in -> Reviews Pan-India health index -> Monitors national TB elimination progress by state -> Reviews state monthly health reports -> Coordinates inter-state emergency medicine buffer transfer -> Generates national executive health summary.

---

# ROLE 13: NATIONAL PLATFORM ADMINISTRATOR / SUPER ADMIN (`SUPER_ADMIN`)

### 1. LOGIN FLOW
- **Credential Entry:** Super Admin logs in (e.g. `super_admin@demo.smarthealth.local` / `Demo@Health2026`).
- **Backend Action:** Authenticates credentials, validates `SUPER_ADMIN` role, verifies `GLOBAL` technical platform scope.
- **Success State:** Navigates to `/platform`.

### 2. DASHBOARD FLOW
- **Page Load:** Mounts `/platform`.
- **Data Fetch:** Calls `GET /api/v1/platform/dashboard` and `GET /api/v1/platform/security-events`.
- **What User Sees:** Technical system health telemetry (Database connection status, query latency ms, active user sessions, background worker health); total user and role counts; security event stream; quick action buttons ("Provision User", "Manage RBAC", "Facility Directory", "Audit Logs").
- **Empty State:** N/A (System telemetry view).

### 3. FEATURE 1: USER IDENTITY PROVISIONING & RBAC ASSIGNMENT
- **Purpose:** Provision new staff accounts and assign scoped roles (`GLOBAL`, `STATE`, `DISTRICT`, `FACILITY`).
- **Who Can Access:** Authenticated Super Admin with `identity.user.create` and `identity.role.assign`.
- **What User Sees:** Searchable staff directory; filter by facility/role; "Provision New User" modal.
- **User Action:** Clicks "Provision User", enters full name ("Dr. Aruna Devi"), email, selects role `DOCTOR`, assigns facility `PHC Kovalam`, assigns scope `FACILITY`, clicks "Create User & Generate Temporary Password".
- **Input:** `{ "name": "Dr. Aruna Devi", "email": "aruna.devi@phc.tn.gov.in", "role_id": "UUID", "facility_id": "UUID", "scope_level": "FACILITY" }`.
- **Validation:** Unique email; valid role and facility UUIDs; scope level must match role requirements.
- **API:** `POST /api/v1/users` followed by `POST /api/v1/users/{id}/roles`.
- **Backend Action:** Creates user row with hashed password; creates `user_roles` scoped junction row.
- **Database Effect:** Inserts `users` and `user_roles` rows.
- **Audit:** Logs `USER_CREATED` and `USER_ROLE_ASSIGNED` with Super Admin ID.
- **Success State:** User appears in staff directory with status `ACTIVE`; credentials dispatched securely.
- **Next Action:** User logs in and performs first-time password rotation.

### 4. FEATURE 2: DYNAMIC ROLE & PERMISSION CATALOGUE MANAGEMENT
- **Purpose:** Configure dynamic roles and toggle atomic database-backed permissions (`module.resource.action`).
- **Who Can Access:** Authenticated Super Admin with `identity.role.manage`.
- **What User Sees:** Dynamic roles list (System and Custom); permission catalog organized by module (Identity, Healthcare, Pharmacy, Supply Chain, Governance, Analytics).
- **User Action:** Inspects role, toggles specific permission (e.g. grants `emergency.incident.report` to a custom role), clicks "Save Role Policy".
- **Input:** `{ "role_id": "UUID", "permission_ids": ["UUID1", "UUID2"] }`.
- **API:** `POST /api/v1/roles/{id}/permissions`.
- **Backend Action:** Synchronizes `role_permissions` join table in database; active user sessions immediately inherit updated permission tree upon next token verification.
- **Database Effect:** Inserts/deletes `role_permissions` rows.
- **Audit:** Logs `ROLE_PERMISSIONS_ASSIGNED`.
- **Success State:** Success toast: "Role permissions synchronized across active cluster."
- **Next Action:** Role members gain immediate authorized access to newly granted features.

### 5. FEATURE 3: IMMUTABLE SECURITY AUDIT LOG EXPLORER
- **Purpose:** Search and inspect tamper-evident audit logs with complete actor provenance and forensic details.
- **Who Can Access:** Authenticated Super Admin with `audit.log.read`.
- **What User Sees:** Audit log explorer with filters (Action Type, Actor User ID, Facility ID, Date Range, Status); table displaying Timestamp, Action, Actor, IP Address, Resource, Status (`SUCCESS` / `FAILED`).
- **User Action:** Filters by `AUTH_LOGIN_FAILED` over the last 24 hours, clicks an event row to inspect full JSON metadata payload and user agent string.
- **API:** `GET /api/v1/audit-logs?action=AUTH_LOGIN_FAILED&limit=50`.
- **Backend Action:** Queries immutable `audit_logs` table; enforces strict read-only access (no DELETE/UPDATE endpoints exist).
- **Audit:** Logs `AUDIT_LOGS_SEARCHED`.
- **Success State:** Renders paginated forensic log entries.
- **Next Action:** Take security mitigation if unauthorized brute-force patterns detected.

### 6. FORBIDDEN ACTIONS
- **Strict Segregation of Duties:** Cannot author medical diagnoses, conduct consultations, or write prescriptions.
- Cannot dispense medications or execute commercial procurement transactions.
- Cannot delete or modify security audit log records (append-only table).

### 7. NOTIFICATIONS
- Critical security alerts on repeated failed login thresholds, unauthorized privilege escalation attempts, or database connection latency spikes.

### 8. AI FEATURES
- Security Anomaly Briefing: Summarizes failed login clusters and geo-IP telemetry anomalies.

### 9. HISTORY
- Permanent, immutable transaction history spanning all platform users and administrative interventions.

### 10. COMPLETE ROLE JOURNEY
- Super Admin logs in -> Reviews system health and database latency (normal: 2ms) -> Inspects security telemetry -> Provisions new Medical Officer account -> Assigns DOCTOR role scoped to PHC Kovalam -> Audits recent role assignment in immutable audit explorer -> Logs out.
