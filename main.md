# SMART HEALTH & SUPPLY CHAIN RESILIENCE



## Master Consolidated Requirements



> **Purpose:** Single master Markdown specification consolidating all 13 uploaded role requirements.

> **Coverage:** Patient through National Platform Administrator / Super Admin.

> **Deduplication:** Repeated cross-role requirements are consolidated once. Role-specific requirements remain in their respective sections.

> **Source fidelity:** This document is based on the uploaded role specifications; it does not intentionally replace their requirements with unrelated assumptions.



## Table of Contents



1. Project Context and Role Structure

2. Consolidated Cross-Role Implementation Requirements

3. Role 01 — Patient

4. Role 02 — Doctor / Medical Officer

5. Role 03 — Nurse / Healthcare Staff

6. Role 04 — PHC In-charge / Facility Manager

7. Role 05 — Pharmacist / PHC Storekeeper

8. Role 06 — District Health Officer (DHO)

9. Role 07 — District Supply Chain Officer

10. Role 08 — District Emergency Coordinator

11. Role 09 — State Health Administrator

12. Role 10 — State Supply Chain / Warehouse Manager

13. Role 11 — State Public Health Analyst

14. Role 12 — National Health Authority / Central Administrator

15. Role 13 — National Platform Administrator / Super Admin

16. Source Coverage and Consolidation Notes



# 1. PROJECT CONTEXT AND ROLE STRUCTURE



The project is **Smart Health & Supply Chain Resilience**, an AI-powered, mobile-first PWA for India's Primary Health Centre (PHC) network and its district, state, national, and platform administration layers.



## 1.1 Agreed 13-Role Structure



| # | Role | Level / Scope | Primary Purpose |
|---|---|---|---|
| 1 | Patient | PHC / public-facing | Access healthcare services and patient-facing wellness features. |
| 2 | Doctor / Medical Officer | PHC | Clinical consultation, prescriptions, assigned patient care, attendance, emergency response. |
| 3 | Nurse / Healthcare Staff | PHC | Nursing operations, patient preparation, tests/observations, reports, beds, tasks, attendance. |
| 4 | PHC In-charge / Facility Manager | PHC | Facility administration, supervision, coordination, readiness, operational reporting. |
| 5 | Pharmacist / PHC Storekeeper | PHC | Pharmacy operations, dispensing, inventory, batches, expiry, replenishment. |
| 6 | District Health Officer (DHO) | District | District health administration and oversight. |
| 7 | District Supply Chain Officer | District | District medicine and essential healthcare supply chain. |
| 8 | District Emergency Coordinator | District | District emergency response coordination. |
| 9 | State Health Administrator | State | State health administration, monitoring, coordination, oversight. |
| 10 | State Supply Chain / Warehouse Manager | State | State warehouse and supply-chain operations. |
| 11 | State Public Health Analyst | State | Public-health analytics, trends, data quality, analytical reporting. |
| 12 | National Health Authority / Central Administrator | National | National health/supply-chain oversight and coordination. |
| 13 | National Platform Administrator / Super Admin | Platform | Technical/platform authority, security, configuration, RBAC, audit, reliability. |

**Administrative/data flow:** National → State → District → PHC.  
**Technical authority:** Role 13 is a separate platform authority and is not automatically the highest healthcare decision-maker.

## 1.2 Cross-Role Integration Principles

The role specifications define a federated system rather than thirteen isolated dashboards:

- Patient appointment booking feeds the shared PHC scheduling/token workflow used by the Doctor.
- Doctor consultations can produce prescriptions that flow to the appropriate PHC Pharmacist.
- Nurse workflows consume authorized patient/appointment/test information and send completed reports to the responsible Doctor.
- PHC operational information is aggregated for district oversight.
- Pharmacist supply requirements feed district supply-chain workflows.
- District supply operations can escalate shortages to the State Supply Chain/Warehouse Manager.
- District emergency coordination consumes emergency-relevant PHC/staff/resource information and coordinates with supply-chain operations.
- State Health Administration receives authorized district/state aggregated information.
- State Public Health Analysis uses authorized aggregated health, supply-chain, and emergency summaries.
- National Health Authority receives authorized state-level aggregated reporting rather than bypassing state authorization.
- Super Admin manages the digital platform itself and does not inherit unrestricted clinical or healthcare decision authority.

Where a source role specifies a narrower boundary, that role-specific boundary takes precedence over broad visibility assumptions.

# 2. CONSOLIDATED CROSS-ROLE IMPLEMENTATION REQUIREMENTS

The following rules are consolidated from requirements that recur across the role specifications. They are stated once here rather than repeated inside every role.

## 2.1 Existing Project First

Before implementing any role:

- Inspect the existing repository/codebase, folder structure, frontend framework, build tools, routing, backend, database/schema, APIs, services, state management, authentication, authorization, shared components, notifications, file-upload/reporting systems, AI integrations, PWA configuration, localization approach, validation, and error handling.
- Inspect the existing role modules and their workflows before changing shared functionality.
- Reuse the existing architecture, design system, components, services, data models, APIs, and working functionality wherever possible.
- Do not unnecessarily replace the current frontend framework, backend, database, UI library, routing conventions, or design system.
- Create an implementation plan based on what actually exists.

## 2.2 Preserve Existing Functionality

- Implement only the requested role in the role-specific phase.
- Do not rebuild the entire application.
- Do not delete, rename, overwrite, or break existing pages, routes, components, data, features, or working role functionality.
- Do not create a separate design system for a new role.
- Extend existing models and endpoints through compatible changes where possible.
- Keep the architecture modular and ready for the remaining roles.
- Shared functionality must remain shared rather than being reimplemented separately for each role.

## 2.3 Functional Implementation — Not Static UI

- Build working functionality, not merely static screens, mock dashboards, dummy buttons, or disconnected prototypes.
- Primary buttons, forms, tables, filters, navigation items, actions, APIs, workflows, AI features, inventory operations, notifications, and role actions must work.
- Every important operation must connect to the appropriate backend/database workflow.
- If a required backend service does not yet exist, implement it using the existing architecture rather than simulating a successful backend operation.
- If an external integration is unavailable, expose a clearly defined integration boundary or an explicit unavailable/integration-pending state. Never pretend that an external service is connected.

## 2.4 Shared Systems and No Duplication

- Reuse existing appointment, token, patient, consultation, prescription, inventory, attendance, notification, reporting, and other shared systems when they already exist.
- Do not create duplicate systems that conflict with existing workflows.
- Do not create duplicate patient profiles, medical records, prescriptions, appointments, tokens, attendance records, or duplicate representations of the same operational data.
- Role modules must integrate with the shared workflows rather than creating parallel workflows.
- Information already available through the platform should not require users to manually submit the same data again.

## 2.5 Role-Based Access Control and Authorization

- Access must be scoped to the authenticated user's authorized role and organizational assignment.
- Enforce permissions in both frontend behavior and backend authorization; hiding a button is not sufficient security.
- The backend is the final authority for access control.
- Do not allow users to bypass authorization by manipulating frontend requests.
- Apply minimum-necessary access to patient, clinical, operational, supply-chain, emergency, district, state, and national information.
- A role must not automatically gain responsibilities owned by another role.
- Organizational boundaries such as assigned PHC, district, state, warehouse, or authorized national scope must be enforced.
- High-risk permission/configuration changes require the appropriate authorization, confirmation, auditing, and step-up authentication/approval where specified by the role requirements.

## 2.6 Data Integrity, Transactions, and Auditability

- Use backend-controlled transactions for critical state changes.
- Prevent duplicate records, double booking, invalid token allocation, inconsistent stock changes, unauthorized updates, and other race-condition/data-integrity problems.
- Use concurrency-safe mechanisms where required, especially for shared counters/tokens and inventory transactions.
- Important actions and sensitive administrative changes must be auditable.
- Preserve transaction references, timestamps, source/actor information, status changes, and relevant history where the role specification requires them.
- Do not mark an operation as completed, delivered, acknowledged, reviewed, resolved, or fulfilled unless the required underlying confirmation actually occurred.

## 2.7 Data Quality and Production Data Rules

- Do not fabricate real healthcare, patient, medicine, stock, operational, district, state, or national statistics.
- Use actual authorized database values in production functionality.
- Synthetic/demo data may be used only in clearly labelled demo/testing environments.
- Do not present simulated data as real hospital/PHC data.
- If data is incomplete, stale, unavailable, or not yet integrated, show an explicit state rather than inventing values.
- Preserve data provenance, freshness, validation status, and source information wherever required by the role.

## 2.8 Responsive UI and Design System

- Reuse the existing design system, including typography, colors, spacing, icons, buttons, cards, forms, navigation, and responsive conventions.
- Maintain a clean, professional healthcare-oriented interface where specified.
- Support mobile phones, tablets, laptops, and desktop screens.
- Avoid overflow, broken alignment, inaccessible controls, and layouts that only work at one screen size.
- Use responsive navigation appropriate to the existing application, including desktop sidebars and mobile drawers/compact navigation where required.
- Relevant pages must provide loading, empty, error, and success states.
- Do not create dead navigation links or placeholder pages that appear functional but do nothing.

## 2.9 Localization and Accessibility

- Where localization is required, use a reusable translation-key based system rather than hardcoding translated interface strings throughout components.
- Preserve the project's existing localization approach.
- Patient-facing content explicitly requires Tamil and English support, including interface text, awareness content, notifications, and AI responses.
- Where voice input/speech-to-text is used, provide graceful text-input fallback.
- Ensure Tamil fonts, text rendering, responsive layouts, keyboard interaction, readable contrast, focus states, and accessible controls work correctly where applicable.
- Do not make language switching or accessibility a one-off feature tied to a single screen when the requirement is module-wide.

## 2.10 Notifications, Failure Handling, and Reliability

- Integrate with the existing notification system rather than creating conflicting notification channels.
- Show clear loading, failure, retry, offline, synchronization, and unavailable states where relevant.
- Do not claim that a notification, alert, delivery, acknowledgement, or synchronization succeeded unless the system has confirmation.
- Where offline operation is explicitly required, show the last synchronized data and provide the defined fallback/escalation process.
- Preserve data consistency across retries and partial failures.

## 2.11 AI Safety and Human Oversight

- Each AI assistant must remain specific to its role and authorized information.
- AI is decision support, not a replacement for qualified healthcare professionals or authorized human decision-makers.
- AI must not independently diagnose patients, prescribe medicines, modify treatment, perform unauthorized clinical triage, determine emergency severity, or make decisions assigned to human authorities.
- AI-generated alerts, predictions, recommendations, forecasts, and insights must be reviewable and clearly identified as AI-generated where required.
- Emergency workflows must never be delayed because of continued chatbot interaction.
- AI must operate only on information the user is authorized to access.
- Human confirmation remains required wherever the source role specification requires an authorized action or confirmation.

## 2.12 Testing and Acceptance

- Test role boundaries, happy paths, validation, failure states, unauthorized access, responsive layouts, shared workflows, database/API integration, and important edge cases.
- Do not claim that tests passed unless they were actually executed.
- Verify that new functionality does not break existing modules.

## 2.13 Exact Repeated Requirements Consolidated Once

The following substantive blocks occurred verbatim in multiple uploaded role specifications and are intentionally stated once here:

> **Repeated in Role(s) 6, 7, 8, 12:**
>
> Do not rebuild, overwrite, or break existing modules.

> **Repeated in Role(s) 7, 8:**
>
> * Tamil.
> * English.
> * Mobile.
> * Tablet.
> * Desktop.

> **Repeated in Role(s) 3, 4:**
>
> - Mobile phones.
> - Tablets.
> - Desktop and laptop screens.

> **Repeated in Role(s) 3, 4:**
>
> Complete Working Development Prompt — Smart Health and Supply Chain Resilience

> **Repeated in Role(s) 3, 12:**
>
> Do not claim tests passed unless they were actually executed.

> **Repeated in Role(s) 7, 11:**
>
> Do not deliver a static mockup or hardcoded dashboard.

> **Repeated in Role(s) 2, 6:**
>
> Implement backend-enforced Role-Based Access Control.


# 3. ROLE 01 — Patient


**Role purpose (master summary):** Patient-facing PHC service user. Uses health awareness, profile, PHC discovery, appointments, records, prescriptions, notifications, feedback, settings, and the dedicated wellness assistant.


### Detailed requirements from the uploaded role specification


SMART HEALTH AND SUPPLY CHAIN RESILIENCE



Patient Module – Complete Working Development Prompt



Build a complete, functional Patient Module for our Smart Health and Supply Chain Resilience project, an AI-powered, mobile-first PWA for India's Primary Health Centre (PHC) network.



First inspect the existing project, framework, folder structure, components, dependencies, and current implementation. Reuse the existing architecture and design system wherever possible. Do not unnecessarily recreate or overwrite existing working features.



Develop ONLY the Patient role in this phase. The platform will eventually support 15 roles, so keep the architecture modular and ready for integrating the remaining 14 roles and their separate AI assistants.



Important: Build working functionality, not just static UI, dummy buttons, or non-functional screens.



1. Demo Entry



- Create a demo role selector that can later accommodate all 15 roles.
- Make Patient the only functional role for now.
- Provide an "Enter Patient Demo" button that opens the Patient Dashboard directly.
- Do not implement registration, login, OTP, or real authentication in this phase.
- Use realistic, clearly labeled fictional demo data.



2. Patient Dashboard and Navigation



Create a clean, professional, healthcare-themed dashboard with consistent colors, typography, spacing, and properly aligned components.



Include:



1. Home
2. Health Awareness
3. My Health Profile
4. Find a PHC
5. Appointments
6. My Health Records
7. My Prescriptions
8. AI Wellness Assistant
9. Notifications
10. Feedback and Complaints
11. Settings



Display the patient's demo name, preferred PHC, upcoming appointments, follow-ups, recent records, health reminders, and useful quick actions.



Include quick actions for booking appointments, finding PHCs, viewing records, and opening the AI Wellness Assistant.



Use a desktop sidebar and responsive mobile navigation. Ensure all pages, menus, cards, and controls work correctly on mobile, tablet, laptop, and desktop without overflow or broken alignment.



3. Health Awareness and Motivation Slides



Immediately after entering the Patient Dashboard, display attractive, rotating health awareness slides or cards to educate and motivate patients.



Cover:



- Daily exercise, walking, and fitness.
- Healthy food and nutrition.
- Hydration and proper sleep.
- Mental wellness and stress management.
- Personal hygiene and disease prevention.
- Diabetes, hypertension, dengue, and other common health conditions.
- Vaccination and preventive healthcare.
- Warning signs that require medical attention.



Each slide must include a heading, relevant illustration, short health tip, motivational message, and a practical action patients can follow.



Implement automatic rotation, manual navigation, pause/resume controls, and a Learn More option. Allow patients to revisit all slides through the Health Awareness section.



Create attractive but lightweight visuals. Support Tamil and English content for every slide. Avoid misleading health claims, unsupported home remedies, or promises of cures.



4. Dedicated Patient AI Wellness Assistant



Create a functional, patient-specific chatbot that acts as a Personal Health and Wellness Assistant, focusing primarily on preventive healthcare and healthy living.



It must support:



- General health and wellness questions.
- Fitness, exercise, nutrition, hydration, and sleep guidance.
- Disease prevention and health awareness.
- Common disease explanations and risk factors.
- Healthy lifestyle recommendations.
- Personalized wellness suggestions based on voluntarily provided information.
- Explanations of dashboard health awareness slides.
- Guidance on when to visit a PHC or consult a doctor.



Provide a chat interface with conversation history, suggested questions, loading and error states, clear AI-generated response labels, and a way to restart or clear conversations.



Example questions:



- "How can I stay healthy every day?"
- "What foods help maintain a balanced diet?"
- "How can I prevent diabetes?"
- "தினமும் ஆரோக்கியமாக இருக்க என்ன செய்யணும்?"
- "என்ன உணவுகளைச் சாப்பிட்டால் உடல் ஆரோக்கியமாக இருக்கும்?"



The assistant must provide understandable, reliable, evidence-based health education. It must not independently diagnose diseases, prescribe medicines, change treatment, or replace a qualified healthcare professional.



For serious or emergency symptoms, clearly advise immediate professional medical assistance. Never delay emergency care by continuing a chatbot conversation.



Do not make the chatbot primarily about medicine stock, medicine collection, or appointment booking. Those remain separate Patient Dashboard features. The AI may explain existing patient-authorized information or guide patients to relevant pages when asked.



5. Tamil, English, and Voice Support



Implement a reusable Tamil-English localization system across the entire Patient Module.



- Provide a visible language selector.
- English selection must display all interface text, awareness slides, notifications, and AI responses in English.
- Tamil selection must display the same in natural, understandable Tamil.
- Detect the language of the patient's typed question or speech transcription and respond in that language.
- Support voice input and speech-to-text where feasible, with a graceful text-input fallback.
- Allow language switching at any time and preserve the selected language across pages.
- Ensure Tamil fonts, text rendering, and responsive layouts work correctly.



Use translation keys for interface text rather than hardcoded strings wherever practical. Make the localization framework reusable by all 15 roles.



6. Patient Profile and PHC Discovery



My Health Profile:



- Display and allow editing of permitted personal information, preferred language, preferred PHC, and voluntarily provided relevant health information.
- Use validation and confirmation messages.



Find a PHC:



- Search and filter PHCs by location and services.
- Display PHC name, address, contact, operating hours, and available services when reliable data exists.
- Provide directions or map navigation where supported.



Do not fabricate real-time facility information. Clearly label synthetic demo data.



7. Appointments



Implement a working demo appointment workflow:



- Select a PHC and healthcare service.
- View available demo slots.
- Book, view, reschedule, or cancel appointments where permitted.
- Display appointment date, time, reference, status, and instructions.
- Show upcoming and past appointments.



Use clear statuses such as Requested, Confirmed, Rescheduled, Cancelled, and Completed.



Prevent duplicate submissions and show success only after the operation actually succeeds. Clearly distinguish simulated demo bookings from real PHC appointments.



8. Health Records and Prescriptions



My Health Records:



- Display the patient's own authorized consultation summaries, laboratory results, vaccination records, referrals, follow-ups, and medical documents.
- Organize by date and category, with search or filters where useful.
- Allow viewing or downloading authorized documents where supported.



My Prescriptions:



- Display prescription reference, date, medicine name, clinician-provided dosage, frequency, duration, and instructions.
- Allow the AI to explain existing instructions in simple language.



Never invent real diagnoses, medical records, or prescription details. Clearly label fictional demo records.



The AI must never prescribe, modify dosage, change treatment duration, or recommend stopping prescribed medicines.



9. Medicine Collection – Strict Access Restrictions



Patients may only view fulfilment information for their own prescribed or specifically allocated medicines.



If included, display the patient's own medicine name, fulfilment status, confirmed collection location, collection time, and instructions.



Possible statuses include Processing, Ready for Collection, Partially Available, Temporarily Unavailable, and Collected.



The backend must NEVER expose PHC stock quantities, inventory ledgers, batches, expiry records, stock movements, procurement, suppliers, warehouses, logistics, internal stock alerts, staff dashboards, or other patients' information.



Do not merely hide these fields in the frontend. Enforce patient-specific access restrictions in backend APIs.



For the demo, use predefined synthetic fulfilment data. Do not implement a pharmacist dashboard inside the Patient Module or claim that a medicine is ready without a valid patient-specific status.



10. Notifications, Feedback, and Complaints



Notifications:



- Display appointment confirmations, changes, follow-up reminders, vaccination reminders, and relevant health updates.
- Allow marking notifications as read or dismissed.
- Use in-app notifications for the demo.



Feedback and Complaints:



- Allow patients to submit healthcare feedback, appointment issues, or service complaints.
- Display their own complaint history and status.
- Provide a reference number and confirmation after successful submission.



Use synthetic data for demo workflows. Keep SMS, email, and WhatsApp integrations modular for future implementation.



11. Architecture, Backend, and Data



Use the existing project's technology stack wherever possible. Do not replace working architecture without a clear reason.



Organize the Patient module into reusable components and modular services for:



- Patient frontend and navigation.
- Profile and medical records.
- PHC discovery and appointments.
- Prescriptions and patient-specific fulfilment.
- Notifications and complaints.
- AI Wellness Assistant.
- Shared design system and localization.



Implement documented, validated backend APIs for patient profile, PHCs, appointments, records, prescriptions, fulfilment status, notifications, complaints, and AI interactions.



Use a practical data model with patient profiles, PHCs, services, appointments, records, prescriptions, patient-specific fulfilment, notifications, complaints, and AI conversations where appropriate.



Use stable IDs, relationships, timestamps, and appropriate status fields.



Use synthetic data for all initial demonstrations. Keep internal supply chain data separate from patient-facing services.



12. Security, Reliability, and Accessibility



- Enforce server-side authorization and patient-level data access.
- Do not trust frontend IDs or hidden UI controls for security.
- Never expose API secrets or privileged credentials in frontend code.
- Protect against injection, invalid inputs, unauthorized access, and duplicate requests.
- Avoid storing sensitive health information insecurely in local storage or shared-device caches.
- Use appropriate encryption, rate limiting, privacy-conscious AI processing, and audit logging.
- Clearly identify offline or stale data; never present it as real-time.
- Handle network failures, API errors, missing records, AI timeouts, and invalid forms with clear recovery actions.
- Optimize for low-end Android devices and slow networks.
- Include accessible typography, sufficient contrast, keyboard navigation, screen-reader labels, and touch-friendly controls.



Full production authentication and identity verification will be implemented collectively after all 15 role interfaces are finalized. Do not use real patient data in the unauthenticated demo.



13. Testing and Implementation



Build in this order:



1. Inspect the existing project and implement the demo entry, shared UI, localization, and responsive Patient Dashboard.
2. Implement awareness slides and the Patient AI Wellness Assistant.
3. Implement profile, PHC discovery, appointments, records, prescriptions, and patient-specific fulfilment.
4. Implement notifications, feedback, and complaints.
5. Test all workflows, Tamil-English switching, mobile responsiveness, security boundaries, and failure handling.



Test that patients cannot access another patient's records or any internal PHC inventory through either the UI or backend APIs.



Ensure every navigation item, button, slide control, form, language selector, and chatbot interaction is functional. Do not leave placeholder pages or non-functional buttons.



Prepare a stable demo using fictional data without depending on live government systems or external integrations.



Final Objective



Deliver a polished, fully functional Patient Module that combines healthcare access, preventive health awareness, motivational slides, and a dedicated bilingual AI Wellness Assistant.



Prioritize patient safety, real usability, correct Tamil-English behavior, secure patient-specific data, responsive UI, and reliable demo workflows.



Build only the Patient role now, but keep the architecture ready for integrating the other 14 roles and their separate AI assistants later. Preserve existing working project features and do not unnecessarily rebuild the entire application.




# 4. ROLE 02 — Doctor / Medical Officer


**Role purpose (master summary):** Clinical role responsible for assigned patients, consultations, prescriptions, emergency handling, attendance, and the Doctor-specific AI assistant.


### Detailed requirements from the uploaded role specification


PROJECT: SMART HEALTH & SUPPLY CHAIN RESILIENCE PWA



ROLE 02: DOCTOR / MEDICAL OFFICER



Build a complete, functional Doctor module that integrates with the existing Patient module and shared PHC scheduling system.



IMPORTANT:
Before making changes, inspect the existing codebase, framework, database, APIs, design system, routing, and Patient module. Reuse existing components, services, data models, and working functionality wherever possible. Do not rebuild, overwrite, or break the Patient module.



Implement ONLY the Doctor role in this phase. Do not implement other roles.



1. ROLE AND PURPOSE



The Doctor is responsible for:



- Attending patients assigned through the PHC appointment and token system.
- Managing consultations and issuing prescriptions.
- Sending prescriptions directly to the appropriate PHC Pharmacist.
- Recording daily attendance for the PHC In-charge.
- Using a personalized AI assistant for daily workload, scheduling, and operational reminders.



The Doctor is not responsible for managing patient registrations, pharmacy inventory, supply chain operations, or platform administration.



2. DOCTOR DASHBOARD



Create a clean Doctor dashboard containing:



- Today's overview and duty status.
- Today's assigned patient count.
- Upcoming appointments and assigned patient queue.
- Emergency alerts.
- Pending and completed consultations.
- Prescription status.
- Daily attendance and attendance history.
- Personalized Doctor AI assistant.



Provide clear navigation to:
Doctor Home, My Queue, Emergency Alerts, Consultations, Prescriptions, Attendance, and AI Assistant.



Display only information authorized for the logged-in Doctor and assigned PHC.



3. APPOINTMENT, TOKEN AND DOCTOR ALLOCATION



Integrate with the existing Patient appointment booking and PHC scheduling system. Do not create a separate or conflicting appointment system.



When a patient books an appointment, the shared scheduling system must:



- Generate a unique sequential token number, such as 501, 502, 503.
- Assign the appointment date, available time slot, PHC, and available Doctor.
- Support approximately 3–4 Doctors per PHC, with configurable capacity.
- Allocate patients according to Doctor duty status, available slots, existing workload, and appointment capacity.
- Prevent duplicate tokens, double booking, and assignment to unavailable Doctors.
- Support authorized reassignment when a Doctor is absent or unavailable.
- Update the assigned Doctor's queue and notify affected users when appointments change.



Each Doctor must see only their assigned queue by default, including:



- Token number.
- Appointment time.
- Patient identifier and permitted details.
- Appointment status.
- Emergency priority indicator.
- Consultation status.



Doctors must not manually select arbitrary patients to construct their queues. They should open patients from their assigned appointments or an authorized emergency assignment.



Token numbers must be unique within the defined PHC and scheduling period. Use a concurrency-safe backend allocation mechanism rather than generating tokens only in the frontend.



4. EMERGENCY PATIENT HANDLING



Implement a priority workflow for authorized emergency cases.



- Authorized PHC staff must be able to flag an emergency and record its arrival time and priority.
- Immediately notify the appropriate available Doctor.
- Show a prominent emergency alert in the Doctor dashboard.
- Allow emergency cases to bypass the normal appointment queue when authorized.
- Ensure emergency cases are not delayed because of ordinary token order.
- Record who raised the emergency, assignment changes, acknowledgement, and response status.
- If the assigned Doctor is unavailable, notify another available authorized Doctor or escalate to the PHC In-charge.
- Allow the Doctor to acknowledge the alert and update the emergency handling status.



Emergency priority must be determined by authorized clinical staff using established protocols. AI must not independently diagnose, triage, or determine emergency severity.



If the system is offline or notifications fail, show the last synchronized queue and provide a clear manual escalation/fallback procedure. Never indicate that an emergency alert was delivered or acknowledged unless confirmed.



5. PATIENT CONSULTATION WORKFLOW



The Doctor workflow must be:



Assigned patient queue → Open assigned patient → Verify patient identity → Attend consultation → Record consultation → Create prescription if required → Complete consultation.



- The Doctor must access the selected patient's relevant, authorized information needed for the current consultation.
- Display the minimum necessary patient information, such as patient identifier, appointment details, and relevant authorized clinical context.
- Do not create duplicate patient profiles or duplicate medical records.
- Allow the Doctor to record consultation notes, relevant observations, and consultation status.
- Mark a consultation as completed, pending, or referred as applicable.
- Save consultation data against the correct patient and appointment.
- Prevent unauthorized access to another PHC's patients or unrelated patient records.



The Doctor must not have unrestricted access to all patient medical records across the platform.



6. PRESCRIPTION CREATION AND DIRECT PHARMACIST HANDOFF



Prescription creation is a Doctor responsibility.



After attending a patient, the Doctor can create a prescription linked to the correct patient and consultation.



Prescription fields:



- Patient ID and consultation ID.
- Prescribing Doctor and PHC.
- Medicine name and relevant medicine identifier.
- Prescribed strength and dosage.
- Route, frequency, and duration where applicable.
- Total prescribed quantity.
- Instructions and relevant precautions.
- Prescription date, status, and authorized signature or approval mechanism.



Workflow:



Doctor selects an assigned patient → Consults patient → Creates and validates prescription → Submits prescription → Prescription appears directly in the assigned PHC Pharmacist's dashboard.



Requirements:



- Automatically associate the prescription with the correct patient, Doctor, consultation, and PHC.
- Send the prescription to the correct PHC Pharmacist through a secure backend workflow.
- Notify the Pharmacist when a new prescription is received.
- Ensure the Pharmacist can identify the patient and the exact prescribed medicines and quantities.
- Allow the Doctor to view prescription status and any clarification requests.
- Prevent accidental duplicate submissions and unauthorized modification after dispensing begins.
- Corrections or cancellations must create an auditable version or amendment, with appropriate notification to the Pharmacist.



The Pharmacist is responsible for checking the prescription, checking available inventory, preparing medicines, recording the actual quantity dispensed, and updating dispensing status.



The Doctor must not manage inventory quantities, batches, expiry dates, procurement, or medicine dispatch operations.



Medicine collection is directly from the PHC pharmacy counter. Do not implement home delivery, courier, or medicine transportation to patients.



Support prescription statuses such as:
Draft, Submitted, Received by Pharmacist, Dispensed, Partially Dispensed, Unavailable, Clarification Required, and Cancelled.



Never mark a prescription as dispensed merely because it was submitted.



7. DAILY DOCTOR ATTENDANCE



Implement a dedicated Doctor attendance section.



- Allow the Doctor to mark daily check-in and check-out.
- Record attendance date, timestamps, Doctor ID, assigned PHC, and attendance status.
- Prevent duplicate attendance records for the same duty period.
- Allow authorized corrections with a reason and audit trail.
- Display attendance history to the Doctor.
- Send attendance information to the PHC In-charge dashboard.
- Allow the PHC In-charge to monitor attendance and review exceptions.



Attendance must be recorded separately from appointment and consultation completion.



Do not automatically mark a Doctor present merely because they log into the PWA.



8. PERSONALIZED DOCTOR AI ASSISTANT



Create a Doctor-specific AI assistant that uses authorized operational data from the Doctor's assigned PHC, duty schedule, and appointment queue.



Its purpose is daily workload assistance, appointment reminders, queue awareness, and operational coordination.



ALLOWED AI FUNCTIONS:



A. Daily workload summary



- Estimate today's expected patient count using available appointment and historical PHC data.
- Summarize assigned appointments, completed consultations, and pending patients.
- Show upcoming workload and relevant schedule reminders.



B. Appointment reminders



- Notify the Doctor about upcoming appointments and the next assigned token.
- Example: "Token 503 is scheduled for 10:30 AM."
- Identify pending or delayed appointments using verified scheduling data.



C. Workload assistance



- Identify unusually high workload or scheduling conflicts.
- Suggest that the PHC In-charge consider authorized reassignment to another available Doctor.
- Provide workload summaries based on the available data and clearly indicate when information is incomplete.



D. Emergency and operational notifications



- Surface emergency alerts received from authorized staff.
- Remind the Doctor about unacknowledged operational alerts and pending tasks.
- Provide daily attendance and schedule reminders.



AI RESTRICTIONS:



- Do not generate medical diagnoses or clinical assessments.
- Do not recommend medicines, dosages, treatments, or prescription changes.
- Do not independently triage or determine emergency severity.
- Do not autonomously assign, reassign, cancel, or complete appointments.
- Do not issue prescriptions or modify clinical records.
- Do not invent patient counts, appointment times, attendance, or emergency alerts.
- Do not expose patient information unrelated to the Doctor's authorized assignments.



AI suggestions must be advisory, explain their operational data source where possible, and require authorized human action for consequential changes.



If the AI service fails, the Doctor must still be able to access the normal queue, attend patients, create prescriptions, and mark attendance.



9. DOCTOR ROLE DO'S AND DON'TS



DO:



- Use the assigned PHC queue and scheduling service.
- Verify the patient before consultation and prescription creation.
- Record accurate consultation and prescription information.
- Submit prescriptions to the correct Pharmacist.
- Record daily attendance and communicate operational issues.
- Respond promptly to authorized emergency alerts.
- Review AI operational suggestions before taking action.



DON'T:



- Manually create conflicting appointment tokens.
- Select or access arbitrary patients outside authorized assignments.
- View or modify another Doctor's restricted records without authorization.
- Manage pharmacy inventory or supply chain operations.
- Allow AI to diagnose, prescribe, triage, or make autonomous clinical decisions.
- Mark prescriptions dispensed without Pharmacist confirmation.
- Modify attendance or consultation history without authorized correction and audit.
- Claim that an appointment, prescription, notification, or emergency alert succeeded without backend confirmation.



10. DATABASE AND BACKEND INTEGRATION



Reuse existing Patient and appointment data models wherever possible.



Implement or extend the following entities as necessary:



Doctor:
doctor_id, user_id, assigned_phc_id, qualifications/role metadata, duty_status, created_at, updated_at.



DoctorSchedule:
schedule_id, doctor_id, phc_id, duty_date, start_time, end_time, slot_capacity, availability_status.



Appointment:
appointment_id, patient_id, phc_id, doctor_id, token_number, appointment_date, time_slot, status, priority, created_at, updated_at.



Consultation:
consultation_id, appointment_id, patient_id, doctor_id, phc_id, consultation_notes, status, timestamps.



Prescription:
prescription_id, consultation_id, patient_id, doctor_id, phc_id, medicine_items, prescribed_quantities, instructions, status, timestamps, version.



DoctorAttendance:
attendance_id, doctor_id, phc_id, duty_date, check_in, check_out, status, correction_reason, timestamps.



EmergencyAlert:
alert_id, patient_reference, phc_id, priority, raised_by, assigned_doctor_id, acknowledgement_status, response_status, timestamps.



DoctorAIInteraction:
interaction_id, doctor_id, conversation_reference, authorized_context_reference, timestamps.



Enforce backend validation, foreign keys, appropriate indexes, unique token constraints, transaction-safe allocation, and audit history.



Do not expose internal database identifiers or unrestricted patient data in public responses.



11. SECURITY AND ACCESS CONTROL



- Doctor access must be limited to authorized PHC assignments and patient consultations.
- Derive the authenticated Doctor identity from the verified session or token.
- Never trust a frontend-supplied doctor_id or patient_id without authorization checks.
- Validate patient, appointment, consultation, prescription, and PHC relationships before every operation.
- Protect sensitive health data in transit and at rest.
- Apply secure session handling, input validation, rate limiting, and API error handling.
- Prevent unauthorized access, injection, duplicate submissions, and insecure file uploads.
- Keep auditable records of prescription creation, changes, attendance corrections, emergency handling, and sensitive data access.
- Keep AI prompts and outputs free from unnecessary personal health information.
- Production access to real patient data requires proper authentication, authorization, and approved privacy safeguards.



For demo mode, use clearly labelled synthetic patients, appointments, prescriptions, and attendance records. Do not represent simulated data as real PHC activity.



12. UI/UX AND ACCESSIBILITY



Reuse the existing Patient module's design system, typography, colors, spacing, localization framework, and reusable components.



Do not redesign or break the existing Patient interface.



Doctor UI must be:



- Clean, professional, mobile-first, and easy to use during busy PHC operations.
- Responsive across mobile phones, tablets, laptops, and desktops.
- Consistent with the existing PWA navigation and visual identity.
- Available in Tamil and English using the shared localization system.



Layout requirements:



- Desktop: sidebar navigation and structured dashboard panels.
- Mobile: compact navigation and touch-friendly queue cards.
- Show token number, appointment time, patient reference, and status clearly.
- Make emergency alerts prominent without confusing them with ordinary notifications.
- Ensure tables, forms, cards, and modals fit small screens without overlap, clipping, or unwanted horizontal scrolling.
- Support readable text, Tamil glyphs, keyboard navigation, screen readers, visible focus, and sufficient color contrast.



Provide meaningful loading, empty, success, error, offline, and stale-data states.



Use accessible labels, clear confirmation messages, and safe form validation. Do not rely on color alone to communicate emergency status.



13. FAILURE HANDLING



Handle:



- Network loss and backend/API failure.
- Concurrent appointment bookings and token conflicts.
- Doctor absence or schedule changes.
- Emergency notification failures.
- Duplicate prescription submissions.
- Pharmacist clarification or unavailable medicines.
- Invalid patient or PHC assignments.
- AI timeout or incorrect operational suggestions.
- Attendance submission failure.
- Stale or incomplete scheduling data.



Use safe retries, idempotency where appropriate, clear error messages, and explicit recovery actions.



Never show false success. Clearly identify pending synchronization and unconfirmed operations.



14. TESTING AND ACCEPTANCE CRITERIA



Test:



- Doctor can access only assigned queues and authorized patient information.
- Appointment allocation supports multiple Doctors and prevents double booking.
- Token generation remains unique under concurrent requests.
- Emergency cases trigger the correct authorized alerts and priority workflow.
- Consultation and prescription are linked to the correct patient.
- Prescription appears in the correct Pharmacist's dashboard.
- Pharmacist dispensing status is reflected correctly.
- Attendance is submitted to the PHC In-charge.
- AI provides operational suggestions only and does not diagnose or prescribe.
- All core workflows function on mobile, tablet, and desktop.
- Tamil and English localization works throughout.
- Existing Patient module remains functional and visually unchanged.
- Unauthorized access to patient data, pharmacy inventory, or administrative functions is blocked.



Implement functional frontend, backend APIs, database integration, validation, and error handling. Do not deliver static mockups, nonfunctional buttons, or hardcoded success messages.



15. IMPLEMENTATION PRIORITY



Phase 1:
Doctor dashboard, role-aware navigation, assigned queue, consultation workflow, attendance, and responsive UI.



Phase 2:
Prescription creation, secure Pharmacist handoff, status tracking, and emergency alerts.



Phase 3:
Personalized operational AI assistant, workload summaries, reminders, and scheduling suggestions.



Phase 4:
Security hardening, integration testing, accessibility, failure handling, audit, and production-readiness improvements.



FINAL OBJECTIVE:



Deliver a working Doctor module integrated with the existing Patient appointment system. Patients receive tokens and appointment slots through the shared scheduling workflow; Doctors attend their assigned queues, handle authorized emergencies, issue prescriptions directly to the correct Pharmacist, submit attendance to the PHC In-charge, and receive personalized AI assistance limited to daily operational workload and scheduling.



Preserve all existing Patient functionality and design. Do not implement other roles in this phase.




# 5. ROLE 03 — Nurse / Healthcare Staff


**Role purpose (master summary):** PHC nursing/healthcare operations role covering patient arrival/preparation, token coordination, routine tests and observations, reports, beds, nursing tasks, and attendance.


### Detailed requirements from the uploaded role specification


ROLE 03 — NURSE / HEALTHCARE STAFF



You are working on an existing project called Smart Health and Supply Chain Resilience, a mobile-first, AI-powered healthcare and PHC management platform.



Your task is to implement Role 03 — Nurse / Healthcare Staff as a complete, functional, secure, responsive module integrated into the existing application.



This is NOT a request to rebuild the application or create a separate standalone dashboard.



Build upon the existing codebase, design system, Patient module, Doctor module, shared components, and backend architecture.



---



1. CRITICAL RULES — READ BEFORE CODING



Before making any changes:



1. Inspect the complete existing codebase, folder structure, frontend framework, backend, database, routing, state management, authentication, shared components, and existing Patient and Doctor modules.
2. Identify the existing design system, typography, colors, spacing, icons, navigation, reusable cards, buttons, form components, responsive breakpoints, and localization approach.
3. Identify the existing Patient appointment/token workflow and Doctor consultation/prescription workflow.
4. Reuse existing functionality and shared services wherever possible.
5. Implement Nurse functionality without breaking or unnecessarily modifying existing Patient and Doctor functionality.
6. Do not create duplicate appointment, token, patient, prescription, attendance, or notification systems if equivalent services already exist.
7. Do not replace the existing project architecture, framework, database, or UI library unless absolutely necessary and justified.
8. Do not remove existing pages, features, routes, components, data, or working functionality.
9. Do not create a separate design system for the Nurse dashboard.
10. Do not implement static mock screens and claim they are functional. Every primary action must have a working, validated workflow.



Priority: Preserve existing functionality first, integrate Nurse functionality second, and add new architecture only when genuinely required.



If an integration is not yet available, create a clearly defined interface or service abstraction and use synthetic demo data only in demo mode. Never present simulated data as real hospital data.



---



2. ROLE DEFINITION AND OBJECTIVE



Role: Nurse / Healthcare Staff



Role ID: 03



Healthcare level: PHC / Facility Level



Primary purpose:



The Nurse manages daily nursing operations, patient arrival and preparation, token-wise queue coordination, routine tests and observations, test report submission to Doctors, assigned bed availability and occupancy, nursing tasks, and daily attendance reporting to the PHC In-charge.



The Nurse must be able to understand:



- How many patients are expected today.
- How many patients have actually arrived.
- Which token patients are waiting, prepared, or pending.
- Which patients require authorized routine tests.
- Which tests are pending or completed.
- Which reports have been sent to the Doctor and which are awaiting review.
- Which assigned beds are occupied, vacant, or unavailable.
- Which nursing tasks remain incomplete.
- Whether attendance has been submitted to the PHC In-charge.



The Nurse role must operate independently for authorized nursing tasks while remaining connected to the existing Patient, Doctor, and PHC In-charge workflows.



---



3. USER PERSONA AND PERMISSIONS



The Nurse is a healthcare professional working at an assigned PHC.



The Nurse must have access only to the assigned PHC, authorized patients, assigned beds, relevant clinical tasks, authorized test orders, and permitted operational data.



Nurse permissions



The Nurse can:



- View assigned PHC appointments, tokens, and patient arrivals.
- Record patient arrival and initial preparation status.
- Record vitals and authorized nursing observations.
- View authorized Doctor-issued prescriptions and nursing instructions.
- Record authorized nursing care and medicine administration.
- View authorized test orders and record permitted test results.
- Upload test reports where supported.
- Send completed reports to the responsible Doctor.
- Track report review status.
- Manage assigned beds and occupancy status.
- Record daily attendance and submit it to the PHC In-charge.
- Use the Nurse-specific AI Assistant.
- View authorized nursing task history and shift handover information.



Nurse restrictions



The Nurse must NOT:



- Independently diagnose a patient.
- Create or modify Doctor prescriptions.
- Change medicine strength, dosage, route, or treatment duration.
- Make independent clinical decisions using AI.
- Independently determine emergency severity or replace clinical triage.
- Access unrelated PHCs or unrestricted patient records.
- Access supply chain procurement, supplier, warehouse, or district inventory administration.
- Access other roles' private dashboards or administrative permissions.
- Mark a test as completed without an actual result or authorized completion record.
- Mark a Doctor report as reviewed unless the Doctor's authorized review action has occurred.
- Modify attendance records without authorized correction workflows.



Enforce these restrictions in both frontend permissions and backend authorization.



Hiding a button is not sufficient security.



---



4. NURSE DASHBOARD — PAGES AND NAVIGATION



Create or integrate the following pages using the existing design system.



Page 1: Nurse Dashboard / Home



This is the Nurse's landing page after entering the Nurse role.



Display a clear daily operational summary.



Dashboard cards



1. Expected Patients Today
2. Actual Patient Arrivals
3. Waiting Patients
4. Patients Requiring Preparation
5. Pending Routine Tests
6. Reports Awaiting Doctor Review
7. Assigned Bed Occupancy
8. Pending Nursing Tasks



Show relevant date, PHC name, assigned Nurse, and shift information when available.



Each summary card should navigate to its relevant filtered page.



Use actual authorized data from the backend.



If no data is available, show an empty state rather than fabricated numbers.



Patient forecast



Show an estimated patient count based on available appointment bookings and historical patient arrival data.



Clearly label the value as an estimate.



Display the forecast period, data source, and last updated time.



If historical data is unavailable, show the actual confirmed bookings separately and indicate that no reliable forecast is available.



Never represent an estimate as a confirmed number of patients.



Page 2: Patient Queue & Token Tracking



Display the existing Patient booking/token information for the Nurse's assigned PHC.



Integrate with the shared appointment/token service used by the Patient and Doctor modules.



Display:



- Patient's authorized identifier and minimum necessary details.
- Appointment date and time.
- Token number.
- Assigned Doctor.
- Arrival status.
- Preparation status.
- Required authorized observations/tests.
- Current workflow status.



Possible statuses:



Booked, Not Arrived, Arrived, Preparation Pending, Tests Pending, Ready for Doctor, Consultation In Progress, Completed, Cancelled, and Referred.



The exact statuses must align with existing shared workflow enums.



Nurse actions



- Verify patient arrival using the authorized patient identification process.
- Mark arrival only after actual arrival is confirmed.
- Open the authorized patient preparation workflow.
- Record relevant vitals and nursing observations.
- View authorized test requirements.
- Mark preparation completed after required steps are actually completed.
- Hand the patient over to the Doctor through the existing workflow.



Do not allow the Nurse to change token numbers, create duplicate bookings, or arbitrarily reassign Doctors.



If a patient arrives without an appointment, provide an authorized walk-in registration or escalation workflow if supported by the existing system.



Do not create fake appointments or confirmations.



Page 3: Vitals & Nursing Care



Create a patient-specific nursing workspace.



The Nurse must select an authorized patient and verify the patient identity before entering observations.



Support the following configurable observations where applicable:



- Blood pressure.
- Temperature.
- Pulse rate.
- Respiratory rate.
- Oxygen saturation (SpO₂).
- Weight.
- Height.
- Other facility-authorized nursing observations.



Each observation should include:



- Patient ID.
- Encounter/consultation ID where applicable.
- Recorded value and unit.
- Date and time.
- Recording Nurse.
- Relevant notes.
- Source or measurement method when supported.



Validate numeric inputs, units, required fields, and plausible ranges.



Do not silently alter recorded values.



If a value is outside configured validation limits, request confirmation or authorized escalation. Do not automatically diagnose the patient.



Maintain an auditable correction process for incorrect observations.



Nursing task management



Display tasks assigned by the Doctor or authorized PHC staff.



Examples:



- Patient preparation.
- Authorized observations.
- Doctor-ordered nursing care.
- Follow-up care.
- Authorized medicine administration.
- Pending handover tasks.



Statuses should include Pending, In Progress, Completed, Not Completed, and Requires Review where applicable.



Record who completed each task and when.



Do not allow the Nurse to independently create clinical treatment orders.



Page 4: Routine Tests & Reports



Create a complete test and report workflow integrated with the Doctor consultation system.



Test order source



Routine tests may originate from:



1. A valid Doctor-issued test order.
2. A facility-authorized standing protocol, if explicitly configured and permitted.



Do not allow the AI Assistant or Nurse to independently create clinical test orders.



Test management



For each authorized test, display:



- Patient identifier.
- Token number.
- Encounter/consultation ID.
- Test name.
- Ordering Doctor or authorized protocol.
- Order date and time.
- Test status.
- Result and units, if applicable.
- Report attachment, if supported.



Support the workflow:



Test Ordered → Pending → Sample/Measurement Recorded → Result Entered or Report Uploaded → Completed → Sent to Doctor → Doctor Review Status.



Use the actual test workflow and permitted status transitions defined in the backend.



Test result entry



Allow authorized Nurses to enter only the tests and results within their assigned responsibilities and permissions.



Where applicable, support:



- Numeric results.
- Text results.
- Units.
- Reference ranges provided by an authorized source.
- Test date and time.
- Result entry operator.
- Report file upload.



Do not invent reference ranges, test values, or medical interpretations.



If a test requires a laboratory technician or another authorized role, route it to that role instead of granting the Nurse unauthorized access.



Report upload security



Validate file type, file size, and file content.



Store reports securely.



Use authenticated access-controlled file URLs.



Prevent unauthorized file access and malicious uploads.



Associate every report with the correct patient, encounter, and test order.



Doctor handoff



After an authorized test is completed:



- Provide a Send to Doctor action.
- Associate the report with the correct consultation and responsible Doctor.
- Notify the Doctor through the existing notification service.
- Update the report handoff status only after the backend confirms successful submission.
- Display submission time and responsible Nurse.
- Allow the Nurse to see whether the Doctor has reviewed the report, where the Doctor workflow supports this.



If the Doctor has not reviewed the report, display Awaiting Doctor Review.



Do not mark a report as reviewed or clinically approved on behalf of the Doctor.



If the report belongs to another Doctor or consultation, prevent submission and show an actionable validation error.



If the upload or submission fails, retain a safe retry workflow and prevent duplicate report creation.



Page 5: Doctor Report Handoff & Review Tracking



Provide a consolidated view of:



- Reports awaiting submission.
- Reports successfully sent to the Doctor.
- Reports awaiting Doctor review.
- Reports requiring correction or clarification.
- Reports successfully reviewed by the Doctor.



Show the responsible Doctor, patient encounter, test, and timestamps.



Allow the Nurse to resend a notification or retry a failed submission only through a safe, authorized, idempotent workflow.



The Nurse cannot approve clinical findings or change Doctor review status.



Page 6: Assigned Bed Management



Create a bed management interface limited to beds assigned to the Nurse or otherwise explicitly authorized.



Display:



- Bed identifier.
- Ward or unit, if applicable.
- Current occupancy status.
- Authorized patient assignment.
- Admission or occupancy start time.
- Last status update.
- Assigned Nurse.



Support statuses such as:



Vacant, Occupied, Cleaning, Maintenance/Unavailable, and Reserved if supported by the facility configuration.



Bed actions



- Update the status of assigned beds.
- Record authorized occupancy changes.
- Associate an admitted patient with the correct bed through the admission workflow.
- Record authorized transfer or discharge updates.
- View current assigned-bed occupancy.



Prevent double assignment of a bed.



Prevent the same patient from being assigned to conflicting beds within the same active admission unless an authorized transfer is completed.



Bed status updates must be validated and persisted by the backend.



PHC In-charge must receive facility-level visibility into bed occupancy.



Do not expose patient details to unauthorized users.



Do not present a bed as available until the backend confirms its availability.



If the PHC does not support inpatient beds, show an appropriate not-configured state rather than fabricated beds.



Page 7: Attendance & Shift Handover



Attendance



The Nurse must be able to:



- Check in.
- Check out.
- View own attendance history.
- Submit daily attendance to the PHC In-charge.
- View submission status.
- Request an authorized correction with a reason.



Attendance must be associated with the authenticated Nurse, assigned PHC, date, and configured shift.



Do not mark attendance automatically based only on login.



Prevent duplicate or conflicting attendance records.



Submit attendance to the PHC In-charge using the existing attendance service if available.



Show Submitted, Pending, Approved, Rejected, or Correction Requested only where those states are supported by the actual approval workflow.



Do not automatically mark attendance as approved.



Shift handover



Provide a handover summary of:



- Pending authorized nursing tasks.
- Patients awaiting preparation.
- Pending routine tests.
- Reports awaiting Doctor review.
- Assigned bed occupancy and unresolved bed status updates.
- Relevant outstanding alerts.



Handover information must be restricted to authorized PHC staff.



Record the handover creator, receiving staff member where supported, timestamp, and status.



Do not include unnecessary patient data in notifications or general handover summaries.



Page 8: Nurse AI Assistant



Implement a dedicated Nurse AI Assistant.



This is a separate role-specific assistant.



It must not reuse the Patient Wellness Assistant as its primary workflow and must not become a general Doctor or supply chain assistant.



The AI must operate only within the Nurse's authorized scope.



---



5. NURSE AI — INTELLIGENCE, INPUTS AND BOUNDARIES



AI Feature A: Daily Patient Forecast



Purpose: Help Nurses prepare for expected daily workload.



Inputs:



- Confirmed appointment/token bookings.
- Authorized historical patient arrival counts.
- Date and time patterns, where sufficient data exists.
- Facility operating schedule.
- Available nursing staff and authorized workload information.



Output:



- Estimated patient count.
- Expected workload by time period, if supported.
- Actual arrivals versus forecast.
- Data freshness and confidence/uncertainty information.



Do not invent forecasts when insufficient data exists.



Forecasting may begin with a transparent baseline using historical averages and booked appointments. Introduce more advanced ML only when sufficient representative data is available.



Measure forecast error using appropriate metrics such as MAE and monitor performance across facilities and time periods.



AI Feature B: Queue & Preparation Assistant



Identify:



- Patients awaiting preparation.
- Missing authorized observations.
- Upcoming booked tokens.
- Delayed preparation tasks.
- Patients ready for Doctor consultation.



Provide operational reminders and summaries.



The AI must not change appointment tokens, cancel appointments, reassign Doctors, or independently make clinical priority decisions.



AI Feature C: Test & Report Assistant



Summarize:



- Authorized test orders awaiting completion.
- Missing result fields.
- Reports awaiting upload.
- Reports not yet sent to the Doctor.
- Reports awaiting Doctor review.
- Failed report submission attempts.



The AI may identify missing information and workflow inconsistencies.



It must not interpret results as a diagnosis, recommend treatment, or alter test orders.



AI Feature D: Nursing Workload & Handover Assistant



Summarize authorized nursing tasks, pending activities, assigned beds, and outstanding handover items.



Provide suggestions to help the Nurse organize work.



Suggestions are advisory. Any reassignment or approval must be performed through the authorized workflow by a permitted user.



AI Feature E: Bed Status Assistant



Identify stale bed status, conflicting occupancy records, and pending authorized bed updates.



The AI may recommend that the Nurse verify the status.



It must not independently declare a bed available or assign a patient to a bed.



AI Feature F: Attendance & Reminder Assistant



Provide reminders for:



- Check-in/check-out.
- Attendance submission.
- Pending handover.
- Incomplete nursing tasks.



Do not modify attendance records or submit approvals automatically.



AI safety and explainability



For every AI-generated operational summary:



- Show that it is AI-generated.
- Show the data source and last updated time where available.
- Distinguish recorded facts from estimates and suggestions.
- Clearly indicate missing or stale data.
- Allow the Nurse to ignore, dismiss, or correct a suggestion.
- Log important AI-assisted actions where appropriate.
- Require human confirmation for consequential actions.



AI failure must never block normal nursing operations.



If the AI service is unavailable, the Nurse must still be able to manage patients, record authorized observations, update tests, submit reports, manage assigned beds, and record attendance.



---



6. END-TO-END WORKFLOW



Implement the following workflow using the existing Patient and Doctor systems.



1. Nurse signs in through the existing authentication mechanism or uses the explicitly labeled demo access mechanism.
2. Backend resolves the Nurse's verified identity, assigned PHC, permissions, and shift.
3. Nurse Dashboard loads today's actual bookings, authorized forecast, arrivals, tests, reports, assigned beds, and tasks.
4. Nurse reviews the expected patient workload.
5. Patient arrives and the Nurse verifies the correct patient and token.
6. Nurse records arrival and completes authorized preparation and observations.
7. Nurse views authorized Doctor orders or configured standing protocols.
8. Nurse performs permitted routine tests or routes them to the appropriate authorized role.
9. Nurse records results or securely uploads the report.
10. Backend validates the patient, encounter, test order, Nurse permission, and report data.
11. Nurse submits the report to the responsible Doctor.
12. Doctor receives the report through the existing Doctor dashboard and notification workflow.
13. Doctor reviews the report and makes clinical decisions through the Doctor module.
14. Nurse sees the report's actual review status without changing the Doctor's decision.
15. Nurse updates assigned bed occupancy and nursing tasks as required.
16. Nurse checks out and submits attendance to the PHC In-charge.
17. PHC In-charge sees authorized attendance and facility operational summaries.
18. Nurse completes the shift handover and views task history.



Do not create duplicate workflows where existing services already provide the same functionality.



All status changes must be validated and persisted on the backend.



---



7. ROLE CONNECTIONS AND INTEGRATIONS



Integrate Nurse with the following roles.



Patient — Role 01



Nurse receives authorized appointment/token and patient arrival information.



Nurse-recorded observations and authorized reports must be linked to the correct patient encounter.



Do not modify Patient's existing wellness assistant, appointment UI, prescriptions, records, or other working features unnecessarily.



Patient must not receive access to internal Nurse dashboards or PHC operational records.



Doctor — Role 02



Doctor creates prescriptions and authorized test orders.



Nurse views authorized orders, records permitted nursing actions and test results, and sends reports to the responsible Doctor.



Doctor receives reports and reviews them in the existing Doctor workflow.



Nurse must not alter Doctor clinical decisions or prescription details.



The existing shared token allocation and Doctor assignment logic must remain the source of truth.



PHC In-charge



Receives Nurse attendance and authorized facility-level operational summaries.



Can view facility-level bed occupancy and permitted nursing workload information.



Attendance approval, correction, and administrative actions remain governed by the PHC In-charge's own permissions.



Platform / Technical Administration



Use existing authentication, RBAC, audit, logging, and integration services.



Do not grant the Nurse administrative privileges.



---



8. DATABASE AND DATA MODEL



Inspect the existing schema before creating tables.



Reuse existing Patient, appointment, token, encounter, prescription, test-order, notification, attendance, and facility entities wherever possible.



Extend existing entities only when necessary.



If equivalent entities do not exist, design minimal backend entities such as:



Nurse Profile / Assignment



- Nurse ID.
- User ID.
- Assigned PHC ID.
- Assigned units or beds, if applicable.
- Role and permission references.
- Active status.
- Created and updated timestamps.



Nursing Observations



- Observation ID.
- Patient ID.
- Encounter ID.
- Nurse ID.
- Observation type.
- Value and unit.
- Recorded timestamp.
- Source and notes.
- Correction history or audit reference.



Test Results / Reports



- Result ID.
- Test order ID.
- Patient ID.
- Encounter ID.
- Recorded by.
- Result values and units.
- Secure attachment reference.
- Submission status.
- Doctor review status.
- Timestamps.



Nursing Tasks



- Task ID.
- Patient ID, if applicable.
- Encounter ID, if applicable.
- Assigned Nurse or unit.
- Task type.
- Source order or protocol reference.
- Status.
- Completion details.
- Audit timestamps.



Bed Assignments / Occupancy



- Bed ID.
- PHC ID.
- Assigned unit/Nurse where applicable.
- Patient/admission reference.
- Occupancy status.
- Start and end timestamps.
- Last updated by.
- Audit reference.



Attendance



Reuse the shared attendance model.



If extension is required, include Nurse ID, PHC ID, shift, check-in, check-out, submission status, approval reference, and correction audit.



Handover



- Handover ID.
- PHC ID.
- Nurse ID.
- Shift/date.
- Authorized pending task references.
- Receiving staff reference if supported.
- Status and timestamps.



AI Activity / Forecast



Store only necessary operational information, such as forecast period, model/version, source data timestamp, generated estimate, uncertainty information, and relevant audit reference.



Do not store unnecessary sensitive patient data in AI logs.



Database requirements



- Use primary keys and foreign keys.
- Enforce PHC-level and resource-level relationships.
- Add indexes for PHC, patient, encounter, date, token, status, and assigned Nurse as appropriate.
- Prevent duplicate reports and duplicate task submissions.
- Enforce concurrency-safe bed assignment and status transitions.
- Use transactions for multi-step clinical handoff operations.
- Add created_at and updated_at timestamps consistently.
- Preserve audit history for important clinical and operational changes.



Do not store sensitive clinical information in insecure client-side storage.



---



9. BACKEND APIs AND BUSINESS LOGIC



Inspect existing endpoints and service contracts first.



Reuse existing APIs where possible.



Do not create duplicate endpoints for existing Patient or Doctor services.



If new endpoints are required, follow the existing API conventions and authorization model.



Potential API capabilities include:



GET /api/nurse/dashboard



Purpose: Return authorized Nurse dashboard summaries, daily workload, and data freshness.



GET /api/nurse/queue



Purpose: Return assigned PHC's authorized patient queue and token information.



POST /api/nurse/arrivals



Purpose: Record verified patient arrival through an idempotent operation.



POST /api/nurse/observations



Purpose: Record authorized nursing observations linked to the correct encounter.



GET /api/nurse/test-orders



Purpose: Retrieve authorized test orders for assigned patients.



POST /api/nurse/test-results



Purpose: Record permitted test results.



POST /api/nurse/reports



Purpose: Securely upload and associate an authorized test report.



POST /api/nurse/reports/{reportId}/submit



Purpose: Submit a completed report to the responsible Doctor.



GET /api/nurse/reports/status



Purpose: Retrieve report submission and actual Doctor review status.



GET /api/nurse/beds



Purpose: Retrieve assigned beds and authorized occupancy status.



PATCH /api/nurse/beds/{bedId}/status



Purpose: Update an authorized bed status with backend concurrency validation.



POST /api/nurse/attendance/check-in



POST /api/nurse/attendance/check-out



POST /api/nurse/attendance/submit



Purpose: Record and submit Nurse attendance to the PHC In-charge.



GET /api/nurse/tasks



Purpose: Retrieve authorized nursing tasks and handover items.



POST /api/nurse/handover



Purpose: Create a shift handover through the authorized workflow.



POST /api/nurse/ai/assistant



Purpose: Provide Nurse-scoped AI operational assistance.



POST /api/nurse/ai/forecast



Purpose: Generate or retrieve an authorized patient workload forecast.



These are proposed capabilities, not instructions to duplicate existing endpoints. Adapt paths, request/response schemas, and HTTP methods to the actual backend architecture.



API requirements



Every endpoint must include:



- Authentication.
- Role-based authorization.
- PHC-level resource authorization.
- Request validation.
- Correct patient and encounter relationship validation.
- Consistent response format.
- Appropriate HTTP status codes.
- Actionable error messages.
- Audit logging for important operations.
- Idempotency for retryable operations where appropriate.



Never trust a patient ID, Nurse ID, PHC ID, Doctor ID, or bed ID merely because it was supplied by the frontend.



Resolve the authenticated user and permissions from the verified session/token.



---



10. UI/UX — STRICT PRESERVATION REQUIREMENTS



The existing UI/UX must not break, become inconsistent, or degrade in performance.



Visual consistency



- Reuse the existing design system and components.
- Match the Patient and Doctor modules' visual language.
- Reuse typography, color tokens, buttons, cards, forms, tables, modals, icons, and spacing.
- Avoid unnecessary redesign or decorative complexity.
- Use clear operational cards, status badges, and readable patient queues.
- Do not introduce a separate theme for the Nurse module.
- Preserve existing navigation and routing behavior.



Responsive design



The Nurse module must work on:



On mobile:



- Use touch-friendly controls.
- Display patient queue and test details in readable cards.
- Avoid horizontal overflow.
- Use responsive navigation consistent with the existing application.



On desktop:



- Use available screen space efficiently.
- Support readable tables, filters, and side navigation where already established.



Accessibility



- Maintain sufficient color contrast.
- Support keyboard navigation.
- Provide visible focus indicators.
- Use accessible labels and form descriptions.
- Support screen readers.
- Do not communicate status through color alone.
- Ensure Tamil text and glyphs render correctly.



Language support



Reuse the existing Tamil/English localization system.



Every new user-facing string must use the existing translation mechanism.



Do not hardcode only English text into components.



Ensure Tamil and English labels, buttons, errors, dates, units, and validation messages display correctly.



Required UI states



Every page and major component must handle:



- Loading.
- Empty data.
- API failure.
- Network interruption.
- Permission denied.
- Stale data.
- Successful save.
- Validation failure.
- Upload failure.
- Retry.
- Confirmation before consequential actions.



Use clear user-facing messages explaining what happened and what the Nurse should do next.



Never show a success toast before the backend confirms success.



---



11. SECURITY, PRIVACY AND AUDIT



Security is mandatory.



Implement:



- Existing authentication and secure session handling.
- Server-side RBAC and PHC-level resource authorization.
- Least-privilege access.
- Input validation and output encoding.
- Protection against SQL/NoSQL injection and XSS.
- CSRF protection where applicable.
- Rate limiting on sensitive endpoints.
- Secure file upload and storage.
- Encryption in transit and appropriate encryption at rest.
- Secure secrets management.
- Privacy-aware AI data handling.
- Audit logs for clinical records, test results, report submission, bed changes, attendance, and permission-sensitive actions.



Audit records should capture the authenticated actor, action, resource, timestamp, and relevant change metadata without unnecessarily duplicating sensitive clinical content.



Do not expose authentication tokens, passwords, secrets, or sensitive patient information in logs.



Do not send unrestricted patient records to external AI services.



Use only the minimum authorized information required for a specific AI task.



Use synthetic data in demo environments and prevent demo data from being confused with production clinical records.



Before production deployment, ensure the application is reviewed against applicable healthcare privacy, data protection, and security requirements.



---



12. FAILURE HANDLING AND EDGE CASES



Handle these scenarios gracefully:



1. Nurse loses internet while entering observations.
2. Backend fails during report upload.
3. Doctor is unavailable when a report is submitted.
4. Patient arrives with an invalid or duplicate token.
5. Patient identity does not match the selected encounter.
6. Nurse attempts to access another PHC.
7. Two Nurses attempt to assign the same bed simultaneously.
8. Bed status becomes stale or conflicts with an active admission.
9. Test result is incomplete or invalid.
10. Nurse attempts to submit a report twice.
11. Doctor report review notification fails.
12. Attendance check-in or check-out fails.
13. AI service is unavailable or returns invalid output.
14. Historical data is insufficient for forecasting.
15. A Nurse's assignment or permissions are revoked during a session.
16. File upload contains an unsupported or malicious file.
17. Patient has no appointment but requires authorized walk-in handling.
18. PHC has no configured beds or no configured routine tests.



Provide clear recovery steps.



Use safe retries and idempotency for operations that may be repeated.



Never fabricate data, silently discard clinical records, falsely mark reports as submitted, or show unconfirmed bed availability.



For interrupted data entry, provide a safe recovery mechanism that respects the application's security and privacy architecture.



Do not store sensitive clinical drafts insecurely in browser local storage.



---



13. PERFORMANCE AND SCALABILITY



Optimize the Nurse module for low-end mobile devices and unreliable network conditions.



Requirements:



- Avoid unnecessary API calls and duplicate data fetching.
- Use pagination or appropriate server-side filtering for large patient queues.
- Load dashboard summaries efficiently.
- Avoid fetching unrestricted patient histories.
- Use indexes for common PHC, date, token, encounter, and status queries.
- Optimize report upload and file retrieval.
- Prevent duplicate requests caused by repeated button clicks.
- Use background jobs or queues for notifications, forecasting, and other non-blocking work where justified by the existing architecture.
- Keep normal nursing workflows functional without AI.
- Use caching only where appropriate and never cache sensitive records insecurely.



Start with the simplest architecture compatible with the existing application.



Do not introduce microservices, additional infrastructure, or complex event streaming solely for this role unless actual requirements justify them.



---



14. TESTING REQUIREMENTS



Write and run tests using the existing project testing framework.



Unit tests



- Nurse permission checks.
- Patient and encounter validation.
- Observation validation.
- Test result validation.
- Bed status transitions.
- Attendance state transitions.
- AI scope restrictions.



Integration tests



- Patient appointment/token to Nurse queue.
- Nurse observations to Doctor consultation.
- Doctor-issued test order to Nurse test workflow.
- Nurse report submission to Doctor dashboard.
- Doctor report review status back to Nurse.
- Nurse attendance to PHC In-charge.
- Assigned bed updates and In-charge visibility.



Security tests



- Nurse cannot access another PHC.
- Nurse cannot create or modify prescriptions.
- Nurse cannot access unauthorized patient records.
- Nurse cannot mark Doctor reports as reviewed.
- Nurse cannot access administrative supply chain modules.
- Unauthorized file access is rejected.
- Frontend permission bypass does not bypass backend authorization.



Workflow and edge-case tests



- Duplicate token and arrival handling.
- Duplicate report submission.
- Concurrent bed assignment.
- Failed report upload and retry.
- Missing or incorrect test result.
- Network interruption.
- AI timeout.
- Attendance duplicate check-in.
- Unauthorized patient/encounter mismatch.



UI/UX tests



- Mobile, tablet, and desktop layouts.
- Tamil and English localization.
- No overflow or broken navigation.
- Loading, empty, success, and error states.
- Keyboard and screen-reader accessibility.
- Existing Patient and Doctor workflows remain functional.



---



15. IMPLEMENTATION ROADMAP



Implement progressively.



Phase 1 — Core Nurse MVP



- Role-based Nurse dashboard.
- Integration with existing Patient queue and token system.
- Patient arrival and authorized preparation.
- Vitals and nursing observation entry.
- Doctor-issued test order visibility.
- Authorized test result entry and report handoff.
- Assigned bed status management.
- Attendance submission to PHC In-charge.
- Backend validation, permissions, and audit.
- Mobile-responsive Tamil/English UI.



Phase 2 — Enhanced Nursing Operations



- Patient forecast using available historical data.
- Advanced queue filtering.
- Test/report review tracking.
- Nursing task management.
- Shift handover.
- Notifications and safe retries.
- Operational history and reports.



Phase 3 — Nurse Intelligence



- Nurse-specific AI Assistant.
- Workload summaries and forecast evaluation.
- Missing report and incomplete task detection.
- Bed status anomaly reminders.
- AI-assisted shift handover.
- Explainable, advisory-only operational recommendations.



Phase 4 — Production Readiness



- Security and privacy review.
- Performance optimization.
- Robust offline and recovery behavior.
- Monitoring, alerting, backup, and recovery.
- Load and concurrency testing.
- Production deployment readiness.



Do not implement advanced AI or infrastructure at the cost of a reliable core nursing workflow.



---



16. FINAL ACCEPTANCE CRITERIA



The Nurse module is complete only when all applicable criteria are satisfied:



1. Nurse can enter the existing application through the correct role and authorization mechanism.
2. Existing Patient and Doctor modules continue to work.
3. Nurse sees authorized daily patient bookings, actual arrivals, and appropriately labeled forecasts.
4. Nurse can manage the assigned token queue and patient preparation.
5. Nurse can record authorized observations and nursing care.
6. Nurse can view authorized Doctor test orders and record permitted test results.
7. Nurse can securely upload and submit reports to the correct Doctor.
8. Nurse can track actual report submission and Doctor review status.
9. Nurse can manage assigned beds with concurrency-safe validation.
10. Nurse attendance reaches the PHC In-charge through the authorized workflow.
11. Nurse AI is limited to authorized nursing and operational tasks.
12. No AI diagnosis, prescribing, dosage changes, or autonomous clinical decisions.
13. All major actions have backend validation, permission checks, and appropriate audit trails.
14. UI/UX remains consistent, responsive, accessible, and bilingual.
15. Loading, empty, error, offline, and recovery states work correctly.
16. Tests verify the major workflows, security boundaries, and regressions.
17. No fabricated patient, report, bed, attendance, or AI success data is presented as real.



---



17. REQUIRED CODING AGENT DELIVERABLES



Before coding, provide a short inspection summary:



- Existing technology stack.
- Existing Patient and Doctor integration points.
- Existing reusable components and APIs.
- Files/modules expected to change.
- Any missing backend services or dependencies.



Then implement the Nurse module in small, verifiable steps.



After implementation, provide:



1. Summary of completed functionality.
2. List of created and modified files.
3. Database changes and migration instructions.
4. API endpoints added or reused.
5. Environment variables or dependencies required.
6. Tests executed and actual results.
7. Known limitations and remaining integration work.
8. Instructions to run and verify the Nurse workflow locally.



Do not claim production readiness if authentication, database persistence, authorization, or required integrations are still mocked.



Final instruction: Build Nurse Role 03 as a practical, secure, fully integrated PHC nursing operations module. Preserve the existing application and its UI/UX. Prioritize correct patient handling, token-based preparation, authorized routine testing, Doctor report handoff, assigned bed management, attendance reporting, and a strictly Nurse-specific AI Assistant.



The final experience should be simple enough for real healthcare staff to use on mobile devices, reliable under poor network conditions, and architected to support the larger Smart Health and Supply Chain Resilience platform without giving the Nurse unauthorized access to other roles or modules.




# 6. ROLE 04 — PHC In-charge / Facility Manager


**Role purpose (master summary):** PHC-level operational supervisor responsible for facility administration, coordination, monitoring, authorized approvals, readiness, shortages, reporting, and district coordination.


### Detailed requirements from the uploaded role specification


ROLE 04 — PHC IN-CHARGE / FACILITY MANAGER



You are a senior full-stack engineer, product architect, AI engineer, UX designer, security engineer, and healthcare workflow specialist.



Your task is to implement Role 04 — PHC In-charge / Facility Manager as a complete, functional, production-oriented module within the existing Smart Health and Supply Chain Resilience PWA.



This is not a request to create a static dashboard or a disconnected UI prototype. Build a working, integrated module that uses the existing project architecture, shared database, authentication, authorization, APIs, and design system.



Follow this principle:



REAL PHC OPERATIONS → REAL USER WORKFLOWS → SHARED DATA → ACTIONABLE DASHBOARD → ROLE-SPECIFIC AI → SECURE DISTRICT COORDINATION.



---



1. PROJECT CONTEXT



The project is a Smart Health and Supply Chain Resilience platform designed to support healthcare facilities, particularly Primary Health Centres (PHCs), through digital operations, resource visibility, medicine supply chain management, operational reporting, and AI-assisted decision support.



The platform follows this administrative structure:



National → State → District → PHC.



The application contains 13 logical application roles:



1. Patient
2. Doctor / Medical Officer
3. Nurse / Healthcare Staff
4. PHC In-charge / Facility Manager
5. Pharmacist / PHC Storekeeper
6. District Health Officer (DHO)
7. District Supply Chain Officer
8. District Emergency Coordinator
9. State Health Administrator
10. State Supply Chain / Warehouse Manager
11. State Public Health Analyst
12. National Health Authority / Central Administrator
13. National Platform Administrator / Super Admin



Role 04 is the PHC-level operational supervisor.



Do not introduce a separate AI Administrator or Data / Integration Officer application role. The platform has only the 13 agreed logical roles. Platform-level technical administration remains within the defined Super Admin scope.



The PHC In-charge is not the owner of every clinical or inventory transaction. They supervise, coordinate, review, approve authorized operational requests, and report PHC-level performance.



---



2. FIRST ACTION — INSPECT THE EXISTING PROJECT



Before writing or modifying any code, thoroughly inspect the current repository.



Identify:



- Frontend framework, build tools, and routing.
- Existing application entry points and layout.
- Current design system, typography, colors, spacing, icons, and components.
- Existing Patient, Doctor, and Nurse modules.
- Existing authentication, demo login, user context, and role selection.
- Existing database schema, backend APIs, services, and data models.
- Existing AI assistant implementation and integrations.
- Existing notification, reporting, and file-upload systems.
- Current responsive layout and PWA configuration.
- Existing shared state management and data-fetching conventions.
- Existing validation, authorization, and error-handling mechanisms.



Create an implementation plan based on what actually exists.



Mandatory preservation rules



1. Do not rebuild the entire application.
2. Do not replace the current frontend framework, backend, database, or design system unnecessarily.
3. Do not delete, rename, or break working Patient, Doctor, or Nurse functionality.
4. Do not duplicate existing appointment, consultation, inventory, or attendance systems.
5. Reuse existing components, shared services, schemas, and APIs wherever appropriate.
6. Extend existing models and endpoints through backward-compatible changes.
7. Do not introduce mock data into production functionality.
8. Do not create duplicate records to display the same data in different roles.
9. Do not remove existing features just to simplify implementation.
10. If a required backend service does not exist, implement it using the current architecture rather than simulating a successful backend operation.



If a feature depends on an external integration that is not configured, provide a clearly labeled unavailable or integration-pending state. Never pretend that a real external service is connected.



Maintain a clear separation between development/demo functionality and production functionality.



---



3. ROLE 04 — OFFICIAL PRODUCT DEFINITION



Role Name: PHC In-charge / Facility Manager.



Definition:



The PHC In-charge is responsible for supervising, coordinating, monitoring, and managing the overall daily administrative and operational functioning of an assigned Primary Health Centre.



The In-charge receives operational data from the PHC's shared system, reviews facility performance, monitors staff availability, oversees bed and facility readiness, reviews medicine and supply shortages, approves authorized operational requests, and submits reports or escalations to the appropriate District authorities.



The In-charge is NOT:



- A Doctor or clinical decision-maker.
- A Nurse performing nursing procedures.
- A Pharmacist performing inventory transactions.
- A District Health Officer.
- A District Supply Chain Officer.
- A National Platform Administrator.



The In-charge must not perform or overwrite responsibilities owned by these other roles.



---



4. PRIMARY OBJECTIVES



Build the In-charge module to accomplish the following:



1. Provide one consolidated overview of the assigned PHC.
2. Show actual daily patient footfall and consultation progress.
3. Monitor Doctor, Nurse, Pharmacist, and other authorized staff availability.
4. Review attendance submissions and manage authorized attendance corrections.
5. Monitor bed availability and facility readiness.
6. Review medicine and medical supply shortage summaries.
7. Review and authorize replenishment requests within configured permissions.
8. Route reports and requests to the correct District officers.
9. Track submitted reports, approvals, escalations, and pending actions.
10. Provide a dedicated In-charge Personal AI Assistant.
11. Make operational information understandable for non-technical users.
12. Work reliably on mobile devices and low-bandwidth networks.
13. Preserve privacy, security, auditability, and human decision-making.



---



5. ROLE 04 DASHBOARD AND NAVIGATION



Create a dedicated role-specific dashboard.



Use the existing application's navigation and design system.



Suggested navigation:



1. PHC Overview
2. Patient Footfall & Queue
3. Staff & Attendance
4. Bed & Facility Management
5. Medicine & Supply Oversight
6. Approvals & Requests
7. Reports & District Communication
8. Alerts & Escalations
9. In-charge AI Assistant
10. Profile, Language, and Settings



Use the existing navigation style if one already exists.



Do not introduce an entirely different visual language for this role.



Dashboard header



Display:



- Assigned PHC name and facility identifier.
- Facility location and assigned District.
- Current date and operational reporting period.
- Logged-in In-charge name and role.
- Current data synchronization status.
- Last successful data refresh time.
- Notification and alert access.
- Language selection using the existing language settings.



The user must always know which PHC they are managing.



Never allow a PHC In-charge to switch to an unauthorized PHC merely by changing a URL, identifier, or frontend selection.



---



6. PHC OVERVIEW DASHBOARD



The dashboard is the primary operational workspace.



It must use actual shared backend data.



A. Patient Footfall



Display:



- Total unique patient visits checked in today.
- Patients currently waiting for Doctor consultation.
- Consultations currently in progress.
- Consultations completed today.
- Visits with pending nursing or other required services.
- Visits fully completed, where the workflow supports that status.
- Daily, weekly, and monthly patient footfall trends.
- Comparison with previous periods where reliable data is available.



Distinguish patient visits from unique individual patients.



A patient attending twice on separate encounters must not be counted as one visit.



Prevent duplicate counts caused by retries, repeated events, or multiple dashboard refreshes.



B. Doctor-wise Operational Summary



For each authorized Doctor assigned to the PHC, display:



- Doctor name and designation.
- Duty status and attendance status.
- Number of assigned visits.
- Number of consultations completed.
- Number of consultations in progress.
- Number of visits waiting for consultation.
- Operational workload indicators.
- Relevant pending handoffs or tasks.



Only display clinical information where explicitly authorized and necessary for facility operations.



Do not expose unrestricted clinical notes or detailed medical histories on the In-charge dashboard.



C. PHC Operational Alerts



Display relevant alerts such as:



- High patient waiting volume.
- Unusual workload concentration.
- Doctor or Nurse duty coverage gaps.
- Delayed operational tasks.
- Pending attendance approvals.
- Critical medicine shortages.
- Bed or facility availability issues.
- Pending reports and overdue requests.
- Data synchronization failures.



Each alert must show:



- Alert category.
- Affected facility or resource.
- Source and timestamp.
- Severity defined by approved business rules.
- Recommended operational action.
- Assigned responsible role.
- Current status.



Do not invent numerical thresholds. Use configurable thresholds and clearly label default or demo configurations.



---



7. SHARED PATIENT WORKFLOW AND DATA VISIBILITY



This is one of the most important integration requirements.



The Patient, Doctor, Nurse, Pharmacist, and In-charge modules must use a shared patient visit / encounter workflow.



Do not create a separate In-charge patient database or a duplicate consultation tracking system.



Patient workflow



Patient appointment or walk-in registration
→ Patient arrival / check-in
→ Nurse preparation and authorized vitals
→ Doctor consultation
→ Prescription, referral, or follow-up where applicable
→ Pharmacy and other required services
→ Visit completion according to the configured workflow.



Data ownership



Patient arrival and check-in:



- Recorded by the existing authorized arrival or reception workflow.



Nurse preparation:



- Recorded by the Nurse module.



Consultation:



- Recorded by the Doctor module.



Prescription:



- Created and maintained by the authorized Doctor.



Dispensing:



- Recorded by the Pharmacist module.



Visit status:



- Derived from the authoritative shared encounter workflow.



In-charge visibility



When the Doctor marks a consultation as completed, the system must update the shared encounter record.



The In-charge dashboard must reflect that completion without requiring manual re-entry.



The Nurse must see the consultation status and relevant handoff information for authorized nursing workflow.



The In-charge must see the aggregate operational counts and appropriate facility-level details.



Implement real-time updates using the existing WebSocket, server-sent event, polling, or data-fetching infrastructure. If real-time infrastructure does not exist, implement safe, configurable refresh and show the last updated timestamp.



Never display stale information as live information.



Required distinctions



Maintain separate statuses for:



- Arrived.
- Waiting for Nurse preparation.
- Waiting for Doctor.
- Consultation in progress.
- Consultation completed.
- Additional services pending.
- Visit completed.
- Cancelled or no-show, where supported.



Do not treat consultation completion as automatic completion of the entire PHC visit.



Do not allow the In-charge to modify clinical encounter status arbitrarily.



Any authorized correction must use a controlled, audited workflow.



---



8. STAFF MANAGEMENT AND ATTENDANCE



Build a Staff & Attendance module.



Staff overview



Display authorized PHC staff, including:



- Doctors.
- Nurses and healthcare staff.
- Pharmacists.
- Other configured facility staff.



Show:



- Staff name and role.
- Assigned duty or shift.
- Attendance status.
- Check-in and check-out timestamps.
- Leave or approved absence status.
- Duty coverage gaps.
- Pending attendance corrections.



Use existing staff and attendance records.



Attendance workflow



1. Staff members record their own authorized check-in and check-out.
2. The system records timestamps and relevant audit information.
3. The In-charge views the attendance submissions.
4. The In-charge reviews and approves, rejects, or requests correction according to configured permissions.
5. The system records the decision, reviewer, timestamp, and reason where applicable.
6. Attendance summaries become available to authorized District administrators.



Logging in to the application must not automatically count as attendance.



Do not silently fabricate attendance records.



Do not allow the In-charge to modify attendance without recording an audit trail.



Duty roster



If roster functionality exists, integrate with it.



If not, implement a basic roster management workflow:



- View assigned shifts.
- Create or modify authorized PHC-level schedules.
- Identify coverage gaps.
- Record duty changes and reasons.
- Notify affected staff.



District-level reassignment or transfers must require the appropriate District authority.



The In-charge must not alter official staff postings or override higher-level authorization.



---



9. BED AND FACILITY MANAGEMENT



Create a facility-level oversight module.



Bed overview



Display:



- Total configured beds.
- Occupied beds.
- Vacant beds.
- Beds under cleaning.
- Unavailable beds.
- Bed occupancy percentage.
- Last status update.
- Beds with stale or conflicting status.



Use Nurse and authorized facility updates as the source of truth.



The In-charge reviews and monitors facility-level status.



Do not allow the In-charge dashboard to create conflicting bed assignments.



Prevent double assignment through backend validation and concurrency-safe transactions.



Bed configuration



If authorized, allow the In-charge to manage the PHC's configured bed capacity and facility status according to the application's permissions.



Any capacity changes must be audited and must not silently overwrite existing occupied-bed records.



If beds are not configured for a PHC, show:



"Bed configuration has not been set up for this facility."



Do not display fabricated bed counts.



Facility readiness



Include operational tracking for:



- Medical equipment availability.
- Equipment maintenance requests.
- Water and electricity issues.
- Cleanliness and sanitation issues.
- Facility infrastructure problems.
- Emergency readiness checklist.
- Facility complaints and unresolved issues.



Allow authorized staff to submit issues.



The In-charge can:



- Review the issue.
- Assign it to an authorized responsible person.
- Set or update its status.
- Record actions taken.
- Escalate unresolved issues to the appropriate District authority.



Do not claim that the system independently verifies physical facility conditions.



Show who reported a condition and when it was last updated.



---



10. MEDICINE AND MEDICAL SUPPLY OVERSIGHT



Integrate with the existing Pharmacist and Supply Chain modules.



Do not create a separate inventory transaction system inside the In-charge module.



Pharmacist responsibilities



The Pharmacist remains the operational owner of:



- Medicine stock updates.
- Goods receipt and stock issue.
- Dispensing.
- Batch and expiry records.
- Inventory reconciliation.
- Stock adjustment workflows.
- Medicine-level transaction records.



In-charge responsibilities



The In-charge must be able to:



- View authorized PHC stock summaries.
- View low-stock and stock-out alerts.
- View near-expiry summaries.
- Review replenishment requests.
- Review requested quantities and reasons.
- Approve, reject, or request revision of requests within configured permissions.
- Escalate critical shortages.
- Monitor pending requests and delivery status.
- View supply chain issues affecting PHC operations.



The In-charge must not:



- Dispense medicines.
- Record pharmacy transactions on behalf of the Pharmacist.
- Change stock quantities directly.
- Change batch or expiry data.
- Falsify or override inventory records.
- Independently allocate District or State warehouse stock.
- Approve requests beyond authorized limits.



Medicine replenishment workflow



Pharmacist records stock
→ Inventory service evaluates configured thresholds
→ Shortage alert generated
→ Pharmacist creates replenishment request
→ In-charge reviews and authorizes where required
→ Request routed to District Supply Chain Officer
→ District officer reviews allocation and availability
→ Dispatch and delivery status updated
→ Pharmacist confirms actual receipt
→ Inventory stock updated through the authorized receipt transaction.



A stock request must have a unique identifier and maintain status history.



Suggested statuses:



- Draft.
- Submitted.
- Pending In-charge Review.
- Approved.
- Rejected.
- Sent to District.
- Under District Review.
- Approved for Allocation.
- Dispatched.
- Partially Delivered.
- Delivered.
- Closed.



Use the existing status model if available.



Support direct pharmacist-to-District shortage alerts for urgent operational visibility, while preserving mandatory approval controls for requests that require In-charge authorization.



An alert is not an approved purchase or allocation request.



Never mark a medicine as received simply because a delivery is marked dispatched.



---



11. REPORTING AND DISTRICT COMMUNICATION



Build a complete reporting and escalation workflow.



The In-charge must be able to send appropriate information to:



Role 06 — District Health Officer (DHO).



Role 07 — District Supply Chain Officer.



Role 08 — District Emergency Coordinator.



The system must automatically identify the appropriate District officers based on the authenticated PHC's assigned District and the configured reporting hierarchy.



Do not let the In-charge send sensitive facility information to arbitrary users or unrelated Districts.



A. DHO Reports



Include:



- Daily patient footfall.
- Consultation completion and waiting summaries.
- Staff attendance and duty coverage.
- Bed availability and occupancy.
- Facility readiness.
- Operational issues.
- Complaints and unresolved tasks.
- PHC performance indicators.
- Required District-level support.



B. District Supply Chain Reports



Include:



- Medicine stock-out alerts.
- Low-stock and critical shortage summaries.
- Approved replenishment requests.
- Requested quantities and supporting information.
- Pending deliveries.
- Supply chain issues affecting patient services.



C. District Emergency Coordinator Reports



Include:



- Facility emergency readiness gaps.
- Urgent equipment or infrastructure problems.
- Critical staffing or facility disruptions.
- Emergency-related operational escalations.
- Current response status and support requested.



Do not include unnecessary patient-identifiable clinical information in routine administrative reports.



Report submission workflow



1. The system generates a report from authorized source data.
2. The In-charge reviews the report.
3. The In-charge can add explanations or supporting information.
4. The In-charge submits the report.
5. The system records the submission timestamp and recipient.
6. The receiving District officer sees the report in their dashboard.
7. The District officer can acknowledge, request clarification, assign action, or update resolution status.
8. The In-charge sees the response and tracks the issue to closure.



Provide report status:



- Draft.
- Pending Review.
- Submitted.
- Acknowledged.
- Clarification Requested.
- Action Assigned.
- Resolved.
- Closed.



Reports must preserve a history of changes and submissions.



Never silently overwrite a previously submitted report.



---



12. IN-CHARGE PERSONAL AI ASSISTANT



Implement a dedicated AI assistant specifically for the PHC In-charge.



This is a core feature, not an optional decorative chatbot.



Name it:



"PHC In-charge AI Assistant"



Its purpose is to help the In-charge understand the PHC's current operational condition, identify pending work, prepare reports, and obtain actionable administrative summaries.



It is not a clinical assistant.



AI capability 1 — Daily Operations Summary



The In-charge can ask:



- "How many patients visited our PHC today?"
- "How many consultations have been completed?"
- "How many patients are waiting for a Doctor?"
- "How many visits are still pending?"
- "Which Doctor has the highest pending workload?"
- "What are today's important operational issues?"
- "Which reports or approvals are overdue?"



The assistant must retrieve actual authorized system data.



Never invent counts, statuses, staff attendance, stock quantities, or patient information.



When data is unavailable, explicitly say that the data is unavailable or was last synchronized at the displayed timestamp.



AI capability 2 — Workload and Staffing Support



The assistant may:



- Summarize Doctor-wise workload.
- Highlight staff coverage gaps.
- Identify unusually high waiting volumes based on configured rules.
- Summarize pending nursing handoffs and operational tasks.
- Suggest that the In-charge review staffing or duty coverage.



It must not independently reassign Doctors, change rosters, approve leave, or determine clinical priority.



AI capability 3 — Medicine and Supply Summary



The assistant may:



- Summarize current stock-out and low-stock alerts.
- Identify pending replenishment requests.
- Explain request and delivery statuses.
- Highlight shortages that may affect facility operations.
- Draft a supply-related report to the District Supply Chain Officer.



The assistant must use actual inventory and supply request data.



It must not create or approve stock transactions or change inventory quantities autonomously.



AI capability 4 — Bed and Facility Summary



The assistant may:



- Summarize bed occupancy and availability.
- Highlight stale or conflicting bed status.
- Summarize equipment or infrastructure issues.
- Identify unresolved facility maintenance requests.
- Suggest operational follow-up.



It must not autonomously assign beds, change occupancy status, or make clinical admission decisions.



AI capability 5 — Report Drafting



The assistant may generate draft:



- Daily operational reports.
- Weekly PHC summaries.
- Staff availability reports.
- Facility readiness reports.
- District escalation messages.
- Supply shortage summaries.



The In-charge must review and explicitly approve a report before submission.



AI capability 6 — Natural Language Interaction



Provide a chat interface supporting questions in Tamil and English.



Use the application's existing language and AI integration where available.



The assistant should:



- Understand simple administrative questions.
- Respond in the user's selected language.
- Provide concise, structured summaries.
- Show relevant reporting period.
- Explain which source data was used.
- Offer navigation to the relevant dashboard or report.
- Preserve useful conversation history according to privacy and retention settings.
- Allow clearing the conversation.



Do not send unrestricted PHC data or all patient records to an external AI provider.



Use authorized, minimal, purpose-specific data retrieval.



AI architecture



Use a controlled AI tool-calling or backend service architecture.



Suggested tools:



- get_phc_daily_summary.
- get_patient_footfall.
- get_consultation_counts.
- get_doctor_workload_summary.
- get_staff_attendance_summary.
- get_bed_availability.
- get_facility_issue_summary.
- get_medicine_shortage_summary.
- get_pending_supply_requests.
- get_pending_approvals.
- get_district_report_status.
- generate_operational_report_draft.



All tools must enforce backend authorization.



Never trust a PHC identifier supplied by the AI or user without validating it against the authenticated user's assigned facility.



Use server-side aggregation for numeric summaries.



AI must not independently calculate authoritative operational totals from incomplete natural-language context.



AI safety



The AI must never:



- Diagnose patients.
- Prescribe medicines or dosages.
- Make treatment decisions.
- Triage patients or determine emergency severity.
- Make autonomous staff attendance decisions.
- Approve supply requests without explicit authorization.
- Change medicine inventory.
- Assign beds or make admission decisions.
- Submit reports without human confirmation.
- Hide missing or stale data.
- Claim that an action succeeded unless the backend confirms success.



All AI suggestions must be advisory.



Provide clear loading, unavailable, error, and retry states.



If the AI service fails, the standard PHC dashboard must continue to work.



---



13. ROLE-BASED ACCESS CONTROL



Implement strict server-side RBAC and facility-level authorization.



The In-charge may access only:



- Their assigned PHC.
- Authorized staff operational information.
- Facility-level patient flow summaries.
- Authorized facility reports.
- Facility bed and readiness information.
- Authorized medicine summaries and requests.
- Reports and escalations within their District reporting scope.



The In-charge must not access:



- Other PHCs without explicit authorization.
- Unrestricted patient clinical records.
- Other Districts' operational data.
- State or National administrative configuration.
- Unauthorized inventory transactions.
- Super Admin technical settings.



Every API must validate:



- Authenticated user.
- Assigned role.
- Assigned PHC.
- Applicable District.
- Resource ownership.
- Required action permission.
- Current record status.



Do not rely only on frontend route protection.



Prevent insecure direct object reference vulnerabilities.



---



14. DATA MODEL AND BACKEND INTEGRATION



Inspect existing schemas first.



Reuse existing entities and relationships wherever possible.



Do not create duplicate entities when an equivalent model exists.



Required logical entities may include:



- Users.
- Roles and permissions.
- States.
- Districts.
- PHCs / Facilities.
- Staff assignments.
- Attendance records.
- Duty rosters.
- Patient visits / encounters.
- Consultation status records.
- Bed configurations and bed status.
- Facility issues.
- Inventory summaries.
- Supply requests.
- Report submissions.
- Escalations.
- Notifications.
- Audit logs.



Every relevant entity should have appropriate:



- Unique identifiers.
- Relationships.
- Status fields.
- Created and updated timestamps.
- Actor identifiers.
- Authorization constraints.
- Audit history where needed.



Use server-side transactions for critical updates.



Prevent duplicate report submissions and duplicate supply requests through idempotency keys and backend validation.



Use concurrency-safe updates for approvals, stock requests, and bed-related operations.



Never allow frontend-supplied totals to become authoritative database values.



---



15. IMPORTANT API REQUIREMENTS



Adapt these to the existing backend conventions. Do not create duplicate APIs if equivalent endpoints already exist.



Suggested endpoints:



GET /api/phc/in-charge/dashboard



Purpose: Retrieve the assigned PHC's authorized operational summary.



GET /api/phc/in-charge/patient-flow



Purpose: Retrieve patient arrival, waiting, consultation, and completion counts.



GET /api/phc/in-charge/staff



Purpose: Retrieve authorized PHC staff and attendance summaries.



POST /api/phc/in-charge/attendance/{attendanceId}/review



Purpose: Review an attendance submission.



POST /api/phc/in-charge/roster



Purpose: Create or update an authorized PHC duty roster.



GET /api/phc/in-charge/beds



Purpose: Retrieve configured bed availability and status.



GET /api/phc/in-charge/facility-issues



Purpose: Retrieve facility issues and maintenance status.



POST /api/phc/in-charge/facility-issues/{issueId}/assign



Purpose: Assign an authorized facility issue.



GET /api/phc/in-charge/supply-requests



Purpose: Retrieve facility supply requests.



POST /api/phc/in-charge/supply-requests/{requestId}/review



Purpose: Approve, reject, or request revision according to permissions.



POST /api/phc/in-charge/reports



Purpose: Submit an authorized reviewed report.



GET /api/phc/in-charge/reports



Purpose: Retrieve report history and District responses.



POST /api/phc/in-charge/escalations



Purpose: Create an authorized District escalation.



POST /api/phc/in-charge/ai/chat



Purpose: Process authorized In-charge AI queries using controlled tools.



For each endpoint, implement:



- Request validation.
- Authentication.
- Server-side authorization.
- Correct status codes.
- Structured errors.
- Audit logging for sensitive actions.
- Safe retries.
- Idempotency where applicable.



Use the existing API versioning and response conventions.



---



16. NOTIFICATIONS AND ALERTS



Integrate with the existing notification system.



Provide in-app notifications for:



- Pending attendance approvals.
- New facility issues.
- Supply requests requiring review.
- District responses.
- Report acknowledgment.
- Report clarification requests.
- Critical shortage alerts.
- Emergency-related operational escalations.
- Data synchronization issues.



Notifications must route only to authorized users.



Support read/unread status and notification history.



Avoid excessive or duplicate notifications.



Use configurable severity and escalation rules.



Do not send patient-sensitive data in notification previews unless explicitly authorized.



SMS, WhatsApp, email, or push integrations must only be implemented when properly configured and authorized.



Never claim that an external notification was sent unless the provider confirms success.



---



17. UI/UX AND ACCESSIBILITY REQUIREMENTS



Preserve the existing application's design system and established visual identity.



The In-charge module must feel like a natural extension of the Patient, Doctor, and Nurse modules.



Responsive design



Support:



Use mobile-first layouts.



On mobile:



- Use compact summary cards.
- Keep primary actions easy to reach.
- Use responsive tables or cards.
- Avoid horizontal overflow.
- Use accessible touch targets.
- Avoid excessive nested navigation.



On desktop:



- Use an efficient administrative dashboard.
- Support readable tables, filtering, and drill-down views.
- Keep important status and actions visible.



Design requirements



- Consistent typography.
- Consistent spacing and colors.
- Consistent card, button, modal, and form styles.
- Clear visual hierarchy.
- Accessible color contrast.
- Meaningful icons.
- Clear status labels.
- No excessive gradients or decorative elements.
- No unnecessary animations.
- Avoid overcrowded dashboards.



Use the existing icon library and component system.



Do not introduce a new component library unless necessary.



Required UI states



Every data-driven page must support:



- Loading.
- Empty state.
- Error.
- Retry.
- Offline.
- Stale data.
- Permission denied.
- Successful action.
- Validation error.
- Pending approval.
- Confirmation before irreversible action.



Use confirmation dialogs for sensitive or irreversible actions.



Provide actionable error messages.



For example:



"Report submission failed. Your draft has been saved. Please retry when the connection is restored."



Never clear a user's entered data because of a temporary network error.



Localization



Support Tamil and English using the existing localization architecture.



All important user-facing labels, forms, alerts, validation messages, and AI responses must support the selected language.



Do not hardcode all text directly into components if the application already uses localization files.



Use clear and familiar terminology suitable for PHC staff.



---



18. OFFLINE AND LOW-CONNECTIVITY SUPPORT



PHCs may experience poor or interrupted connectivity.



Implement appropriate offline behavior using the existing PWA architecture.



Requirements:



- Cache the application shell and approved static assets.
- Show when the device is offline.
- Display the last successful synchronization time.
- Allow safe viewing of appropriately cached, authorized operational summaries where privacy permits.
- Queue only approved and safe operations for synchronization.
- Prevent duplicate submissions during retries.
- Resolve conflicting updates through explicit reconciliation.
- Preserve drafts during network failures.
- Never show stale data as current.
- Never claim a report or approval has reached the District until the backend confirms it.



Do not cache unrestricted clinical records or sensitive data insecurely.



Use secure storage and data minimization.



---



19. SECURITY, PRIVACY, AND AUDITABILITY



Implement security as a core requirement.



Authentication



Use the existing authentication system.



Do not introduce a separate production login system unnecessarily.



Demo authentication must be clearly labeled as demo-only.



Authorization



Use backend RBAC, PHC scope, District scope, and resource-level access controls.



Never rely on hidden frontend buttons as a security mechanism.



Data protection



- Encrypt data in transit.
- Use appropriate encryption at rest.
- Protect session tokens and secrets.
- Avoid exposing sensitive information in URLs or logs.
- Validate all input on the backend.
- Prevent injection and insecure file access.
- Apply rate limiting to sensitive endpoints.
- Protect AI tool calls with the same authorization rules as standard APIs.



Audit logging



Record relevant events:



- Attendance approvals and rejections.
- Roster changes.
- Facility issue assignments and escalations.
- Supply request approvals and rejections.
- Report submissions and revisions.
- Permission-sensitive actions.
- Relevant data corrections.



Audit entries should include:



- Actor.
- Action.
- Resource.
- Timestamp.
- Previous and new values where appropriate.
- Reason for sensitive changes.



Audit logs must not be editable by ordinary In-charge users.



Do not log passwords, tokens, or unnecessary patient clinical data.



---



20. PERFORMANCE AND SCALABILITY



Design the module to support growth from a small number of PHCs to a large multi-State platform.



Do not over-engineer the MVP.



Requirements:



- Use paginated APIs for large tables.
- Filter and aggregate data on the backend.
- Avoid fetching every patient record just to calculate dashboard totals.
- Use indexed database queries for PHC, District, date, status, and resource identifiers.
- Cache only safe, appropriately scoped summaries.
- Invalidate or refresh cached summaries when relevant data changes.
- Use background jobs for scheduled report generation and non-urgent processing where appropriate.
- Avoid N+1 database queries.
- Use timeouts and retry limits for external integrations.
- Ensure one PHC cannot affect another PHC's data through incorrect query scoping.



The dashboard should remain usable during periods of increased activity.



Measure actual performance instead of inventing benchmark results.



---



21. TESTING REQUIREMENTS



Write and run tests using the project's existing testing framework.



Unit tests



Test:



- Patient count aggregation.
- Consultation completion calculations.
- Waiting and pending status calculations.
- Attendance approval rules.
- Bed occupancy calculations.
- Supply request approval rules.
- Report status transitions.
- Permission checks.



Integration tests



Test:



- Doctor completes consultation → In-charge dashboard updates.
- Nurse records arrival → Patient flow summary updates.
- Pharmacist records shortage → In-charge alert appears.
- In-charge approves supply request → District Supply Chain Officer receives it.
- In-charge submits report → DHO receives it.
- District officer responds → In-charge sees response.
- Staff attendance submission → In-charge can review it.



Security tests



Test:



- In-charge cannot access another PHC.
- In-charge cannot access unauthorized clinical records.
- In-charge cannot modify inventory directly.
- In-charge cannot approve unauthorized requests.
- Unauthorized users cannot call protected endpoints.
- Manipulated identifiers cannot bypass resource authorization.



Edge-case tests



Test:



- Network interruption during report submission.
- Duplicate submission.
- Concurrent approval attempts.
- Missing staff data.
- Stale bed status.
- Incomplete supply request.
- External AI service failure.
- Missing District officer configuration.
- Empty dashboard.
- Partial synchronization failure.



UI and end-to-end tests



Test:



- Responsive mobile layout.
- Tablet and desktop layout.
- Navigation between In-charge pages.
- Form validation.
- Loading and error states.
- Tamil and English display.
- Keyboard accessibility.
- Preservation of existing Patient, Doctor, and Nurse workflows.



Do not report tests as passed unless they have actually been executed.



---



22. MONITORING AND OPERATIONS



Integrate with existing monitoring and logging infrastructure.



Monitor:



- API failures and latency.
- Dashboard load performance.
- Database query performance.
- Failed report submissions.
- Synchronization errors.
- Notification delivery status.
- AI service errors and latency.
- Unauthorized access attempts.
- Background job failures.



Provide actionable technical error logs without exposing sensitive patient data.



Support incident investigation and recovery through authorized technical administration.



Do not introduce a separate AI Administrator application role.



---



23. IMPLEMENTATION PRIORITY



Implement in the following order.



Phase 1 — Functional MVP



- Inspect and preserve existing application.
- Implement Role 04 routing and authorization.
- Build PHC overview dashboard.
- Integrate patient footfall and consultation counts.
- Build staff and attendance review.
- Build bed and facility overview.
- Integrate Pharmacist stock summaries and supply requests.
- Build District report and escalation workflow.
- Add essential loading, error, empty, and responsive states.



Phase 2 — Enhanced Operations



- Advanced filtering and historical reporting.
- Duty roster management.
- Facility issue assignment and tracking.
- Supply request status history.
- District acknowledgments and clarification workflow.
- Notification integration.
- Improved offline and synchronization handling.



Phase 3 — In-charge Personal AI



- Authorized AI chat.
- Daily operations summaries.
- Workload and staffing insights.
- Supply shortage summaries.
- Report drafting.
- Tamil and English support.
- AI error handling and human confirmation.



Phase 4 — Production Hardening



- Full security and authorization tests.
- Audit review.
- Performance optimization.
- Monitoring and alerting.
- Backup and recovery validation.
- Accessibility and user acceptance testing.



Do not implement advanced features by breaking or delaying essential workflows.



---



24. FINAL ACCEPTANCE CRITERIA



The Role 04 implementation is complete only when:



1. An authenticated In-charge can access only their assigned PHC.
2. The dashboard displays real data from existing shared modules.
3. Doctor consultation completion is automatically reflected in the In-charge operational counts.
4. Nurse and Pharmacist updates are reflected without duplicate manual entry.
5. Patient footfall, waiting, consultation, and completion counts are calculated correctly.
6. Staff attendance can be reviewed and approved according to permissions.
7. Bed and facility status is visible with clear data freshness.
8. Medicine shortages and supply requests are integrated with the Pharmacist workflow.
9. Authorized supply requests reach the correct District Supply Chain Officer.
10. Facility reports reach the correct DHO.
11. Emergency-related operational escalations reach the correct District Emergency Coordinator.
12. District responses and request statuses can be tracked.
13. The In-charge Personal AI Assistant answers using authorized actual data.
14. AI never independently makes clinical or administrative approval decisions.
15. Existing Patient, Doctor, Nurse, and Pharmacist workflows remain functional.
16. Mobile, tablet, and desktop layouts work without overflow.
17. Tamil and English localization works.
18. Offline, loading, empty, error, and stale-data states are handled.
19. Backend authorization, audit logs, validation, and safe retries are implemented.
20. Relevant automated tests have been run and results reported accurately.



---



25. REQUIRED DEVELOPMENT APPROACH



Do not simply return a proposed architecture or a list of components.



Work directly within the existing codebase.



First inspect the project and identify the existing reusable components, modules, APIs, and data models.



Then implement the Role 04 module incrementally.



Before modifying shared components or schemas, verify that the changes will not break existing roles.



After implementation:



- List the files created and modified.
- Explain the important integrations.
- Identify any backend or environment configuration required.
- Report which tests were actually executed and their results.
- Clearly identify incomplete features and external integrations that still require setup.
- Do not claim production readiness for features that are still mocked or untested.



Final product objective:



A real PHC In-charge should be able to open the application, understand the complete operational status of their assigned PHC, monitor patients and staff, review medicine and facility issues, coordinate with the correct District officers, submit authorized reports, and use a dedicated Personal AI Assistant — without manually collecting the same information from Doctors, Nurses, and Pharmacists or duplicating their responsibilities.



Build this as a secure, integrated, mobile-first extension of the existing Smart Health and Supply Chain Resilience platform.




# 7. ROLE 05 — Pharmacist / PHC Storekeeper


**Role purpose (master summary):** PHC pharmacy/store role responsible for prescription dispensing, medicine inventory, batches, expiry, stock movement, replenishment, forecasting, and auditability.


### Detailed requirements from the uploaded role specification


# ROLE 05 – PHARMACIST / PHC STOREKEEPER



## Complete Functional Implementation Prompt



Act as a senior full-stack developer, healthcare product architect, database engineer, and AI/ML architect.



I am building a Smart Health & Supply Chain Resilience PWA for Primary Health Centres (PHCs).



Your task is to implement **Role 05 – Pharmacist / PHC Storekeeper** as a complete, functional, integrated module inside the existing project.



Do not build a static dashboard, dummy UI, or disconnected demo. Every major screen, button, form, table, alert, stock update, and workflow must work with the backend and database.



IMPORTANT:



* Work ONLY on Role 05.
* Do not redesign, remove, rename, or modify other existing roles.
* Reuse the existing authentication, role-based access control, database, APIs, design system, and project architecture wherever possible.
* Integrate with the existing Doctor, Patient, PHC In-charge, District Supply Chain Officer, and State Supply Chain workflows.
* First inspect the existing project structure, database schema, and APIs. Reuse existing entities and avoid duplicate tables or conflicting implementations.
* If an integration is not implemented yet, create a clearly defined interface and explain what is required to connect it.



# 1. ROLE OBJECTIVE



The Pharmacist is responsible for:



1. Receiving and dispensing doctor-approved prescriptions.
2. Maintaining accurate PHC medicine inventory.
3. Tracking medicine purchase/receipt history, batch numbers, quantities, and expiry dates.
4. Monitoring medicine consumption and stock movement.
5. Predicting future medicine requirements and possible stock-outs.
6. Identifying when and how much medicine to reorder.
7. Creating replenishment requests and tracking medicine deliveries.
8. Ensuring every stock change is recorded and auditable.



The pharmacist must be able to answer:



* How much stock is available now?
* When and how much medicine was last received?
* Which batch will expire first?
* How quickly is the medicine being consumed?
* How many days will the current stock last?
* How much medicine will be needed next week or next month?
* When should we request replenishment?
* Which medicines are at risk of stock-out?
* Which replenishment requests are pending or dispatched?



# 2. MAIN DASHBOARD



Create a responsive pharmacy dashboard with real database-backed information.



Display:



* Total medicines maintained by the PHC.
* Total available stock and stock by medicine.
* Low-stock and critical-stock medicines.
* Medicines expected to run out soon.
* Near-expiry and expired batches.
* Pending prescriptions.
* Pending replenishment requests.
* Incoming medicine deliveries.
* Recent stock movements.
* Forecasted medicine demand for the next 7, 30, and 90 days, where sufficient data is available.



Every dashboard card must open the corresponding detailed page.



Provide search, filters, sorting, pagination, loading states, empty states, error messages, and refresh functionality.



Do not display fabricated live stock figures.



# 3. MEDICINE INVENTORY MANAGEMENT



Create a functional inventory module.



Each medicine should support:



* Medicine ID and standardized medicine name.
* Generic name and category.
* Dosage form: tablet, capsule, syrup/suspension, injection, vaccine, topical medicine, IV fluid, or medical supply, where applicable.
* Strength and unit of measurement.
* Approved facility formulary status.
* Minimum stock threshold.
* Target or maximum stock level.
* Reorder lead time.
* Storage requirements, where applicable.
* Active/inactive status.



Maintain stock separately for each PHC and each batch.



For every inventory batch, record:



* Batch number.
* Medicine ID.
* PHC ID.
* Supplier or supplying warehouse.
* Date received.
* Expiry date.
* Received quantity.
* Available quantity.
* Reserved quantity, if supported.
* Unit of measurement.
* Receipt reference and transaction ID.



Implement:



* Add medicine from the authorized formulary.
* View medicine details.
* Search by medicine name, category, batch number, and expiry.
* Filter by low stock, critical stock, near expiry, expired, and available stock.
* View stock by batch and total PHC stock.
* Configure reorder thresholds based on authorized facility policy.



Use approved facility medicine lists and actual authorized inventory data.



Do not assume that every PHC stocks every medicine. Seed sample medicines only for clearly labelled demo/testing environments.



Examples of medicine categories include tablets, capsules, oral liquids, injections, vaccines, IV fluids, dressings, syringes, gloves, and antiseptics. Actual medicines, strengths, quantities, storage conditions, and approved formulations must be configurable from the facility's authorized formulary.



Do not invent a universal PHC medicine list or recommend clinical dosage.



# 4. PRESCRIPTION AND DISPENSING WORKFLOW



Integrate directly with Role 02 – Doctor / Medical Officer.



Workflow:



1. Doctor completes a consultation and submits an authorized prescription.
2. Prescription automatically appears in the same PHC's pharmacist queue.
3. Pharmacist sees the encounter reference, prescribed medicine, strength, dosage instructions, prescribed quantity, and prescription status according to permissions.
4. Pharmacist verifies the prescription and available medicine batches.
5. Pharmacist selects the correct batch and records the actual quantity dispensed.
6. The system deducts stock from the selected batch only after successful dispensing confirmation.
7. Prescription and dispensing statuses update automatically.
8. Patient collection status is updated through the existing patient workflow.



Implement the following statuses:



* Pending dispensing.
* Under verification.
* Partially dispensed.
* Dispensed.
* Unavailable.
* Cancelled.



Support:



* Partial dispensing.
* Medicine unavailable.
* Prescription clarification requests to the doctor.
* Prescription cancellation.
* Dispensing history.
* Prevention of duplicate dispensing.
* Correct handling of concurrent stock changes.



Do not allow the pharmacist to alter the doctor's clinical prescription without an authorized correction workflow.



Never deduct stock merely because a prescription was created.



Stock must be deducted only when the pharmacist confirms actual dispensing.



# 5. PURCHASE AND STOCK RECEIPT HISTORY



Create a dedicated purchase/receipt history page.



For each medicine, show:



* Date of purchase or receipt.
* Medicine name and quantity.
* Batch number and expiry date.
* Supplier or warehouse.
* Purchase/order/reference number, if available.
* Date requested, approved, dispatched, and received.
* Actual received quantity.
* Difference between requested, dispatched, and received quantities.
* Receipt status.



Distinguish between a purchase order, a replenishment request, a dispatch, and an actual receipt.



Do not mark medicine as received when it is only requested or dispatched.



Only add stock after the pharmacist verifies and confirms actual receipt.



Maintain a complete historical record of all receipts and stock movements.



# 6. STOCK MOVEMENT AND AUDIT HISTORY



Implement stock transactions for:



* Medicine received.
* Medicine dispensed.
* Medicine returned, where permitted.
* Damaged stock.
* Expired stock.
* Authorized stock adjustment.
* Stock transferred, where the project supports approved transfers.



Every transaction must include:



* Transaction ID.
* PHC ID.
* Medicine ID and batch ID.
* Transaction type.
* Quantity and unit.
* Previous and resulting stock.
* Timestamp.
* Performing user.
* Reason or reference.
* Approval reference where required.



Do not permit silent deletion or editing of completed transactions.



Use authorized reversal or correction transactions with reasons and audit records.



# 7. BATCH AND EXPIRY MANAGEMENT



Create a batch and expiry management page.



Features:



* Batch-wise stock display.
* Expiry date tracking.
* Configurable near-expiry warning period.
* Expired stock identification.
* Near-expiry alerts.
* Expiry-based stock reports.
* Quarantine or exclusion of expired stock from dispensing.
* Authorized removal and disposal recording.



Use FEFO (First Expiry, First Out) as the default batch-selection suggestion where applicable.



The pharmacist must be able to review and override batch suggestions only through an authorized, auditable workflow.



Never allow expired or quarantined stock to be dispensed.



# 8. MEDICINE CONSUMPTION AND DEMAND FORECASTING



This is a core requirement.



Build a functional demand planning module, not just a static chart.



Calculate medicine consumption using actual historical dispensing and valid stock transaction data.



Provide:



* Daily consumption.
* Weekly consumption.
* Monthly consumption.
* Average daily consumption.
* Consumption trends.
* Seasonal or historical demand patterns, where enough data exists.
* Forecasted demand for the next 7, 30, and 90 days.
* Expected stock-out date.
* Estimated days of stock remaining.
* Suggested replenishment date.
* Suggested replenishment quantity.



Use historical consumption, current usable stock, confirmed incoming supplies, lead time, approved minimum/maximum stock levels, and relevant available demand indicators.



Account for expired, damaged, quarantined, and reserved stock when calculating usable stock.



Clearly show:



* Actual historical values.
* Forecasted values.
* Assumptions.
* Confidence or uncertainty.
* Data period used.
* Missing or insufficient data warnings.



Do not treat unconfirmed incoming supplies as available stock.



Do not assume future patient counts or seasonal demand data exist. If unavailable, state that the estimate is based on historical consumption only.



If insufficient historical data exists, use a transparent configurable baseline or threshold-based estimate and label it as preliminary.



Never fabricate historical data or present a forecast as a guaranteed requirement.



# 9. REORDER PLANNING AND SHORTAGE PREDICTION



Create an intelligent reorder planning page.



For each medicine, display:



* Current usable stock.
* Average daily consumption.
* Estimated days remaining.
* Forecasted demand during replenishment lead time.
* Confirmed incoming quantity.
* Safety stock or approved buffer.
* Suggested reorder date.
* Suggested reorder quantity.
* Stock-out risk level and explanation.



Use configurable, explainable reorder calculations.



A possible baseline calculation is:



Reorder Point = Expected Demand During Lead Time + Approved Safety Stock.



Suggested Replenishment Quantity = Target Stock Level − Projected Usable Stock at the expected receipt date.



Apply facility-approved constraints and ensure quantities cannot become negative.



Allow the pharmacist to review, edit, and submit the suggested request within authorized limits.



The system must not automatically purchase medicines or commit funds.



When stock is low or expected to become insufficient, generate actionable alerts and allow the pharmacist to create a replenishment request directly.



# 10. REPLENISHMENT WORKFLOW AND CONNECTIONS



Implement direct system communication between the pharmacist and the following roles.



## Role 04 – PHC In-charge / Facility Manager



* Review and approve replenishment requests when approval is required by policy.
* View PHC stock and shortage summaries.
* Monitor pending requests and expiry risks.



The In-charge must not be a technical communication bottleneck. The pharmacist can create a request and the system can notify both the In-charge and the authorized District Supply Chain Officer according to configured approval rules.



## Role 07 – District Supply Chain Officer



* Receive replenishment requests directly from the pharmacist's PHC.
* View requested medicines, quantities, urgency, and shortage evidence.
* Check district warehouse availability.
* Allocate, approve, or reject requests according to permissions.
* Record dispatch information and expected delivery.
* Update request status.



## Role 10 – State Supply Chain / Warehouse Manager



* Support escalated requirements when district stock is insufficient.
* Receive authorized escalations through the district workflow.
* Record state-level allocation and dispatch information.



The pharmacist must be able to track:



* Draft.
* Submitted.
* Awaiting review.
* Approved.
* Partially approved.
* Rejected.
* Allocated.
* Dispatched.
* Partially received.
* Received.
* Closed.



The pharmacist confirms actual receipt, batch number, expiry, and quantity before inventory is increased.



Support notifications, request history, rejection reasons, partial fulfillment, and delivery discrepancy reporting.



Do not allow the pharmacist to modify district or state warehouse inventory directly.



# 11. PHARMACY AI ASSISTANT



Create one role-specific AI assistant for the pharmacist, integrated with the existing platform assistant architecture where available.



It should help with:



* Natural-language inventory search.
* Summarizing current stock.
* Identifying critical and low-stock medicines.
* Summarizing expiry risks.
* Explaining consumption trends.
* Estimating stock-out risk.
* Explaining demand forecasts.
* Drafting replenishment requests.
* Generating pharmacy stock reports.



Example queries:



* "Which medicines may run out within 7 days?"
* "Show batches expiring within the next 60 days."
* "How much of this medicine was dispensed last month?"
* "Which medicines need replenishment this week?"
* "Draft a replenishment request for medicines at risk."



AI must use only data authorized for the logged-in pharmacist's PHC.



AI must not:



* Diagnose patients.
* Prescribe medicines.
* Recommend clinical dosages.
* Change a doctor's prescription.
* Dispense medicines.
* Modify stock independently.
* Submit or approve purchases without authorized human action.
* Access another PHC's inventory without permission.



Show the data and reasoning behind forecasts where possible.



Every AI-generated action must be reviewed and confirmed by the pharmacist.



If AI is unavailable, all standard inventory, dispensing, and replenishment functions must continue to work.



# 12. DATABASE AND BACKEND



Inspect the existing schema before implementing.



Reuse or extend existing entities where possible.



Required logical entities include:



* Medicine.
* FacilityFormulary.
* InventoryBatch.
* StockTransaction.
* Prescription.
* DispensingRecord.
* ReplenishmentRequest.
* ReplenishmentRequestItem.
* ReceiptRecord.
* SupplierOrWarehouseReference.
* ForecastRecord, if needed.
* Notification.
* AuditLog.



Use appropriate primary keys, foreign keys, indexes, timestamps, and PHC-level data ownership.



Important indexes include PHC ID, medicine ID, batch ID, expiry date, transaction date, prescription status, and replenishment status.



Use database transactions for dispensing, receiving stock, and other multi-step inventory changes.



Use idempotency keys or equivalent safeguards to prevent duplicate dispensing, duplicate receipt, and duplicate stock deduction during retries.



Validate quantities, units, dates, batch references, expiry dates, and user permissions on the backend.



Do not trust frontend calculations for stock integrity.



# 13. SECURITY AND ACCESS CONTROL



Enforce role-based access control on the backend.



The pharmacist must only access inventory and prescriptions assigned to their authorized PHC.



Implement:



* Secure authentication.
* PHC-level data isolation.
* Server-side authorization.
* Input validation.
* Protection against injection and unauthorized API access.
* Secure session handling.
* Rate limiting where appropriate.
* Audit logs for sensitive operations.
* Minimal access to patient information.
* Secure handling of prescription and inventory data.



Do not expose patient clinical records unnecessarily to the pharmacist.



Use only the minimum patient and prescription information required for dispensing.



# 14. OFFLINE AND FAILURE HANDLING



Design for real PHC conditions, including unstable internet and low-end mobile devices.



Support:



* Responsive mobile-first PWA.
* Offline viewing of safely cached, non-sensitive or appropriately protected data.
* Clearly marked offline mode.
* Queued non-conflicting actions where safe.
* Retry and synchronization status.
* Duplicate operation protection.
* Conflict detection for simultaneous stock changes.
* Graceful handling of database or API failure.



Never confirm a dispensing or stock receipt as successfully committed until the backend confirms the transaction.



If the network fails during a stock operation, clearly show whether it is pending, failed, or confirmed.



Do not allow stale offline inventory to be treated as guaranteed current stock.



# 15. UX AND ACCESSIBILITY



Design a clean, professional, mobile-first pharmacy interface.



Use clear navigation and readable stock tables.



Provide:



* Search and filters.
* Medicine details.
* Confirmation dialogs for dispensing and stock adjustments.
* Clear success and error messages.
* Loading indicators.
* Empty states.
* Low-stock and expiry warnings.
* Tamil and English language support where supported by the existing application.
* Accessible labels, keyboard navigation, and sufficient contrast.



Use consistent design patterns from the existing project.



# 16. TESTING



Implement and test:



* Prescription-to-dispensing integration.
* Correct stock deduction.
* Partial dispensing.
* Duplicate request prevention.
* Concurrent dispensing of the same batch.
* Expired batch exclusion.
* Partial delivery and receipt.
* Replenishment approval and rejection.
* Stock forecasting calculations.
* Insufficient historical data.
* Offline and retry scenarios.
* PHC-level authorization.
* Invalid quantities and dates.
* Audit trail integrity.



Add unit, API, integration, and end-to-end tests wherever the existing project supports them.



# 17. IMPLEMENTATION REQUIREMENTS



Work in the following order:



Phase 1: Inspect the existing project, identify the framework, database, authentication, existing roles, APIs, and reusable components.



Phase 2: Explain briefly what will be reused and which database/API changes are required.



Phase 3: Implement the complete Role 05 frontend and backend integration.



Phase 4: Implement inventory transactions, dispensing, receipt, replenishment, demand forecasting, and AI assistant integration.



Phase 5: Add validation, permissions, audit logs, error handling, and tests.



Phase 6: Verify that all pages and workflows work end-to-end.



Do not stop after producing a plan or UI mockup. Implement the actual functionality in the available project.



Do not replace existing working functionality unnecessarily.



Do not use hardcoded values as if they were real operational data.



If sample data is necessary for a demo, clearly label it as DEMO DATA and keep it separate from production data.



At the end, provide a concise implementation summary:



1. Pages implemented.
2. Backend APIs implemented.
3. Database changes.
4. Integrations completed.
5. Forecasting logic and assumptions.
6. AI capabilities and limitations.
7. Tests performed and their results.
8. Remaining integration requirements or limitations.



FINAL EXPECTATION:



A real PHC pharmacist must be able to receive a doctor's prescription, dispense medicines, maintain batch-level inventory, view purchase and receipt history, track expiry, monitor consumption, forecast future medicine requirements, identify expected stock-outs, create replenishment requests, communicate directly with district supply chain, confirm actual deliveries, and maintain a complete audit trail.



Build a practical, secure, fully integrated pharmacy management module—not a static dashboard.
# 18. PROFESSIONAL UI/UX, RESPONSIVE DESIGN & MULTILINGUAL SUPPORT



This section is mandatory. Apply these requirements to the entire Role 05 – Pharmacist / PHC Storekeeper module.



## A. Responsive Design – All Devices



Build a mobile-first, responsive Progressive Web App (PWA) that works correctly on:



* Android smartphones and tablets.
* iPhones and iPads.
* Windows and macOS laptops and desktops.
* Different screen sizes, resolutions, and orientations.



Requirements:



* Use responsive layouts, flexible grids, and adaptive navigation.
* On mobile, use a compact navigation menu and touch-friendly buttons.
* On tablets, use layouts suitable for pharmacy counters and stock management.
* On desktops, provide efficient tables, dashboards, and multi-column layouts.
* Prevent horizontal overflow, overlapping elements, clipped text, and broken tables.
* Make all forms, charts, alerts, dialogs, filters, and stock tables usable on small screens.
* Support installation as a PWA where the browser and operating system permit.
* Handle network interruptions and provide clear offline/sync status.



Do not create separate disconnected mobile and desktop applications. Maintain one consistent, responsive application.



## B. Professional Healthcare UI/UX



Design a modern, clean, professional healthcare pharmacy interface.



The interface must be easy to understand for pharmacists with limited technical knowledge.



Requirements:



* Consistent design system, typography, spacing, colors, buttons, forms, and icons.
* Clear navigation and logical grouping of pharmacy functions.
* Prioritize important information: available stock, critical shortages, expiry alerts, prescriptions, and pending replenishment.
* Use readable tables, search, filters, sorting, and pagination.
* Use appropriate charts for consumption trends and demand forecasts.
* Provide loading, empty, success, warning, error, and offline states.
* Confirm important actions such as dispensing, receiving stock, and stock adjustments.
* Clearly explain what happened and what the pharmacist should do next.
* Use accessible contrast, keyboard navigation, screen-reader labels, and touch-friendly controls.



Do not use excessive animations, unnecessary decorative elements, or confusing dashboard cards.



## C. Tamil and English Language Support



Implement complete bilingual support throughout the Role 05 module.



Provide a language selector with:



1. English.
2. தமிழ் (Tamil).



Requirements:



* Translate all navigation labels, buttons, forms, field names, alerts, validation messages, notifications, and error messages.
* Translate dashboard cards, stock statuses, replenishment statuses, reports, and AI assistant responses.
* Use proper Tamil Unicode text and a font that renders Tamil characters correctly.
* Ensure Tamil text does not become broken, clipped, or displayed as boxes.
* Preserve medicine names, generic names, batch numbers, standardized medical terminology, and official medicine identifiers accurately.
* Do not translate medicine identifiers or change the meaning of clinical instructions.
* Allow the pharmacist to switch languages at any time without losing entered data or changing stock values.
* Remember the user's selected language across sessions.
* Keep the underlying database values, medicine IDs, and transaction records language-independent.



Do not implement language support only for the dashboard. Every screen and workflow must support the selected language.



## D. Tamil-English Mixed Input (Tanglish)



Support Tamil-English mixed-language queries in the pharmacy AI assistant wherever technically feasible.



Examples:



* "Indha week stock mudiyapora medicines enna?"
* "Intha medicine expiry eppo?"
* "Next 30 days ku evlo stock venum?"
* "Last month evlo tablets dispense pannom?"



The assistant should understand these queries and respond in the user's selected language.



Do not use unreliable automatic translation for medicine names, strengths, batch numbers, quantities, or clinical instructions.



## E. Voice Input and Text-to-Speech



Where supported by the device and browser, provide optional voice input for pharmacy searches and AI assistant queries.



* Support Tamil and English speech recognition where available.
* Allow the pharmacist to review and edit recognized text before submitting.
* Provide a graceful text-input fallback if speech recognition is unavailable.
* Never use voice recognition alone to confirm dispensing, receive stock, or authorize a transaction.
* Provide optional text-to-speech responses where supported and appropriate.



Clearly indicate when browser or device limitations prevent a voice feature from working.



## F. Technical Implementation



* Use the existing project framework and design system.
* Implement reusable responsive components.
* Use proper internationalization (i18n) rather than hardcoding translated text throughout the code.
* Keep translations in organized language resource files.
* Format dates, quantities, and numbers appropriately for the selected language and locale.
* Test Tamil text rendering, language switching, form validation, tables, charts, and AI responses.
* Test the complete application on mobile, tablet, and desktop screen sizes.



FINAL REQUIREMENT:



The pharmacist must be able to complete the entire workflow—from receiving prescriptions and dispensing medicines to inventory management, forecasting, replenishment, and reporting—on a smartphone, tablet, or computer, in either Tamil or English, without losing functionality or data.




# 8. ROLE 06 — District Health Officer (DHO)


**Role purpose (master summary):** District health administration and oversight role covering PHC operations, service delivery, staff availability, health indicators, alerts, reports, analytics, and district coordination.


### Detailed requirements from the uploaded role specification


## ROLE 06: DISTRICT HEALTH OFFICER (DHO)



Build a complete, functional District Health Officer module for the federated Smart Health & Supply Chain Resilience PWA.



IMPORTANT:



Before making changes, inspect the existing codebase, framework, database, APIs, design system, routing, shared dashboards, PHC modules, Patient module, Doctor module, and existing district/state data structures.



Reuse existing components, services, data models, APIs, authentication, authorization, localization, dashboards, and working functionality wherever possible.



Implement ONLY the District Health Officer role in this phase.



Do not implement or modify the responsibilities of the District Supply Chain Officer, District Emergency Coordinator, State Health Administrator, State Supply Chain/Warehouse Manager, State Public Health Analyst, National Health Authority, or Platform Administrator.



The DHO is a district-level health administration and oversight role.



The DHO can view and coordinate district health information across PHCs under their authorized district, but does not become a super-user with unrestricted access to clinical records, pharmacy operations, supply-chain operations, emergency operations, or platform administration.



---



# 1. ROLE AND PURPOSE



The District Health Officer (DHO) is responsible for overseeing public-health service delivery and healthcare operations across the PHCs within the DHO's assigned district.



The DHO's primary responsibilities are:



* Monitoring the operational status of PHCs under the district.
* Monitoring district-level healthcare service availability.
* Reviewing aggregated patient and service statistics.
* Monitoring staff availability and attendance at district level.
* Identifying PHCs experiencing unusual workload, service disruption, or operational problems.
* Reviewing district-level health indicators and trends.
* Monitoring district health alerts and escalations.
* Coordinating health-related actions between PHCs and appropriate district-level officers.
* Reviewing district reports and analytics.
* Supporting district-level health planning and decision-making.
* Receiving AI-generated district health and operational insights.
* Escalating issues to the appropriate district or state authority when they exceed the DHO's responsibility.



The DHO does NOT own or directly operate:



* Individual clinical consultations.
* Diagnosis or prescription.
* Nursing procedures.
* Pharmacy dispensing.
* Detailed medicine inventory management.
* Supply procurement or warehouse operations.
* Detailed supply-chain distribution.
* Detailed emergency-response operations.
* Advanced public-health analytical modelling owned by the Public Health Analyst.
* Platform administration.
* User-role management.



The federated platform must enforce these boundaries.



---



# 2. DHO DASHBOARD



Create a clean District Health Officer dashboard containing:



* Today's District Health Status.
* PHCs Under the District.
* PHC Operational Status.
* Staff Availability.
* Patient and Service Overview.
* District Health Indicators.
* Medicine/Resource Alert Summary.
* Emergency Alert Summary.
* Pending District Actions.
* District Reports.
* District Analytics.
* AI-generated District Insights.



The dashboard should provide a high-level view of the district without exposing unnecessary individual patient information.



Provide clear navigation to:



* DHO Home
* PHCs
* Health Overview
* Staff Monitoring
* Patient & Service Statistics
* Health Alerts
* Emergency Overview
* Reports
* Analytics
* AI Assistant



The dashboard must show only information belonging to the authenticated DHO's assigned district.



---



# 3. DISTRICT AND PHC ACCESS



The DHO must have access to all PHCs officially mapped to their district.



The system must allow the DHO to:



* View the list of PHCs under the district.
* View each PHC's operational status.
* View PHC service availability.
* View patient/service workload indicators.
* View staff availability summaries.
* View relevant resource alerts.
* View unresolved operational issues.
* View district-level performance indicators.
* Compare authorized PHC-level aggregated indicators.
* Identify PHCs requiring attention.



The DHO must NOT:



* Modify a PHC's internal configuration.
* Change another user's role.
* Modify Doctor schedules directly.
* Modify Nurse records directly.
* Modify Pharmacist inventory records.
* Modify patient clinical records.
* Modify prescriptions.
* Directly perform PHC-level clinical operations.



If an operational change is required, the DHO should create, assign, escalate, or coordinate an appropriate action through the responsible role.



---



# 4. FEDERATED DISTRICT HEALTH VIEW



The DHO module must follow the federated architecture of the platform.



The DHO should receive district-level information from connected PHC modules.



Example:



PHC data → District aggregation → DHO dashboard.



The DHO should be able to see:



* Number of active PHCs.
* PHC operational status.
* Patient/service volumes.
* Staff availability.
* Health-service indicators.
* District-level health alerts.
* Relevant resource/medicine shortage alerts.
* Emergency situation summaries.
* Pending escalations.
* District trends.



The DHO should NOT receive unrestricted raw data simply because it originates from a PHC.



Use minimum-necessary data access.



---



# 5. PATIENT AND HEALTHCARE DATA ACCESS



The DHO requires patient/service information for district-level health administration.



The DHO may access aggregated or appropriately anonymized information such as:



* Daily patient footfall.
* Number of consultations.
* Number of completed consultations.
* Number of referrals.
* Service utilisation.
* PHC-wise patient workload.
* Disease/service category statistics where authorized.
* District-level health trends.
* Age-group or demographic aggregates where appropriate and authorized.
* Other approved district health indicators.



The DHO must NOT have unrestricted access to individual patient medical records.



The DHO must NOT:



* Open arbitrary patient profiles.
* Read detailed consultation notes without specific authorization.
* View unrestricted prescriptions.
* Edit patient medical records.
* Create or modify diagnoses.
* Create prescriptions.
* Modify Doctor clinical decisions.
* Access patients outside the DHO's authorized district scope.



If a legitimate district-level workflow requires patient-level information, access must be explicitly authorized, logged, and limited to the minimum necessary information.



The normal DHO dashboard should operate using aggregated district-level information.



---



# 6. STAFF MONITORING



The DHO can monitor district-level healthcare workforce availability.



The DHO can view:



* Doctors available at each PHC.
* Nurses/healthcare staff availability.
* Attendance summaries.
* Absence indicators.
* PHC staffing levels.
* Staff shortages affecting service availability.
* Duty coverage indicators.
* Workforce workload indicators where available.



The DHO can identify:



* PHCs with insufficient staff.
* PHCs experiencing unusual staff absence.
* PHCs with service disruption caused by staffing issues.
* District-wide staffing patterns.



The DHO should NOT directly edit individual attendance records.



The DHO should NOT:



* Check in staff.
* Check out staff.
* Change Doctor schedules directly.
* Change Nurse schedules directly.
* Approve arbitrary attendance corrections unless a separate authorized workflow explicitly grants that permission.
* Modify another role's personnel records.



The DHO can escalate staffing issues to the appropriate authority.



---



# 7. MEDICINE AND RESOURCE VISIBILITY



The DHO needs visibility into medicine/resource situations because shortages can affect district healthcare delivery.



The DHO can view:



* PHC-level medicine shortage alerts.
* Critical resource availability indicators.
* PHCs reporting shortages.
* Resource-related service disruption.
* District-level shortage summaries.
* Repeated shortage patterns.
* Critical health-resource alerts.



However, medicine and supply-chain operations remain owned by the appropriate Supply Chain roles.



The DHO must NOT:



* Edit medicine stock quantities.
* Create stock transactions.
* Change medicine batches.
* Modify expiry dates.
* Record dispensing.
* Create procurement orders.
* Manage warehouse inventory.
* Directly distribute stock between PHCs.
* Modify supply-chain transaction records.



If a shortage is detected:



PHC → shortage reported → District Supply Chain Officer → supply-chain action.



The DHO may:



* View the shortage.
* Understand its health impact.
* Raise/escalate a district health concern.
* Coordinate with the responsible officer when necessary.



The DHO should not replace the District Supply Chain Officer.



---



# 8. HEALTH ALERTS



Implement a district-level Health Alerts section.



The DHO can receive alerts related to:



* Significant PHC service disruption.
* Unusual patient/service volume.
* Staffing shortages affecting services.
* Critical resource shortages affecting healthcare delivery.
* District-level health indicators requiring attention.
* Escalated PHC operational problems.
* Relevant emergency situations.



Each alert should contain:



* Alert ID/reference.
* PHC or affected area.
* Alert category.
* Severity assigned by the authorized workflow.
* Timestamp.
* Current status.
* Source.
* Assigned responsible role where applicable.
* Escalation status.



The DHO can:



* View alerts.
* Acknowledge alerts where appropriate.
* Review their status.
* Escalate district health issues.
* Coordinate with responsible district officers.
* Add authorized administrative comments.



The DHO must not independently redefine clinical emergency severity.



---



# 9. EMERGENCY OVERVIEW AND COORDINATION



The DHO needs district-level visibility during emergencies because emergencies affect health-service delivery.



The DHO can view:



* Active emergencies affecting PHCs.
* Affected PHCs/areas.
* Number of affected facilities.
* Health-service disruption.
* High-level patient/service impact.
* Resource availability indicators.
* Emergency response status.
* Escalation status.



The DHO may coordinate health-administration actions and escalate the situation.



However, detailed emergency operations belong to the District Emergency Coordinator.



The DHO must NOT independently:



* Determine emergency severity.
* Perform clinical triage.
* Assign individual emergency patients to Doctors.
* Deploy emergency resources directly unless explicitly authorized.
* Replace the Emergency Coordinator's operational workflow.



Emergency workflow:



Authorized emergency staff
→ Emergency Coordinator
→ DHO receives district health impact/status
→ DHO coordinates health administration/escalation where required
→ State/National authority when escalation threshold is reached.



---



# 10. DISTRICT HEALTH PERFORMANCE



Create a District Health Performance section.



The DHO can monitor:



* PHC service availability.
* Patient footfall.
* Consultation volume.
* Referral volume.
* Staff availability.
* PHC operational status.
* Health-service trends.
* District health indicators.
* PHC-level aggregated performance.



Allow comparison between PHCs using authorized aggregated indicators.



Examples:



* PHC A: high patient load.
* PHC B: staff shortage.
* PHC C: service disruption.
* PHC D: normal operation.



The system should highlight facilities requiring administrative attention.



Do not turn these indicators into an automatic punitive ranking system.



The dashboard should present factual operational indicators and allow the DHO to investigate the underlying situation.



---



# 11. PENDING DISTRICT ACTIONS



Create a Pending Actions section.



Potential pending actions include:



* PHC operational issues.
* Escalated staffing problems.
* Unresolved health-service disruptions.
* Resource-related health alerts.
* Emergency coordination follow-ups.
* Requests requiring DHO review.
* Reports requiring acknowledgement.
* District-level escalations.



Each action should contain:



* Action ID.
* Source PHC/role.
* Category.
* Description.
* Priority.
* Created date/time.
* Current status.
* Responsible person/role.
* Due date where applicable.
* Escalation status.



Possible statuses:



Pending
In Review
Assigned
In Progress
Escalated
Resolved
Closed



The DHO should not be able to close an action without the appropriate confirmation or evidence when the action belongs to another operational role.



---



# 12. REPORTS



Create a District Reports section.



The DHO can:



* View district health reports.
* Generate authorized reports.
* Filter reports by PHC.
* Filter by date range.
* Review district-level trends.
* Export approved district reports.



Possible reports:



* Daily District Health Summary.
* PHC Performance Summary.
* Patient Service Utilisation Report.
* Staff Availability Report.
* Health Alert Report.
* PHC Operational Status Report.
* Resource/Shortage Impact Summary.
* Emergency Health Impact Summary.



Reports should contain aggregated information unless the DHO has a specifically authorized reason to access limited patient-level information.



---



# 13. DISTRICT ANALYTICS



Create a District Analytics section.



Analytics may include:



* Patient volume trends.
* PHC workload trends.
* Consultation trends.
* Referral trends.
* Staff availability trends.
* Service utilisation.
* PHC operational trends.
* Health-alert trends.
* Resource shortage impact.
* District-level performance indicators.



Analytics should allow:



* Date filtering.
* PHC filtering.
* Category filtering.
* Trend visualisation.
* Summary metrics.
* Comparison of authorized PHCs.



The DHO should use analytics for health administration and planning.



Advanced epidemiological/public-health analysis should remain available to the authorized Public Health Analyst role rather than making the DHO an unrestricted analytics user.



---



# 14. PERSONALIZED DHO AI ASSISTANT



Create a DHO-specific AI assistant using authorized district-level operational and health data.



The AI assistant is intended for:



* District health monitoring.
* Daily district summaries.
* PHC situation awareness.
* Workload insights.
* Health-alert summarisation.
* Resource-impact awareness.
* Administrative reminders.
* District planning support.



## ALLOWED AI FUNCTIONS



### A. Daily District Summary



The AI can summarize:



* Number of active PHCs.
* Current PHC operational status.
* Patient/service volume.
* Staff availability.
* Active district health alerts.
* Pending DHO actions.
* Significant resource-related health alerts.



Example:



"Today, 4 PHCs are reporting higher-than-usual patient volume. Two PHCs have staff shortages affecting service availability. One critical medicine shortage has been escalated to the District Supply Chain Officer."



### B. PHC Situation Awareness



The AI can identify:



* Unusual workload.
* Repeated service disruptions.
* Staff availability concerns.
* Repeated health alerts.
* PHCs requiring administrative attention.



### C. District Health Trends



The AI can summarize historical trends using authorized data.



Example:



"Patient footfall at three PHCs has increased over the previous seven days."



The AI must clearly identify the data period used.



### D. Administrative Action Suggestions



The AI may suggest:



* Reviewing a PHC's operational issue.
* Contacting the responsible district officer.
* Escalating an unresolved issue.
* Reviewing staffing concerns.
* Reviewing repeated service disruption.



The DHO must make the final decision.



### E. Alert Summarisation



The AI can summarize multiple related alerts into a concise district situation report.



## AI RESTRICTIONS



The AI must NOT:



* Diagnose patients.
* Recommend medicines.
* Create prescriptions.
* Determine emergency severity independently.
* Perform clinical triage.
* Modify patient records.
* Modify attendance.
* Modify stock records.
* Create procurement orders.
* Directly assign emergency resources.
* Automatically change PHC operations.
* Automatically close alerts.
* Invent statistics.
* Invent patient information.
* Expose unauthorized patient information.



AI output must be advisory.



Consequential actions require authorized human confirmation.



If AI fails, the DHO must still have access to normal dashboards, reports, alerts, and district information.



---



# 15. DHO ROLE DO'S AND DON'TS



## DO:



* Monitor PHCs within the assigned district.
* Review aggregated health and service information.
* Monitor staff availability.
* Review district health alerts.
* Monitor PHC operational status.
* Review medicine/resource shortage impacts.
* Coordinate with responsible district officers.
* Review reports and analytics.
* Escalate issues appropriately.
* Use AI insights as decision support.
* Maintain confidentiality of patient information.



## DON'T:



* Access unrestricted individual patient records.
* Diagnose patients.
* Prescribe medicines.
* Modify prescriptions.
* Manage pharmacy dispensing.
* Edit medicine inventory.
* Manage warehouse operations.
* Create procurement orders.
* Perform detailed supply-chain transactions.
* Replace the District Supply Chain Officer.
* Replace the District Emergency Coordinator.
* Modify staff attendance directly.
* Manage platform users and permissions.
* Allow AI to make autonomous administrative or clinical decisions.



---



# 16. DATABASE AND BACKEND INTEGRATION



Reuse existing PHC, Patient, Doctor, Nurse, Pharmacy, Appointment, Attendance, Alert, and Supply Chain data models wherever possible.



The DHO module may require or extend the following entities:



## District



district_id
state_id
district_name
status
created_at
updated_at



## DHO



dho_id
user_id
district_id
role_metadata
status
created_at
updated_at



## PHC



phc_id
district_id
phc_name
location
operational_status
created_at
updated_at



## DistrictHealthSummary



summary_id
district_id
report_date
patient_count
consultation_count
referral_count
active_phc_count
staff_availability_summary
service_status
created_at
updated_at



## PHCHealthSnapshot



snapshot_id
phc_id
district_id
snapshot_date
patient_volume
service_status
staff_availability
health_indicators
resource_alert_summary
created_at
updated_at



## DistrictHealthAlert



alert_id
district_id
phc_id
alert_type
severity
source
description
status
created_at
updated_at



## DHOAction



action_id
district_id
source_phc_id
created_by
assigned_role
category
description
priority
status
due_at
created_at
updated_at



## DistrictReport



report_id
district_id
report_type
period_start
period_end
generated_by
report_reference
created_at



## DHOAIInteraction



interaction_id
dho_id
conversation_reference
authorized_context_reference
created_at
updated_at



Do not duplicate patient, appointment, prescription, inventory, or staff records unnecessarily.



The DHO dashboard should consume authorized aggregated data from existing modules.



---



# 17. SECURITY AND ACCESS CONTROL



The DHO can access only:



* Their assigned district.
* PHCs belonging to that district.
* Authorized district-level aggregated health information.
* Authorized district operational information.



Never trust a frontend-supplied:



* dho_id
* district_id
* phc_id
* patient_id



without backend authorization checks.



The backend must verify:



Authenticated user
→ DHO role
→ assigned district
→ requested PHC belongs to district
→ requested data is authorized for DHO access.



Patient-level health information must be protected.



The DHO must not be able to bypass role restrictions through modified API requests.



Apply:



* Secure authentication.
* RBAC.
* Object-level authorization.
* Input validation.
* API security.
* Rate limiting.
* Secure sessions.
* Encryption in transit and at rest.
* Audit logging.
* Secure error handling.
* Protection against injection.
* Protection against unauthorized data enumeration.



Sensitive DHO actions should be auditable.



Audit events should include:



* User.
* Action.
* Resource.
* Timestamp.
* Previous state where applicable.
* New state where applicable.
* Reason where required.



---



# 18. UI/UX AND ACCESSIBILITY



Reuse the existing design system from the Patient and Doctor modules.



Do not redesign or break existing modules.



The DHO UI must be:



* Professional.
* Mobile-first.
* Responsive.
* Dashboard-oriented.
* Easy to understand.
* Suitable for district-level operational monitoring.



Support:



* Mobile.
* Tablet.
* Desktop.



Use:



* District summary cards.
* PHC status cards.
* Alert panels.
* Charts.
* Tables.
* Filters.
* Search.
* Drill-down from district → PHC → aggregated indicators.



Do not expose patient-level information unnecessarily during drill-down.



Provide:



* Loading states.
* Empty states.
* Error states.
* Offline states.
* Stale-data indicators.
* Success confirmations.



Support:



* Tamil.
* English.



Accessibility must include:



* Readable text.
* Keyboard navigation.
* Screen-reader support.
* Visible focus.
* Accessible labels.
* Adequate contrast.
* Responsive layouts.
* No reliance on color alone.



---



# 19. FAILURE HANDLING



Handle:



* Network failure.
* Backend/API failure.
* Database failure.
* Stale PHC data.
* Missing PHC data.
* Delayed synchronization.
* Incorrect or incomplete data.
* Failed report generation.
* Failed AI service.
* Alert delivery failure.
* Unauthorized access attempts.



The system must:



* Clearly identify stale information.
* Never display false real-time status.
* Never claim an action succeeded without backend confirmation.
* Provide retry mechanisms.
* Preserve unsent administrative actions where safe.
* Clearly identify synchronization status.



If a PHC is offline, show:



"Last synchronized: [timestamp]"



rather than presenting old data as current.



---



# 20. TESTING AND ACCEPTANCE CRITERIA



Test:



### District Access



* DHO can access only their assigned district.
* DHO can view all authorized PHCs within that district.
* DHO cannot access another district's PHCs.



### Patient Data



* Aggregated patient statistics are visible.
* Individual patient records are restricted.
* Unauthorized patient API requests are blocked.



### PHC Monitoring



* DHO can view PHC operational status.
* DHO can view PHC-level aggregated indicators.
* DHO can identify PHCs requiring attention.



### Staff Monitoring



* DHO can view staff availability summaries.
* DHO cannot directly modify attendance records.



### Supply Chain Boundary



* DHO can view relevant shortage/resource-impact information.
* DHO cannot edit medicine inventory.
* DHO cannot create procurement or warehouse transactions.



### Emergency Boundary



* DHO can view relevant district emergency status.
* DHO can coordinate/escalate health-administration actions.
* DHO cannot independently perform emergency triage or replace the Emergency Coordinator.



### Reports



* District reports generate correctly.
* PHC filters work.
* Date filters work.
* Exported reports contain authorized information only.



### AI



* AI uses authorized district data.
* AI does not expose unauthorized patient information.
* AI does not diagnose.
* AI does not prescribe.
* AI does not independently modify operational records.
* AI clearly indicates when data is incomplete or stale.



### Security



* RBAC works at backend level.
* Object-level authorization prevents cross-district access.
* API manipulation cannot bypass DHO restrictions.
* Sensitive actions are audited.



### UI



* Works on mobile, tablet, and desktop.
* Tamil and English localization works.
* Existing Patient and Doctor modules remain functional and visually unchanged.



---



# 21. IMPLEMENTATION PRIORITY



## Phase 1 — Core DHO Module



Implement:



* DHO authentication/role access.
* District assignment.
* DHO dashboard.
* PHC list.
* PHC operational status.
* Staff availability overview.
* Patient/service aggregated statistics.
* District health overview.



## Phase 2 — Monitoring & Coordination



Implement:



* Health alerts.
* Pending actions.
* PHC performance.
* District reports.
* Emergency health overview.
* Resource/shortage visibility.
* Escalation and coordination workflows.



## Phase 3 — Analytics & AI



Implement:



* District analytics.
* Trend analysis.
* PHC comparison.
* District health summaries.
* Personalized DHO AI assistant.
* Operational insights.
* Administrative recommendations.



## Phase 4 — Production Readiness



Implement:



* Security hardening.
* Object-level authorization.
* Audit logging.
* Accessibility.
* Tamil/English validation.
* Failure handling.
* Offline/stale-data handling.
* Integration testing.
* Performance optimization.
* Production monitoring.



---



# 22. FINAL OBJECTIVE



Deliver a working District Health Officer module integrated with the federated Smart Health & Supply Chain Resilience platform.



The DHO must be able to:



* View all authorized PHCs within the district.
* Understand the district's current health-service situation.
* Monitor PHC operational status.
* Monitor staff availability.
* View aggregated patient and service statistics.
* Monitor district health indicators.
* Receive relevant health/resource alerts.
* View emergency health impact and coordinate appropriately.
* Review pending district actions.
* Generate district reports.
* Analyse district health trends.
* Receive AI-powered district health and operational insights.



The DHO must NOT become a super-admin or replace other specialized roles.



The system must preserve clear responsibility boundaries:



DHO → District Health Administration



District Supply Chain Officer → District Supply Chain Operations



District Emergency Coordinator → Emergency Operations



Doctor → Clinical Consultation and Prescription



Nurse/Healthcare Staff → Patient Care



PHC In-charge → PHC Facility Operations



Pharmacist/Storekeeper → Pharmacy and PHC Inventory



State Public Health Analyst → Advanced Public Health Analytics



State Supply Chain/Warehouse Manager → State Supply Chain



National Health Authority → National Health Oversight



National Platform Administrator → Platform Administration



The federated platform connects these roles and allows authorized information to flow between them while maintaining strict role-based access control.



Do not deliver a static dashboard or mock-only implementation.



Implement functional frontend, backend APIs, database integration, authorization, validation, error handling, auditability, and responsive UI.



Do not break existing Patient or Doctor functionality.



Do not implement other roles in this phase.




# 9. ROLE 07 — District Supply Chain Officer


**Role purpose (master summary):** District medicine and essential-supply chain role covering PHC stock, requests, replenishment, redistribution, district warehouse activity, alerts, and state escalation.


### Detailed requirements from the uploaded role specification


## ROLE 07: DISTRICT SUPPLY CHAIN OFFICER



Build a complete, functional District Supply Chain Officer module for the federated Smart Health & Supply Chain Resilience PWA.



IMPORTANT:



Before making changes, inspect the existing codebase, framework, database, APIs, design system, routing, PHC modules, Pharmacist module, Doctor module, District Health Officer module, District Emergency Coordinator module, and existing supply-chain data models.



Reuse existing components, APIs, services, authentication, authorization, database models, and design system wherever possible.



Implement ONLY the District Supply Chain Officer role in this phase.



The District Supply Chain Officer manages the **district-level medicine and essential healthcare supply chain**.



This role must not become responsible for clinical care, patient management, emergency clinical decisions, or platform administration.



---



# 1. ROLE AND PURPOSE



The District Supply Chain Officer is responsible for ensuring that medicines and essential healthcare supplies are available at the PHCs within the assigned district.



Main responsibilities:



* Monitor medicine availability across district PHCs.
* Monitor shortages and low-stock situations.
* Review PHC supply requests.
* Monitor medicine demand and consumption.
* Manage authorized replenishment and redistribution.
* Monitor district warehouse stock.
* Track incoming and outgoing supplies.
* Monitor batch and expiry information.
* Respond to supply-chain alerts.
* Coordinate emergency supply requests with the District Emergency Coordinator.
* Escalate district shortages to the State Supply Chain / Warehouse Manager when district stock is insufficient.
* Provide relevant district shortage and supply-impact information to the DHO.
* Generate supply-chain reports and analytics.
* Use AI supply insights for forecasting and early warnings.



The role does NOT manage:



* Patient clinical care.
* Doctor consultations or prescriptions.
* Nursing records.
* Individual patient medical records.
* Emergency clinical decisions.
* State warehouse inventory.
* Platform administration.



---



# 2. DISTRICT SUPPLY CHAIN DASHBOARD



Create a dashboard containing:



* District supply status.
* PHC stock status.
* Low-stock and stock-out alerts.
* Pending PHC supply requests.
* Emergency supply requests and priority.
* Medicine demand and consumption.
* District warehouse stock.
* Incoming/outgoing supply status.
* Near-expiry alerts.
* Pending supply actions.
* State-level supply escalations.
* Supply-chain reports and analytics.
* AI Supply Insights.



Navigation:



* Supply Dashboard
* PHC Stock
* Supply Requests
* Emergency Requests
* Replenishment
* Redistribution
* District Warehouse
* Supply Movement
* Alerts
* Escalations
* Reports
* AI Insights



Display only supply-chain information belonging to the authenticated Officer's assigned district.



---



# 3. PHC SUPPLY ACCESS



The Officer can access PHCs under the assigned district for supply-chain purposes.



Can view:



* PHC medicine stock.
* Medicine availability.
* Consumption.
* Demand.
* Supply requests.
* Shortage/low-stock status.
* Near-expiry stock.
* Supply history.
* Pending/received supply status.



The Officer must NOT access unrelated PHC information such as:



* Individual patient medical records.
* Consultation notes.
* Nursing records.
* Doctor clinical information.



Use minimum-necessary access.



---



# 4. MEDICINE STOCK MANAGEMENT



The Officer can monitor and manage authorized district-level medicine supply operations.



Functions:



* View PHC stock.
* Identify low-stock medicines.
* Identify stock-outs.
* Review stock levels.
* Monitor medicine consumption.
* Monitor batch information.
* Monitor expiry dates.
* Identify near-expiry stock.
* Review stock movement.
* Allocate authorized district stock to PHCs.



Inventory changes must be recorded through backend-controlled transactions and audit history.



Do not directly modify State Warehouse inventory.



---



# 5. SUPPLY REQUESTS



PHCs can submit medicine/resource requests.



The Officer can:



* View pending requests.
* Review requested medicine and quantity.
* Check available district stock.
* Approve/reject/process requests according to the configured workflow.
* Initiate replenishment.
* Track request status.
* Prioritize requests according to configured urgency rules.



Possible statuses:



Pending
Under Review
Approved
Rejected
Partially Fulfilled
Fulfilled
Escalated



Do not mark a request as fulfilled until the relevant supply transaction and PHC receipt are confirmed.



---



# 6. EMERGENCY SUPPLY REQUESTS



The District Emergency Coordinator can raise or forward emergency supply requirements to the DSCO.



Emergency requests must include:



* Emergency reference.
* Affected PHC/area.
* Required medicine/resource.
* Required quantity.
* Priority/urgency.
* Required-by time where available.
* Request status.



The DSCO can:



* Review emergency supply requirements.
* Prioritize emergency requests over normal requests according to configured rules.
* Check district stock.
* Allocate available district stock.
* Initiate emergency dispatch.
* Track emergency supply status.
* Escalate to the State Supply Chain / Warehouse Manager if district stock is insufficient.



Emergency supply priority must not be determined solely by AI.



The authorized emergency workflow and human decision-making remain responsible for urgency.



---



# 7. REPLENISHMENT AND REDISTRIBUTION



The Officer can coordinate medicine distribution across PHCs.



### Normal Replenishment



When PHC stock is low:



**PHC → Supply Request → DSCO Review → Stock Allocation → Dispatch → PHC Receipt Verification → PHC Stock Update**



### Inter-PHC Redistribution



When one PHC has excess stock and another has a shortage:



**PHC A Surplus → DSCO Review → Authorized Redistribution → Dispatch → PHC B Receipt Verification → PHC B Stock Update**



All movements must be recorded with:



* Medicine.
* Quantity.
* Source.
* Destination.
* Date/time.
* Responsible user.
* Status.



The system must prevent duplicate or conflicting stock transactions.



---



# 8. PHC RECEIPT CONFIRMATION



A supply must NOT be considered received simply because the DSCO marked it as dispatched.



When the shipment reaches the PHC, the **Pharmacist or authorized receiving staff** must verify:



* Actual quantity received.
* Medicine identity.
* Batch number.
* Expiry date.
* Condition of received stock where applicable.



Only after successful verification should the PHC inventory be updated.



Workflow:



**DSCO Dispatch → Shipment Arrives → Pharmacist/Authorized Receiver Verifies → Actual Quantity + Batch + Expiry Confirmed → PHC Stock Updated**



If the received quantity differs from the dispatched quantity:



Example:



**Dispatched: 100 → Received: 80**



The system must record the discrepancy and update PHC stock using the verified received quantity.



Do not silently update stock using the originally dispatched quantity.



Possible receipt statuses:



Dispatched
In Transit
Received Pending Verification
Partially Received
Verified
Discrepancy Reported
Rejected



The receipt confirmation must be auditable.



---



# 9. DISTRICT WAREHOUSE



The Officer can access the **district warehouse** supply information.



Can:



* View available district warehouse stock.
* Track incoming supplies.
* Track outgoing supplies.
* Monitor medicine batches.
* Monitor expiry.
* Allocate authorized district warehouse stock to PHCs.
* Track warehouse-to-PHC movement.



The DSCO must NOT directly modify State Warehouse inventory.



### State Warehouse Escalation



If required medicine/resource is unavailable at district level:



**PHC Requirement → DSCO → District Stock Check → Insufficient Stock → Escalate to State Supply Chain / Warehouse Manager**



The State Supply Chain / Warehouse Manager is responsible for state warehouse inventory and state-level allocation.



The DSCO can:



* Create escalation.
* Specify required medicine/resource and quantity.
* Specify affected PHC/emergency.
* Track escalation status.
* Receive state allocation/dispatch updates.



The DSCO cannot directly edit or deduct State Warehouse stock.



---



# 10. DHO CONNECTION — DISTRICT HEALTH IMPACT



The DSCO must have a controlled information connection with the **District Health Officer**.



The DSCO can send relevant aggregated supply-chain information to the DHO, including:



* Critical district shortages.
* PHCs affected by shortages.
* Major stock-out risks.
* Significant supply delays.
* Supply issues affecting healthcare service availability.
* District-level supply-chain impact.



The DHO can use this information for district health oversight.



The DHO does NOT take over supply-chain operations.



The DSCO remains responsible for:



* Supply requests.
* Allocation.
* Replenishment.
* Redistribution.
* Supply movement.
* State supply escalation.



The connection is:



**DSCO Supply Data → Aggregated Health Impact → DHO**



Do not expose unnecessary inventory transaction details or unrelated supply-chain information to the DHO.



---



# 11. SUPPLY-CHAIN ALERTS



Provide alerts for:



* Low stock.
* Stock-out.
* Rapid consumption.
* Unusual demand.
* Delayed supply.
* Near-expiry medicines.
* Critical PHC shortages.
* District warehouse shortages.
* Failed or delayed supply movement.
* Emergency supply requirements.
* State supply escalations.



The Officer can:



* View alerts.
* Acknowledge alerts.
* Investigate supply status.
* Initiate appropriate supply action.
* Escalate issues to the State Supply Chain / Warehouse Manager.
* Share relevant district health impact with the DHO.



---



# 12. AI SUPPLY INSIGHTS



Create a supply-chain-specific AI assistant/insight system.



AI can provide:



### Stock-out Prediction



Predict potential medicine shortages using historical consumption and current stock.



Example:



> "PHC A may run out of Medicine X within approximately 4 days based on recent consumption."



### Demand Forecast



Estimate future medicine demand using available historical and current data.



### Shortage Detection



Identify multiple PHCs showing unusually low stock or increasing consumption.



### Redistribution Suggestion



Identify potential redistribution opportunities.



Example:



> "PHC C has sufficient stock while PHC D is approaching a shortage. Consider reviewing redistribution."



### Expiry Warning



Identify medicines approaching expiry.



### Emergency Supply Insight



Summarize urgent supply requirements and identify whether district stock appears sufficient based on verified current data.



AI restrictions:



* Do not automatically change stock.
* Do not automatically approve supply requests.
* Do not automatically dispatch medicines.
* Do not create procurement orders autonomously.
* Do not directly modify State Warehouse stock.
* Do not determine emergency priority independently.
* Do not invent stock or consumption data.
* Clearly identify incomplete or stale data.
* AI recommendations require human confirmation.



If AI fails, normal supply-chain operations must continue.



---



# 13. REPORTS AND ANALYTICS



Provide:



* District stock report.
* PHC stock report.
* Stock-out report.
* Medicine consumption report.
* Supply request report.
* Emergency supply report.
* Replenishment report.
* Redistribution report.
* Expiry report.
* Supply movement report.
* State escalation report.



Analytics should support:



* Medicine demand trends.
* Consumption trends.
* Stock-out patterns.
* PHC supply requirements.
* Emergency supply requirements.
* Supply performance.



Allow appropriate date and PHC filters.



---



# 14. DO'S AND DON'TS



## DO



* Monitor district PHC stock.
* Process supply requests.
* Prioritize authorized emergency supply requests.
* Manage authorized replenishment.
* Coordinate redistribution.
* Track supply movement.
* Monitor batches and expiry.
* Verify state escalation status.
* Track PHC receipt confirmation.
* Respond to supply alerts.
* Provide relevant shortage impact to DHO.
* Review AI supply insights.



## DON'T



* Access individual patient medical records.
* Modify Doctor prescriptions.
* Perform clinical consultations.
* Manage nursing records.
* Make emergency clinical decisions.
* Modify State Warehouse inventory directly.
* Mark PHC stock received without receiver verification.
* Manage staff attendance.
* Manage platform users or permissions.
* Allow AI to autonomously make supply decisions.



---



# 15. DATABASE AND BACKEND



Reuse existing supply-chain, pharmacy, medicine, and warehouse data models.



Where necessary, support:



### DistrictSupplyOfficer



* officer_id
* user_id
* district_id
* status
* created_at
* updated_at



### SupplyRequest



* request_id
* phc_id
* medicine_id
* requested_quantity
* approved_quantity
* priority
* urgency
* status
* created_at
* updated_at



### StockTransaction



* transaction_id
* medicine_id
* source_location
* destination_location
* quantity
* transaction_type
* status
* created_by
* created_at



### SupplyReceipt



* receipt_id
* transaction_id
* phc_id
* medicine_id
* dispatched_quantity
* received_quantity
* batch_number
* expiry_date
* verification_status
* verified_by
* verified_at
* discrepancy_reason



### SupplyAlert



* alert_id
* district_id
* phc_id
* medicine_id
* alert_type
* priority
* status
* created_at



### SupplyEscalation



* escalation_id
* district_id
* medicine_id
* requested_quantity
* reason
* target_role
* status
* created_at
* updated_at



### DHOHealthImpact



* impact_id
* district_id
* affected_phc_id
* shortage_reference
* impact_summary
* severity
* created_at



### SupplyAIInteraction



* interaction_id
* officer_id
* context_reference
* created_at



Use foreign keys, indexes, transaction-safe stock updates, validation, and audit history.



Do not duplicate existing inventory or medicine records unnecessarily.



---



# 16. SECURITY AND ACCESS CONTROL



Implement backend-enforced RBAC.



The Officer can access only supply-chain information for the assigned district.



Backend must verify:



**Authenticated User
→ District Supply Chain Officer
→ Assigned District
→ Requested PHC belongs to District
→ Requested resource is supply-chain data**



Never trust frontend-supplied user, district, PHC, medicine, transaction, or stock identifiers without authorization checks.



Protect:



* Medicine inventory data.
* Supply transactions.
* Warehouse information.
* Supply requests.
* Receipt verification.
* State escalation information.



Record audit logs for:



* Stock changes.
* Supply approvals.
* Emergency prioritization.
* Replenishment.
* Redistribution.
* Dispatch.
* Receipt verification.
* Discrepancies.
* State escalations.
* Cancellations/corrections.
* Sensitive access.



---



# 17. UI/UX



Reuse the existing project design system.



The module must be:



* Mobile-first.
* Responsive.
* Simple and operational.
* Suitable for district-level supply-chain monitoring.



Use:



* Stock cards.
* PHC status cards.
* Supply request cards.
* Emergency priority indicators.
* Alerts.
* Tables.
* Filters.
* Search.
* Supply-status indicators.
* Receipt verification screens.
* Escalation status.
* Charts where useful.



Support:



Provide clear:



* Loading states.
* Empty states.
* Error states.
* Offline states.
* Stale-data indicators.
* Confirmation states.
* Pending verification states.
* Discrepancy states.



Do not rely only on colour to communicate supply severity.



---



# 18. FAILURE HANDLING



Handle:



* Network failure.
* API/database failure.
* Concurrent stock updates.
* Duplicate supply requests.
* Duplicate transactions.
* Stale inventory.
* Failed dispatch confirmation.
* Failed receipt confirmation.
* Quantity discrepancy.
* Invalid batch/expiry information.
* Warehouse synchronization failure.
* State escalation failure.
* AI failure.



Never show false success.



If data is stale, clearly show the last synchronization time.



Use safe retries and idempotency for critical supply transactions.



Never update PHC stock until receipt verification is confirmed.



---



# 19. TESTING AND ACCEPTANCE CRITERIA



Test that:



* Officer can access only the assigned district.
* Officer can view authorized PHCs.
* Stock data is accurate and synchronized.
* Normal supply requests can be processed.
* Emergency requests receive appropriate priority handling.
* Replenishment works correctly.
* Redistribution correctly updates source and destination workflows.
* State escalation occurs when district stock is insufficient.
* DSCO cannot directly modify State Warehouse stock.
* Dispatched stock does not automatically become PHC stock.
* Pharmacist/authorized receiver can verify actual quantity, batch, and expiry.
* PHC stock updates only after successful receipt verification.
* Quantity discrepancies are recorded correctly.
* Duplicate stock transactions are prevented.
* Batch and expiry information is available.
* Supply alerts work.
* DHO receives relevant aggregated shortage/health-impact information.
* AI predicts/identifies supply risks using available data.
* AI cannot autonomously modify inventory.
* Unauthorized patient/clinical data access is blocked.
* All supply transactions and receipt confirmations are auditable.
* Tamil and English work correctly.
* Module works on mobile, tablet, and desktop.



---



# 20. IMPLEMENTATION PRIORITY



### Phase 1 — Core



* DSCO authentication/RBAC.
* Supply dashboard.
* PHC stock visibility.
* Stock alerts.
* Supply requests.
* Basic supply reports.



### Phase 2 — Supply Operations



* Replenishment.
* Inter-PHC redistribution.
* District warehouse integration.
* Supply movement tracking.
* Batch/expiry monitoring.
* PHC receipt verification.



### Phase 3 — Coordination



* Emergency supply requests.
* Priority/urgency handling.
* DHO health-impact connection.
* State warehouse escalation.
* Escalation tracking.



### Phase 4 — Intelligence



* Stock-out prediction.
* Demand forecasting.
* Redistribution suggestions.
* Expiry warnings.
* Emergency supply insights.
* AI Supply Insights.



### Phase 5 — Production Readiness



* Security hardening.
* Audit logs.
* Concurrency protection.
* Failure handling.
* Accessibility.
* Performance optimization.
* Integration testing.



---



# FINAL OBJECTIVE



Deliver a functional District Supply Chain Officer module that ensures medicines and essential healthcare supplies move efficiently across PHCs within the assigned district.



The core workflow is:



**PHC Demand → Supply Request → DSCO Review → Priority Check → District Stock Check → Allocation → Dispatch → PHC Receipt Verification → Actual Quantity/Batch/Expiry Confirmation → PHC Stock Update**



If district stock is insufficient:



**DSCO → State Supply Chain/Warehouse Manager → State Allocation/Dispatch → District/PHC Receipt**



For emergencies:



**District Emergency Coordinator → Emergency Supply Request → DSCO Priority Handling → District Allocation or State Escalation → PHC Receipt Verification**



For district health impact:



**Supply Shortage → Aggregated Impact Information → DHO**



The DSCO owns the **district supply-chain workflow**, while other roles retain their own responsibilities:



* Doctor → Clinical care and prescriptions.
* Pharmacist → PHC pharmacy, dispensing, and receipt verification.
* PHC In-charge → PHC facility operations.
* DHO → District health administration and health-impact oversight.
* District Emergency Coordinator → Emergency coordination.
* State Supply Chain/Warehouse Manager → State-level supply chain and warehouse inventory.
* National Platform Administrator → Platform administration.



The federated platform must connect these workflows through controlled data exchange without giving the DSCO access to unrelated clinical, patient, emergency, or platform-administration functions.



Implement functional frontend, backend APIs, database integration, RBAC, validation, auditability, receipt verification, emergency priority handling, state escalation, DHO information exchange, error handling, and responsive UI.



Do not break existing Patient, Doctor, PHC, DHO, Pharmacist, or other functionality.



Do not implement other roles in this phase.




# 10. ROLE 08 — District Emergency Coordinator


**Role purpose (master summary):** District emergency-response coordination role covering alerts, affected PHCs, staff/resources, response tracking, escalation, reporting, and emergency AI support.


### Detailed requirements from the uploaded role specification


## ROLE 08: DISTRICT EMERGENCY COORDINATOR



Build a complete, functional District Emergency Coordinator module for the federated Smart Health & Supply Chain Resilience PWA.



IMPORTANT:



Before making changes, inspect the existing codebase, framework, database, APIs, design system, routing, PHC modules, Doctor/Nurse modules, District Health Officer module, District Supply Chain module, and existing emergency-related functionality.



Reuse existing components, APIs, services, authentication, authorization, database models, notifications, and design system wherever possible.



Implement ONLY the District Emergency Coordinator role in this phase.



The District Emergency Coordinator is responsible for **coordinating district-level healthcare emergency response**.



This role must not become responsible for normal clinical care, regular supply-chain management, general PHC administration, or platform administration.



---



# 1. ROLE AND PURPOSE



The District Emergency Coordinator is responsible for:



* Monitoring active district emergencies.
* Receiving and managing emergency alerts.
* Identifying affected PHCs/areas.
* Coordinating emergency response with relevant PHC and healthcare staff.
* Checking emergency-related staff availability.
* Coordinating emergency medicine/resource requirements with the District Supply Chain Officer.
* Tracking emergency response progress.
* Escalating major emergencies to the DHO and higher authorities when required.
* Maintaining emergency response records and reports.
* Using AI for emergency situation awareness and coordination support.



The role does NOT:



* Diagnose patients.
* Prescribe medicines.
* Perform clinical triage.
* Manage normal medicine inventory.
* Manage procurement or warehouse operations.
* Manage normal PHC operations.
* Manage staff attendance.
* Manage platform users or permissions.



---



# 2. EMERGENCY DASHBOARD



Create a focused Emergency Dashboard containing:



* Active Emergencies.
* Emergency Alerts.
* Affected PHCs / Areas.
* Emergency Response Status.
* Available Emergency Staff.
* Emergency Medicine/Resource Status.
* Pending Emergency Tasks.
* Escalations.
* Emergency Reports.
* AI Emergency Insights.



Navigation:



* Emergency Home
* Active Emergencies
* Alerts
* Affected PHCs
* Response Coordination
* Resources
* Escalations
* Reports
* AI Insights



Show only emergencies and emergency-related information within the Coordinator's authorized district.



---



# 3. EMERGENCY ALERTS



The system must allow authorized users to raise emergency alerts.



An emergency alert should contain:



* Emergency ID.
* Emergency type.
* Affected PHC/area.
* Time reported.
* Source.
* Current status.
* Priority/severity assigned through the authorized emergency workflow.
* Response status.



The Coordinator can:



* Receive alerts.
* View alerts.
* Acknowledge alerts.
* Review affected PHCs.
* Start/coordinate the response.
* Update response status.
* Escalate when required.



Do not allow the AI to independently determine emergency severity.



---



# 4. AFFECTED PHC ACCESS



The Coordinator can view PHCs affected by an active emergency.



Relevant information includes:



* PHC identity/location.
* Current emergency status.
* Service disruption.
* Available emergency staff.
* Emergency resource requirements.
* Response status.



The Coordinator should not receive unrestricted access to the PHC's normal operations or patient records.



Only the minimum information required for emergency coordination should be shown.



---



# 5. EMERGENCY RESPONSE COORDINATION



Core workflow:



**Emergency Detected → Alert → Emergency Coordinator → Assess Affected PHC → Coordinate Staff/Resources → Track Response → Escalate if Required → Resolve → Report**



The Coordinator can:



* Create/assign authorized emergency tasks.
* Coordinate with PHC In-charge.
* Check available Doctors/Nurses for emergency response.
* Coordinate emergency resource requirements.
* Track task completion.
* Update emergency response status.
* Escalate unresolved or major emergencies.



Possible response statuses:



Pending
Acknowledged
Response Started
In Progress
Escalated
Resolved
Closed



Do not mark an emergency resolved without authorized confirmation.



---



# 6. EMERGENCY STAFF COORDINATION



The Coordinator can view emergency-relevant availability of:



* Doctors.
* Nurses/healthcare staff.



This information is used only for emergency coordination.



The Coordinator must NOT:



* Modify staff attendance.
* Edit normal staff schedules.
* Change permanent staff assignments.
* Modify clinical records.



Staff allocation should follow authorized workflows and require appropriate human confirmation.



---



# 7. EMERGENCY RESOURCE COORDINATION



The Coordinator can view emergency-related availability of:



* Critical medicines.
* Essential medical supplies.
* Other configured emergency resources.



When additional supplies are required:



**Emergency Coordinator → District Supply Chain Officer → Supply action**



The Coordinator can submit or coordinate an emergency supply requirement.



The Coordinator must NOT:



* Edit regular medicine inventory.
* Create warehouse stock transactions.
* Manage procurement.
* Perform supply distribution directly.



The District Supply Chain Officer remains responsible for supply-chain operations.



---



# 8. ROLE CONNECTIONS



The Emergency Coordinator must have controlled connections with the following roles:



### PHC In-charge



Emergency information flow:



**PHC In-charge → Emergency Coordinator**



* Emergency reported.
* Affected PHC status.
* Required support.
* Response updates.



**Emergency Coordinator → PHC In-charge**



* Emergency tasks.
* Coordination requests.
* Response instructions within authorized scope.



### Doctor / Medical Officer



Information flow:



* Doctor availability.
* Emergency clinical support requirement.
* Response status.



The Coordinator does not modify clinical decisions.



### Nurse / Healthcare Staff



Information flow:



* Staff availability.
* Emergency care/support requirements.
* Response status.



The Coordinator does not manage normal nursing operations.



### District Supply Chain Officer



Information flow:



* Emergency medicine/resource requirement.
* Available supply.
* Supply request status.
* Delivery/fulfilment status.



The DSCO performs the actual supply-chain operation.



### District Health Officer



Information flow:



* Emergency status.
* Affected PHCs.
* District health impact.
* Escalation.
* Resolution status.



The DHO provides district-level health oversight.



### State Health Administrator



Only for major emergencies requiring state-level escalation.



### State Supply Chain / Warehouse Manager



Only when emergency supply requirements exceed district-level capacity.



### National Health Authority



Only for emergencies requiring national-level escalation.



Do not create unnecessary direct connections with unrelated roles.



---



# 9. ESCALATION



Create an emergency escalation workflow.



Escalate when:



* Emergency response exceeds district capacity.
* Required staff are unavailable.
* Required critical resources are unavailable.
* Multiple PHCs are significantly affected.
* Emergency remains unresolved.
* State-level intervention is required.



Example:



**PHC → Emergency Coordinator → DHO → State Authority**



For supply shortages:



**Emergency Coordinator → District Supply Chain Officer → State Supply Chain/Warehouse Manager**



Escalations must record:



* Reason.
* Source.
* Timestamp.
* Recipient role.
* Status.
* Response/update.



---



# 10. AI EMERGENCY INSIGHTS



Create an AI assistant focused only on emergency coordination.



AI may:



* Summarize active emergencies.
* Identify affected PHCs.
* Summarize response status.
* Highlight unresolved emergency tasks.
* Identify resource/staff gaps from available data.
* Summarize emergency trends.
* Suggest escalation based on configured operational rules.
* Prepare an emergency situation summary.



Example:



> "Three PHCs are affected by the current emergency. PHC A has limited medical staff availability and PHC B has reported a critical medicine requirement."



AI restrictions:



* No diagnosis.
* No clinical triage.
* No emergency severity decision without authorized rules/human confirmation.
* No prescription.
* No autonomous staff assignment.
* No autonomous resource movement.
* No inventory modification.
* No emergency closure.
* No fabricated information.



AI suggestions require human confirmation.



If AI fails, normal emergency coordination must continue.



---



# 11. EMERGENCY REPORTS



Provide:



* Emergency incident report.
* Affected PHC report.
* Response status report.
* Resource requirement report.
* Escalation report.
* Emergency resolution report.



Reports should include only authorized emergency information.



---



# 12. DO'S AND DON'TS



## DO



* Monitor active district emergencies.
* Manage emergency alerts.
* Track affected PHCs.
* Coordinate emergency staff availability.
* Coordinate emergency resource requirements.
* Track response progress.
* Escalate when required.
* Maintain emergency records.
* Use AI for emergency situation awareness.



## DON'T



* Diagnose patients.
* Prescribe medicines.
* Perform clinical triage.
* Access unnecessary patient medical records.
* Manage normal medicine inventory.
* Manage procurement or warehouses.
* Manage staff attendance.
* Manage normal PHC operations.
* Manage platform users/permissions.
* Allow AI to make autonomous emergency decisions.



---



# 13. DATABASE AND BACKEND



Reuse existing emergency, PHC, staff, supply, and user models wherever possible.



Where necessary, support:



### EmergencyIncident



* emergency_id
* district_id
* emergency_type
* affected_area
* reported_by
* priority
* status
* started_at
* resolved_at
* created_at
* updated_at



### EmergencyTask



* task_id
* emergency_id
* assigned_role
* assigned_user
* description
* status
* created_at
* updated_at



### EmergencyResourceRequest



* request_id
* emergency_id
* resource_type
* resource_id
* requested_quantity
* status
* created_at
* updated_at



### EmergencyEscalation



* escalation_id
* emergency_id
* from_role
* to_role
* reason
* status
* created_at
* updated_at



### EmergencyAIInteraction



* interaction_id
* coordinator_id
* emergency_id
* context_reference
* created_at



Use backend validation, foreign keys, indexes, authorization checks, transaction safety, and audit history.



Do not duplicate existing PHC, staff, medicine, or supply records unnecessarily.



---



# 14. SECURITY AND ACCESS CONTROL



Implement backend-enforced RBAC.



The Coordinator can access only:



* Emergencies within the assigned district.
* Emergency-related PHC information.
* Emergency-related staff availability.
* Emergency-related resource information.



Never trust frontend-supplied:



* coordinator_id
* district_id
* emergency_id
* phc_id



without backend authorization.



Protect sensitive emergency and health information.



Record audit logs for:



* Emergency creation.
* Alert acknowledgement.
* Task assignment.
* Escalation.
* Emergency status changes.
* Emergency closure.



---



# 15. UI/UX



Reuse the existing project design system.



The Emergency Coordinator UI must be:



* Mobile-first.
* Responsive.
* Fast to understand.
* Suitable for urgent situations.



Prioritize:



* Active emergencies.
* Alerts.
* Affected PHCs.
* Response status.
* Pending tasks.
* Escalation actions.



Use clear status indicators and do not rely on colour alone.



Support:



Provide:



* Loading.
* Empty.
* Error.
* Offline.
* Stale-data.
* Confirmation states.



---



# 16. FAILURE HANDLING



Handle:



* Network failure.
* Backend/API failure.
* Notification failure.
* Duplicate emergency reports.
* Duplicate tasks.
* Stale PHC status.
* Failed escalation.
* Failed supply request.
* AI failure.



Never display false success.



Show the last synchronization time when emergency information is stale.



If notification delivery is not confirmed, do not show the alert as successfully delivered.



---



# 17. TESTING AND ACCEPTANCE CRITERIA



Test that:



* Coordinator can access only assigned district emergencies.
* Emergency alerts work correctly.
* Affected PHCs are identified correctly.
* Emergency response status updates correctly.
* Emergency tasks can be coordinated.
* Staff availability is visible for emergency purposes.
* Emergency supply requests reach the correct Supply Chain Officer.
* DHO receives appropriate emergency status/escalations.
* State escalation works when authorized.
* AI provides emergency insights without making autonomous clinical decisions.
* Unauthorized patient/clinical access is blocked.
* Emergency actions are auditable.
* Tamil and English work correctly.
* UI works on mobile, tablet, and desktop.



---



# 18. IMPLEMENTATION PRIORITY



### Phase 1 — Core Emergency Management



* Emergency dashboard.
* Emergency alerts.
* Affected PHCs.
* Response status.
* Emergency tasks.



### Phase 2 — Coordination



* Staff availability.
* Emergency resource requests.
* DSCO integration.
* DHO integration.
* Escalation workflow.



### Phase 3 — Intelligence



* AI emergency summaries.
* Resource/staff gap insights.
* Emergency trend insights.
* Escalation suggestions.



### Phase 4 — Production Readiness



* Security hardening.
* Audit logging.
* Failure handling.
* Accessibility.
* Integration testing.
* Performance optimization.



---



# FINAL OBJECTIVE



Deliver a functional District Emergency Coordinator module that coordinates healthcare emergency response across PHCs within the assigned district.



Core workflow:



**Emergency Detected → Alert → Coordinator → Affected PHC Assessment → Staff/Resource Coordination → Response Tracking → Escalation → Resolution → Report**



The role boundaries must remain clear:



* **Emergency Coordinator → Emergency coordination**
* **DHO → District health administration**
* **PHC In-charge → PHC operations**
* **Doctor → Clinical care**
* **Nurse → Patient care**
* **District Supply Chain Officer → Medicine/supply operations**
* **State authorities → State-level escalation**
* **Platform Administrator → Platform administration**



The Emergency Coordinator should receive only the information necessary to coordinate emergencies and must not become a general-purpose administrator or clinical user.



Do not deliver a static mockup or hardcoded dashboard. Implement functional frontend, backend APIs, database integration, RBAC, validation, auditability, notifications, error handling, and responsive UI.



Do not break existing Patient, Doctor, PHC, DHO, or Supply Chain functionality.



Do not implement other roles in this phase.




# 11. ROLE 09 — State Health Administrator


**Role purpose (master summary):** State health administration role covering district-level oversight, alerts, schemes/targets, reports, analytics, administrative coordination, and state AI support.


### Detailed requirements from the uploaded role specification


# ROLE 09: STATE HEALTH ADMINISTRATOR



## Smart Health & Supply Chain Resilience – Complete Development Prompt



You are a senior full-stack developer, product architect, UI/UX designer, AI/ML engineer, and security engineer.



Build a complete, functional, responsive State Health Administrator module for the existing Smart Health & Supply Chain Resilience PWA.



IMPORTANT: Focus ONLY on Role 09 – State Health Administrator. Do not redesign, replace, or modify other role modules. Integrate this role into the existing project architecture, authentication, database, navigation conventions, and design system.



Do not create a static demo or a dashboard with non-functional buttons. Every page, navbar item, action, filter, form, AI feature, and workflow must work correctly.



---



# 1. ROLE PURPOSE



The State Health Administrator is responsible for state-level health administration, monitoring, coordination, and oversight across all districts within the assigned state.



The administrator must be able to:



* Monitor district-wise aggregated health and operational status.
* Identify health issues and emerging trends across districts.
* Monitor health alerts, district reports, and unresolved escalations.
* Coordinate with District Health Officers, District Supply Chain Officers, Emergency Coordinators, State Supply Chain Managers, and State Public Health Analysts.
* Monitor state health schemes, targets, and administrative activities.
* Use a dedicated State AI Assistant for health summaries, trend analysis, predictions, and decision support.
* Prepare and review state-level reports and authorized escalations.



The State Health Administrator must see only the state and districts assigned to their account.



This is a state-level administrative role, not a technical platform administrator.



# 2. ROLE ACCESS AND HIERARCHY



Implement the following logical project hierarchy:



National Health Authority (Role 12)
↕
State Health Administrator (Role 09)
↕
District Health Officer (Role 06)
District Supply Chain Officer (Role 07)
District Emergency Coordinator (Role 08)
State Supply Chain / Warehouse Manager (Role 10)
State Public Health Analyst (Role 11)
↕
PHC-level authorized operational data



The State Health Administrator must receive authorized aggregated information from district and state-level roles.



Data must be filtered by the administrator's assigned state and authorized permissions.



Do not allow the State Health Administrator to access:



* Individual patient medical records or identifiable patient information.
* Individual prescriptions or patient-level clinical histories.
* Direct pharmacy dispensing transactions or individual patient medicine records.
* Unrestricted district or state warehouse operational controls.
* Other states' confidential information.
* Platform-wide user management, technical configuration, or Super Admin functions.
* Unapproved direct modifications to district records.



The State Health Administrator can view, review, coordinate, approve, or escalate only those actions explicitly permitted by the configured role permissions.



Do not invent unrestricted approval powers.



# 3. AUTHENTICATION AND ONBOARDING



Implement:



* Secure login using the existing authentication system.
* Role-based routing for Role 09.
* State assignment during authorized account creation or administrator verification.
* Profile page with name, designation, assigned state, contact information, and account settings.
* Secure logout and session expiration handling.
* Unauthorized access and session-expired screens.
* Password reset using the existing authentication workflow.



Do not allow users to select another role or state to bypass authorization.



After login, redirect the user to the State Health Administrator Dashboard.



# 4. NAVBAR AND PAGE STRUCTURE



Create a professional, responsive navigation system with the following pages:



1. State Dashboard
2. District-wise Health Status
3. District Reports
4. Health Alerts & Escalations
5. Administrative Approvals
6. Scheme & Target Monitoring
7. State Reports & Analytics
8. State AI Assistant
9. Notifications
10. Profile & Settings



Every navbar item must navigate to its correct page.



Requirements:



* Highlight the active navigation item.
* Maintain consistent navigation across all pages.
* Use a collapsible sidebar on desktop and a working mobile drawer or compact navigation on mobile.
* Ensure all menu items remain accessible on small screens.
* Add breadcrumbs where useful.
* Add loading, empty, error, and success states to every relevant page.
* Ensure browser refresh and direct page navigation work correctly.
* Preserve navigation state when appropriate.
* Use the existing project routing conventions.



Do not create dead navigation links, placeholder pages, or buttons that do nothing.



# 5. STATE DASHBOARD



Build the main dashboard as a state-level health overview.



Include:



A. Overview Cards



* Total authorized districts.
* Reporting district status.
* Health alerts requiring review.
* Pending administrative actions.
* Districts with reported health concerns.
* Districts requiring follow-up.



Use actual authorized database values. Do not hardcode fake statistics.



B. District-wise Overview



Display a searchable, filterable district table with:



* District name.
* Reporting status.
* Aggregated health status.
* Active health alerts.
* Pending escalations.
* Last report update.
* View Details action.



Allow the administrator to open a district summary without exposing unauthorized patient-level information.



C. Health Trend Visualization



Display charts for:



* Aggregated patient visit trends.
* Health indicator trends.
* District-wise health alerts.
* Reporting completeness.
* District comparison over selected periods.



Use actual validated data and clear date ranges.



D. Recent Activities



Show recent authorized events such as:



* District reports received.
* Escalations submitted.
* Alerts updated.
* Administrative actions completed.
* State-level coordination updates.



Each activity must show its source, timestamp, and status where available.



# 6. DISTRICT-WISE HEALTH STATUS



Create a dedicated district monitoring page.



Features:



* Search districts by name.
* Filter by reporting status, health alerts, and date range.
* Sort district data.
* View authorized district summaries.
* Compare aggregated district health indicators.
* Display reporting gaps and unresolved issues.
* Open district-level reports and related escalations.



When a district is selected, show:



* District overview.
* Aggregated health indicators.
* PHC reporting status.
* Health alerts.
* District-level administrative issues.
* Supply-related health impact summaries.
* Emergency coordination status.
* Relevant pending actions.



Do not expose individual patient records.



# 7. DISTRICT REPORTS



Implement a functional report management module.



The State Health Administrator must be able to:



* View reports submitted by authorized district authorities.
* Filter reports by district, category, status, and date.
* Open report details.
* Review submitted information.
* Add authorized review comments.
* Request clarification or corrections through the appropriate workflow.
* Track report status.
* Generate consolidated state reports.
* Export authorized reports in PDF or CSV format where supported.



Report categories may include:



* District health status.
* PHC operational status.
* Health indicators and trends.
* Medicine availability and supply gaps.
* Emergency and incident summaries.
* Administrative performance and scheme progress.



Report status examples:



Draft → Submitted → Under Review → Clarification Requested → Reviewed → Closed



Implement only the transitions appropriate to the actual permissions and workflow.



Do not silently modify submitted district data.



# 8. HEALTH ALERTS & ESCALATIONS



Create a dedicated alert and escalation management page.



Display:



* Alert ID.
* Source district.
* Alert category.
* Severity.
* Reported date and time.
* Current status.
* Assigned authority.
* Required follow-up.



Provide filters for district, severity, category, and status.



The administrator must be able to:



* Open alert details.
* Review the supporting information.
* Add authorized comments.
* Assign or forward issues to the appropriate authorized authority.
* Escalate unresolved state-level issues to Role 12 when permitted.
* Track resolution status.
* View the history of actions taken.



Example alert categories:



* Rising health service demand.
* Potential disease trend.
* Essential medicine shortage affecting PHCs.
* Emergency resource requirement.
* District reporting or operational issue.



Do not allow the AI to automatically declare a disease outbreak or issue official public health alerts.



All consequential decisions require authorized human review.



# 9. ADMINISTRATIVE APPROVALS



Create an approval and review page for workflows specifically assigned to the State Health Administrator.



Include:



* Pending approvals.
* Requests requiring clarification.
* Approved requests.
* Rejected requests.
* Approval history.
* Request details and supporting documents.



For each request, show:



* Requesting authority.
* District or department.
* Request type.
* Submission date.
* Reason and supporting evidence.
* Current status.



Provide Approve, Reject, Request Clarification, and View Details actions only when permitted.



Require confirmation before consequential actions.



Record the decision, authorized user, timestamp, and reason in the audit log.



Do not implement arbitrary approvals for medicine dispatch, warehouse transactions, or clinical decisions unless an explicitly authorized workflow exists.



# 10. SCHEME & TARGET MONITORING



Build a state-level scheme and target monitoring module.



Features:



* View configured state health schemes and targets.
* Monitor district-wise progress.
* Compare reported progress with configured targets.
* Identify missing reports and delayed activities.
* View progress charts and reporting periods.
* Add authorized administrative remarks.
* Generate scheme progress summaries.



Do not invent government scheme names, official targets, or actual performance data.



Allow authorized configuration of project-specific schemes and targets.



# 11. STATE REPORTS & ANALYTICS



Implement state-level analytics and report generation.



Include:



* State health overview reports.
* District comparison reports.
* Health indicator trends.
* Medicine shortage impact summaries.
* Emergency and escalation reports.
* Scheme and target progress reports.
* Reporting completeness and data quality reports.



Provide:



* Date-range filters.
* District filters.
* Category filters.
* Download and export options.
* Printable report layout.
* Report generation status.



Every report must identify its reporting period, source, and last update.



Clearly distinguish actual reported values, estimated values, and AI-generated forecasts.



Do not present forecasts as confirmed outcomes.



# 12. DEDICATED STATE AI ASSISTANT



Build a State Health Administrator-specific AI Assistant.



The AI must serve ONLY Role 09 and must use only the data and actions authorized for the logged-in administrator.



Do not reuse an unrestricted general AI assistant that can access all roles' data.



The AI must have state-scoped data access enforced by the backend.



## A. State Health Summary



Allow queries such as:



* Summarize the health status of my state.
* Which districts have unresolved health alerts?
* Show districts with incomplete reports.
* Summarize the latest district health reports.
* What administrative issues require follow-up?



Generate concise, evidence-based answers with relevant source districts, reporting periods, and timestamps.



## B. Health Trend Analysis and Prediction



Analyze validated historical and current aggregated health data.



Potential predictions:



* District-wise changes in health service demand.
* Possible increases in selected health indicators.
* Emerging trends that may require further investigation.
* Districts requiring additional monitoring.



Use suitable validated forecasting or anomaly detection models when sufficient data is available.



Every prediction must include:



* Predicted indicator.
* Relevant district and forecast period.
* Data period used.
* Confidence or uncertainty information when statistically supported.
* Important factors or trends supporting the prediction.
* Recommended human review or follow-up.



If historical data is insufficient, clearly state that a reliable prediction cannot be generated.



Never fabricate forecasts, confidence percentages, or outbreak probabilities.



## C. Medicine Shortage and Supply Impact Insights



Use authorized aggregated supply chain data from Role 07 and Role 10.



The AI may:



* Identify districts with reported medicine shortages.
* Summarize medicine availability risks.
* Compare district requests with authorized warehouse availability.
* Identify potential future supply gaps using validated consumption and demand data.
* Suggest reviewing replenishment, redistribution, or escalation options.



Do not directly change inventory, create dispatch orders, approve procurement, or modify warehouse records.



## D. District Risk and Anomaly Detection



Detect patterns such as:



* Unusual changes in reported health indicators.
* Multiple districts reporting related health concerns.
* Incomplete or inconsistent reporting.
* Unusual discrepancies in aggregated supply or service data.



Flag anomalies for authorized review.



Do not automatically label a district as fraudulent, unsafe, or responsible for a health incident.



## E. Administrative Decision Support



The AI can suggest:



* Which unresolved reports require review.
* Which district issues need coordination.
* Which alerts may require escalation.
* Which reports are needed for state-level review.
* Possible administrative follow-up actions.



Show the reason behind each recommendation and allow the administrator to accept, dismiss, or request more information.



AI recommendations must never execute consequential actions automatically.



## F. State AI Assistant UI



Build a dedicated conversational interface with:



* Chat input.
* Suggested prompts.
* Conversation history.
* Clear loading and error states.
* Source references for generated insights.
* Copy and export options where supported.
* Tamil and English support.
* Tanglish input support where feasible.
* Optional voice input with a graceful fallback if speech services are unavailable.



The AI must not reveal other states' data, patient identities, private records, or unauthorized role information.



If the AI service fails, display a clear error and allow the user to retry or continue using the normal dashboard.



# 13. NOTIFICATIONS



Create a working notification center.



Show relevant notifications for:



* New district reports.
* Health alerts.
* Pending administrative approvals.
* Escalation updates.
* Report clarification requests.
* AI forecast warnings requiring review.



Implement:



* Read and unread states.
* Mark as read.
* Open related page.
* Timestamp.
* Relevant notification category.



Notifications must be restricted to the assigned state and authorized role.



Use the existing notification infrastructure where available.



# 14. PROFILE & SETTINGS



Implement:



* View profile.
* Update permitted profile fields.
* View assigned state and role.
* Language preference.
* Notification preferences.
* Password or account security settings through the existing authentication system.
* Secure logout.



Do not allow changing role or state assignment through ordinary profile editing.



# 15. DATABASE AND BACKEND



Use the existing project's database and backend architecture.



Do not create an unnecessary second backend or duplicate existing entities.



Reuse existing tables, APIs, authentication, and services wherever possible.



Implement or extend the following logical entities as required:



1. State Administrators
2. State and District Assignments
3. District Health Reports
4. Aggregated Health Indicators
5. Health Alerts
6. Administrative Escalations
7. Approval Requests
8. Health Schemes and Targets
9. State Report Records
10. Notifications
11. AI Insights and Forecast Records
12. Audit Logs



Each record must have appropriate identifiers, timestamps, ownership, status, and jurisdiction fields.



Implement:



* Server-side state and role authorization.
* Input validation.
* Database constraints.
* Appropriate indexes.
* Pagination for large lists.
* Safe handling of duplicate requests.
* Consistent error responses.



Never rely only on frontend filtering to protect sensitive data.



# 16. API REQUIREMENTS



Implement real backend APIs using the existing project's conventions.



Suggested endpoints:



GET /api/state/dashboard



GET /api/state/districts



GET /api/state/districts/:districtId/summary



GET /api/state/reports



GET /api/state/reports/:reportId



POST /api/state/reports/:reportId/review



GET /api/state/alerts



GET /api/state/alerts/:alertId



POST /api/state/alerts/:alertId/actions



GET /api/state/approvals



POST /api/state/approvals/:requestId/decision



GET /api/state/schemes



GET /api/state/analytics



POST /api/state/exports



POST /api/state/ai/chat



GET /api/state/ai/insights



GET /api/state/notifications



PATCH /api/state/notifications/:notificationId/read



These are logical endpoint suggestions. Adapt them to the existing backend and avoid duplicating existing endpoints.



Every endpoint must enforce authentication, role permissions, state assignment, input validation, and appropriate error handling.



# 17. DO'S



You MUST:



1. Inspect the existing codebase before making changes.
2. Reuse the existing design system, components, routing, database, and authentication.
3. Build Role 09 as a separate, properly authorized module.
4. Make every navbar item and page functional.
5. Implement actual data loading, filtering, searching, sorting, and pagination.
6. Connect all forms and actions to real backend workflows.
7. Display clear loading, success, empty, and error states.
8. Validate user input on both frontend and backend.
9. Use real authorized data wherever available.
10. Label sample or mock data clearly in development and demo environments.
11. Make AI outputs traceable to authorized sources and reporting periods.
12. Use AI only for state-level health administration, analytics, and decision support.
13. Require human review for consequential decisions.
14. Maintain audit logs for approvals, escalations, and administrative actions.
15. Implement responsive design for mobile, tablet, laptop, and desktop.
16. Support Tamil and English throughout the interface.
17. Ensure accessible typography, contrast, keyboard navigation, and touch targets.
18. Test the complete user workflow before declaring the module complete.
19. Preserve all existing role modules and their permissions.
20. Use graceful fallbacks when AI, APIs, or external services are unavailable.



# 18. DON'TS



You MUST NOT:



1. Modify or break the existing modules for Roles 01–08 or Roles 10–13.
2. Give Role 09 access to individual patient records or clinical histories.
3. Allow the State Administrator to access another state's restricted information.
4. Give this role Super Admin or unrestricted database access.
5. Build static dashboard cards with hardcoded production statistics.
6. Create non-functional buttons, fake navigation, or placeholder workflows.
7. Use AI to autonomously approve requests, dispatch medicines, or modify stock.
8. Allow AI to generate unsupported health predictions or fabricated statistics.
9. Present predicted outcomes as confirmed facts.
10. Allow AI-generated diagnoses or automated clinical decisions.
11. Expose sensitive data in browser storage, URLs, logs, or AI prompts unnecessarily.
12. Bypass backend authorization using frontend-only role checks.
13. Break the existing application layout or replace the global design system.
14. Use fixed-width layouts that overflow on mobile.
15. Remove existing features or dependencies without checking their impact.
16. Introduce unnecessary frameworks or duplicate backend services.
17. Leave TODOs or unfinished functionality in required user workflows.
18. Claim a feature works unless it has been implemented and tested.



# 19. UI/UX AND RESPONSIVE DESIGN



The interface must be modern, professional, clean, attractive, and suitable for government health administration.



Design principles:



* Clear visual hierarchy.
* Consistent typography, spacing, and component styles.
* Professional dashboard cards and readable charts.
* Easy-to-understand labels and navigation.
* Consistent colors for status and severity.
* Minimal clutter and unnecessary animations.
* Clear confirmations for important actions.
* Helpful empty states and error messages.



Responsive requirements:



Desktop:



* Sidebar navigation.
* Multi-column dashboard layout.
* Full tables and analytics.



Tablet:



* Collapsible sidebar.
* Adaptive cards and charts.
* Responsive tables with horizontal scrolling or alternative layouts.



Mobile:



* Compact navigation or drawer.
* Single-column layouts where appropriate.
* Stacked cards.
* Mobile-friendly forms and dialogs.
* Readable charts.
* No clipped content or horizontal page overflow.



Do not use fixed pixel widths for major page containers.



Use responsive CSS, flexible grids, fluid sizing, and appropriate breakpoints.



Verify that modals, dropdowns, tables, charts, and navigation remain usable at different screen sizes.



Do not redesign other roles' UI or change global styles in ways that break their layouts.



# 20. SECURITY AND PRIVACY



Implement:



* Role-based access control.
* State-level data isolation.
* Secure session handling.
* Server-side authorization.
* Input validation and sanitization.
* Protection against SQL injection, XSS, CSRF, and unauthorized API access where applicable.
* Rate limiting for sensitive endpoints and AI requests.
* Secure file uploads and report exports.
* Safe handling of secrets and environment variables.
* Audit logging for important actions.
* Appropriate data retention and privacy controls.



AI services must receive only the minimum authorized data needed for a request.



Do not send patient-identifiable or unrelated confidential data to AI services.



# 21. FAILURE HANDLING



Handle these situations gracefully:



* Slow or unavailable internet.
* Backend or database failure.
* AI service timeout or failure.
* Missing or incomplete district reports.
* Unauthorized district access.
* Invalid forms.
* Duplicate approval or escalation submissions.
* Expired authentication session.
* Failed report generation or export.
* Empty dashboard data.
* Invalid or insufficient data for predictions.



Show meaningful messages and recovery actions.



Do not show false success messages when an operation fails.



Use safe retries and prevent duplicate consequential actions.



# 22. TESTING AND ACCEPTANCE CRITERIA



Before completion, test:



Authentication:



* Authorized Role 09 can log in.
* Other roles cannot access Role 09 pages without permission.
* State isolation is enforced by the backend.



Navigation:



* Every navbar item opens the correct page.
* Browser refresh and direct navigation work.
* No broken routes or dead buttons.



Data:



* Dashboard values come from authorized backend data.
* Filters, search, sorting, and pagination work.
* Reports and alerts show correct status and timestamps.
* Approval and escalation actions update the correct records.



AI:



* AI answers only from authorized state-scoped information.
* AI clearly distinguishes facts from predictions.
* Insufficient data produces an appropriate response.
* AI failures do not break the dashboard.
* AI cannot independently execute administrative actions.



UI:



* Test mobile, tablet, laptop, and desktop layouts.
* No broken navbar, overlapping components, clipped text, or horizontal overflow.
* Forms, dialogs, tables, charts, and buttons remain usable.



Security:



* Test unauthorized API requests.
* Test cross-state data access.
* Test input validation and access control.
* Verify audit logs for consequential actions.



Run existing tests and add appropriate unit, integration, API, and end-to-end tests.



Fix discovered issues before marking the module complete.



# 23. FINAL IMPLEMENTATION INSTRUCTIONS



Work in this order:



Phase 1: Inspect the existing project, understand the architecture, identify reusable components, APIs, authentication, and database entities.



Phase 2: Implement Role 09 routing, role-based access, state-scoped dashboard, navbar, and core pages.



Phase 3: Connect district reports, alerts, approvals, schemes, analytics, and notifications to functional backend workflows.



Phase 4: Integrate the State Health Administrator-specific AI assistant with authorized data, explainable insights, and safe fallbacks.



Phase 5: Complete responsive design, accessibility, security, and testing.



Phase 6: Verify all navbar links, forms, actions, APIs, AI workflows, and layouts.



Do not stop after generating the UI. Complete the frontend, backend integration, database operations, authorization, and working user flows.



At the end, provide a concise implementation summary listing:



* Pages implemented.
* APIs and database entities reused or created.
* AI capabilities implemented.
* Security and role restrictions implemented.
* Tests executed and their actual results.
* Any remaining limitations or external configuration required.



FINAL GOAL:



Deliver a production-oriented, fully functional, responsive, secure, and user-friendly State Health Administrator module that fits seamlessly into the existing Smart Health & Supply Chain Resilience PWA, without breaking any other role or existing functionality.




# 12. ROLE 10 — State Supply Chain / Warehouse Manager


**Role purpose (master summary):** State supply-chain and warehouse role covering state inventory, district requests, allocation/redistribution, dispatch, procurement/replenishment coordination, shortages, expiry, emergency supply, and forecasting.


### Detailed requirements from the uploaded role specification


# ROLE 10: STATE SUPPLY CHAIN / WAREHOUSE MANAGER



## Complete Development Prompt



You are a senior full-stack developer, product architect, UI/UX designer, AI/ML architect, security engineer, and database engineer.



Build a complete, functional, responsive State Supply Chain / Warehouse Manager module for the existing Smart Health & Supply Chain Resilience PWA.



IMPORTANT:
Focus ONLY on Role 10 – State Supply Chain / Warehouse Manager.



Do not redesign, replace, or modify the existing modules for other roles. Integrate Role 10 into the existing application architecture, authentication, database, routing, design system, and shared components.



This must be a working application module, not a static dashboard or frontend-only demo.



All navbar items, buttons, forms, tables, filters, APIs, AI features, inventory operations, and workflows must function correctly.



Preserve all existing role functionality and permissions.



# 1. ROLE PURPOSE



The State Supply Chain / Warehouse Manager is responsible for managing and coordinating state-level medicine and essential medical supply operations.



The role must manage:



* State warehouse inventory.
* Medicine stock availability.
* Batch numbers and expiry dates.
* District-wise medicine requests.
* State-level stock allocation and redistribution.
* Dispatch and delivery tracking.
* Replenishment and procurement coordination.
* Supply shortages and expiry risks.
* Emergency medicine supply coordination.
* State-level supply chain reports.
* AI-powered automatic shortage detection and demand forecasting.



The main objective is to ensure that essential medicines and medical supplies are available at the required facilities through effective state-level supply coordination.



The manager must be able to identify supply issues early, coordinate with district authorities, and make informed allocation and replenishment decisions.



# 2. ROLE ACCESS AND CONNECTIONS



Implement the following logical project connections.



## Role 05 – Pharmacist / PHC Storekeeper



Information received:



* PHC medicine stock.
* Medicine consumption.
* Stock-out and low-stock requests.
* Replenishment requirements.
* Batch and expiry information.
* Actual receipt confirmation, where authorized.



The Pharmacist normally communicates supply requirements through the District Supply Chain Officer workflow.



Do not require pharmacists to manually report the same data repeatedly if it is already available in the system.



## Role 07 – District Supply Chain Officer



Information received:



* District-level consolidated medicine requests.
* District warehouse stock availability.
* District-level shortages.
* Pending replenishment requests.
* District allocation requirements.
* Receipt confirmation and stock discrepancy reports.



Information sent to Role 07:



* State allocation decisions.
* Approved quantities.
* Dispatch details.
* Shipment status.
* Replenishment coordination updates.
* Shortage and stock availability summaries.



## Role 08 – District Emergency Coordinator



Information received:



* Emergency medicine requirements.
* Emergency supply requests.
* Affected districts and facilities.
* Urgent medical resource requirements.



Information sent:



* Emergency supply availability.
* Approved allocation details.
* Dispatch and delivery status.
* Relevant supply coordination updates.



## Role 09 – State Health Administrator



Information sent:



* State-wide essential medicine availability.
* Critical medicine shortage summaries.
* Districts with significant supply gaps.
* Major unresolved supply issues.
* Emergency supply status.
* State-level supply chain reports.



The State Health Administrator has health administration and oversight responsibilities, while Role 10 manages operational supply chain activities.



## Role 11 – State Public Health Analyst



Information shared:



* Aggregated medicine consumption.
* Medicine availability trends.
* District-level supply gaps.
* Validated supply and demand data.
* Historical stock and distribution trends.



The analyst may use authorized data for public health analysis and forecasting.



## Role 12 – National Health Authority



Provide authorized state-level aggregated supply chain reports and relevant information required by the configured national reporting workflow.



Do not give Role 12 unrestricted access to operational warehouse controls.



## Warehouse Staff and Procurement Personnel



Where these users or integrations exist in the project, connect authorized workflows for:



* Physical stock receipt.
* Batch and expiry verification.
* Warehouse stock movement.
* Procurement status.
* Purchase order status.
* Supplier delivery information.
* Dispatch preparation and confirmation.



Do not invent external integrations or assume a supplier API exists. Reuse existing services or provide clearly configured integration interfaces.



# 3. AUTHENTICATION AND ROLE ACCESS CONTROL



Implement:



* Secure login through the existing authentication system.
* Role 10-specific routing.
* Authorized state and warehouse assignment.
* Secure session management.
* Logout.
* Session expiration handling.
* Unauthorized access screens.
* Profile and account settings.



The logged-in manager must access only assigned state and warehouse data.



Enforce all permissions on the backend.



Do not rely only on frontend role checks.



The manager must not access:



* Individual patient records.
* Patient medical histories.
* Individual prescriptions.
* Clinical diagnosis and treatment workflows.
* Unassigned states' restricted warehouse information.
* Platform-wide user administration.
* Super Admin settings.
* Unauthorized procurement or financial approvals.



Only allow inventory, allocation, dispatch, and procurement actions explicitly permitted by the configured role permissions.



# 4. NAVBAR AND PAGE STRUCTURE



Create the following working navbar pages:



1. State Supply Dashboard
2. Warehouse Inventory
3. District Supply Requests
4. Allocation & Redistribution
5. Dispatch & Delivery Tracking
6. Procurement & Replenishment
7. Supply Chain Reports & Analytics
8. AI Supply Chain Assistant
9. Notifications
10. Profile & Settings



Every navbar item must open its correct page.



Requirements:



* Highlight the active navigation item.
* Support desktop sidebar navigation.
* Support collapsible or drawer navigation on tablets and mobile.
* Keep navigation consistent across pages.
* Implement breadcrumbs where useful.
* Support direct page navigation and browser refresh.
* Display loading, empty, error, and success states.
* Prevent broken links and dead buttons.
* Preserve existing global navigation conventions.



Do not create placeholder pages or buttons that do nothing.



# 5. STATE SUPPLY DASHBOARD



Build a functional state-level supply chain dashboard.



## A. Overview Cards



Display actual authorized data for:



* Total medicines tracked.
* State warehouse stock status.
* Low-stock medicines.
* Critical stock-out risks.
* Pending district requests.
* Pending allocation decisions.
* Dispatches in transit.
* Expiry-risk batches.
* Pending receipt confirmations.



Use real backend data.



Never hardcode production statistics.



If sample data is used for development or demonstration, clearly label it as demo data.



## B. State Warehouse Summary



Show:



* Warehouse name.
* Medicine availability.
* Available quantity.
* Reserved quantity.
* Pending inward stock.
* Batch and expiry information.
* Last verified stock update.



Support authorized warehouse filtering where multiple warehouses exist.



## C. District Supply Overview



Display a district-wise table containing:



* District name.
* Submitted requests.
* Critical medicine shortages.
* Allocation status.
* Dispatch status.
* Pending receipt confirmations.
* Last update.



Provide search, sorting, filtering, pagination, and district details.



## D. Supply Trends



Show charts for:



* Medicine consumption trends.
* Stock availability over time.
* District-wise demand.
* Pending supply requests.
* Dispatch and delivery trends.
* Expiry-risk quantities.



Use validated data and clear reporting periods.



## E. Automatic AI Alerts



Show AI-generated alerts for:



* Predicted stock-outs.
* Increasing demand.
* Expiry risk.
* Unusual consumption.
* Potential dispatch delays.
* Districts requiring supply review.



Display alert severity, source, detection time, supporting data, and recommended action.



# 6. WAREHOUSE INVENTORY



Build a complete inventory management page.



Each medicine inventory record should support:



* Medicine ID.
* Medicine name.
* Generic name, where available.
* Category.
* Strength and dosage form.
* Unit of measurement.
* Batch number.
* Manufacturing date, if available.
* Expiry date.
* Available quantity.
* Reserved quantity.
* Damaged or quarantined quantity.
* Warehouse location.
* Supplier or receipt reference.
* Last updated timestamp.



Implement:



* Search by medicine name, code, or batch.
* Filters by warehouse, category, availability, and expiry.
* Sort and paginate inventory.
* Medicine details.
* Batch-wise stock details.
* Low-stock indicators.
* Expiry alerts.
* Authorized inward and outward stock transactions.
* Inventory movement history.



All stock modifications must be recorded as validated transactions.



Do not allow silent quantity changes.



For physical stock adjustments, require an authorized user, a reason, and an audit record.



Implement appropriate duplicate transaction protection.



# 7. DISTRICT SUPPLY REQUESTS



Build a working district request management module.



Display requests submitted by authorized district supply officers.



Each request should contain:



* Request ID.
* District.
* Medicine and required quantity.
* Available district stock, when provided.
* Reported consumption.
* Request priority.
* Request date.
* Supporting reason.
* Current status.
* Requesting officer.



Provide:



* Search and filters.
* Request details.
* Supporting information.
* Request validation.
* Approve, partially approve, reject, or request clarification where permitted.
* Approval reason.
* Request history.
* Status tracking.



Possible statuses:



Submitted → Under Review → Approved / Partially Approved / Rejected / Clarification Requested → Allocated → Dispatched → Received → Closed



Only implement valid transitions.



Require a reason for rejection or partial approval.



Prevent duplicate approvals and concurrent allocation conflicts.



Do not automatically approve requests using AI.



# 8. ALLOCATION & REDISTRIBUTION



Implement a complete state-level stock allocation workflow.



The manager must be able to:



* Review approved district requests.
* View available warehouse stock.
* View reserved stock.
* Review pending dispatch quantities.
* Compare requests with actual available stock.
* Allocate available quantities to authorized districts.
* Create allocation records.
* Review redistribution requests.
* Track allocation status.
* Maintain allocation history.



Allocation must consider:



* Verified available stock.
* Existing reservations.
* Approved district requirements.
* Reported urgency.
* Emergency requirements.
* Expiry and batch suitability.
* Existing allocation commitments.



Use FEFO (First Expiry, First Out) for suitable batches where applicable.



Do not allocate expired, quarantined, or unavailable stock.



Do not allocate the same physical stock multiple times.



Implement database transactions or equivalent concurrency controls to prevent overselling or double allocation.



Require human authorization for allocation decisions.



AI may recommend quantities and priorities but must not execute the allocation automatically.



# 9. DISPATCH & DELIVERY TRACKING



Build a complete dispatch management module.



Features:



* Create authorized dispatch orders from approved allocations.
* Select appropriate warehouse batches.
* Record dispatch quantities.
* Generate dispatch references.
* Assign transport or delivery information where supported.
* Record dispatch date and time.
* Track shipment status.
* Record expected delivery date where available.
* Record delivery delays.
* View dispatch history.



Possible shipment statuses:



Pending → Prepared → Dispatched → In Transit → Delivered / Partially Delivered / Delivery Exception → Reconciled



Actual delivery must be confirmed by the authorized receiving officer.



Implement receipt confirmation containing:



* Dispatch reference.
* Receiving district or facility.
* Actual quantity received.
* Damaged or missing quantity.
* Batch details.
* Receipt date.
* Receiving officer.
* Discrepancy reason where applicable.



Do not increase district or PHC inventory merely because a dispatch order was created.



Only verified receipt confirmation may update the receiving inventory.



Reconcile dispatch and receipt quantities.



Record discrepancies and create authorized follow-up workflows.



# 10. PROCUREMENT & REPLENISHMENT



Create a procurement and replenishment planning module.



The manager must be able to:



* Review low-stock and predicted shortage medicines.
* View historical consumption.
* View pending district requests.
* Review existing procurement or replenishment records.
* Create replenishment proposals where authorized.
* Track procurement request status.
* View supplier delivery status when supported.
* Monitor pending inward stock.
* Track procurement and replenishment history.



The AI may suggest:



* Which medicines require replenishment review.
* Estimated replenishment quantities.
* Potential reorder timing.
* Medicines with sustained demand increases.



All quantities must be clearly marked as estimates or recommendations when generated by AI.



Procurement approval, purchase order issuance, and financial commitments must follow the configured authorization workflow.



Do not place real procurement orders or make payments without an explicitly authorized integration and approval.



# 11. AUTOMATIC AI MONITORING ENGINE



This is a mandatory core requirement.



The State Supply Chain AI must NOT depend on the manager manually entering a question or uploading data.



Implement an automatic background monitoring system.



The backend must automatically analyze authorized data whenever relevant data changes and at configured intervals.



## A. Event-Driven Analysis



Trigger analysis when:



* Warehouse stock changes.
* New district requests are submitted.
* Allocation quantities change.
* Dispatch or receipt status changes.
* New consumption reports arrive.
* New batch or expiry data is recorded.
* Procurement or supplier delivery status changes.



Use the existing event infrastructure where available.



Otherwise, implement suitable backend event handlers or queued background jobs.



## B. Scheduled Monitoring



Implement configurable scheduled jobs to periodically:



* Check low-stock thresholds.
* Evaluate stock-out risk.
* Recalculate demand forecasts.
* Check batch expiry risk.
* Review pending dispatches.
* Detect overdue deliveries.
* Identify unresolved supply issues.
* Generate relevant alerts.



Do not run expensive AI inference unnecessarily for every page load.



Use appropriate scheduling, deduplication, caching, and background processing.



## C. Automatic Alert Generation



When a valid rule or model detects an issue, automatically create or update an alert.



Each alert must contain:



* Alert ID.
* Medicine or supply item.
* Affected warehouse or district.
* Alert category.
* Severity.
* Detection timestamp.
* Supporting data.
* Model or rule used.
* Confidence or uncertainty where supported.
* Recommended action.
* Current status.
* Assigned authority.



Deduplicate repeated alerts for the same unresolved issue.



Update existing alerts when the underlying risk changes.



Automatically resolve alerts only when the configured validated resolution conditions are met.



Maintain alert history.



## D. Notification Delivery



Automatically notify the authorized Role 10 user when important supply risks are detected.



Use the existing in-app notification system.



Where configured and supported, integrate email, SMS, or other notification channels.



Do not claim external notifications are working unless the relevant provider is configured and tested.



Support notification priority, read/unread state, and navigation to the relevant record.



If the AI service is unavailable, critical rule-based inventory alerts must continue to work.



# 12. ROLE 10 AI ASSISTANT



Build a dedicated State Supply Chain AI Assistant.



It must serve ONLY Role 10 and use only authorized state and warehouse data.



The AI assistant complements automatic background monitoring; it does not replace it.



## A. Demand Forecasting



Analyze:



* Historical medicine consumption.
* District requests.
* Stock movement.
* Seasonal patterns when sufficient data exists.
* Current availability.
* Validated demand trends.



Predict potential future medicine demand over configured forecast periods.



Display:



* Medicine.
* District or warehouse.
* Forecast period.
* Estimated demand.
* Relevant historical data.
* Uncertainty or prediction interval where statistically supported.
* Key factors.
* Recommended review action.



Do not fabricate forecast values or confidence percentages.



If data is insufficient, clearly indicate that a reliable forecast is unavailable.



## B. Stock-Out Prediction



Automatically detect and predict possible shortages using:



* Available stock.
* Reserved quantities.
* Historical consumption.
* Pending approved requests.
* Expected replenishment.
* Verified incoming stock.
* Lead-time data where available.



Estimate days of stock remaining only when the underlying consumption and stock data support the calculation.



Show the calculation basis.



Generate shortage-risk alerts and recommendations.



## C. Allocation Recommendations



Recommend district allocation options based on:



* Available and unreserved stock.
* District requirements.
* Verified urgency.
* Emergency requests.
* Supply commitments.
* Expiry and batch suitability.



Explain why a district or medicine requires attention.



Do not automatically approve, reject, or execute allocations.



## D. Expiry Risk Detection



Automatically analyze batch expiry dates, available quantities, and validated consumption data.



Identify batches that may expire before expected utilization.



Suggest:



* Reviewing FEFO dispatch.
* Checking authorized redistribution opportunities.
* Reviewing district demand.
* Escalating potential wastage risks.



Do not automatically transfer stock between warehouses.



## E. Supply Anomaly Detection



Detect unusual patterns such as:



* Unexpected consumption changes.
* Stock discrepancies.
* Repeated emergency requests.
* Unusual inventory adjustments.
* Mismatches between dispatch and receipt.
* Unusual supplier delivery delays.



Flag these for human review.



Do not automatically accuse users of fraud or misconduct.



## F. Supply Chain AI Chat



Allow the manager to ask:



* Which medicines have critical shortage risks?
* Which districts have pending supply requests?
* Which batches are at risk of expiry?
* What deliveries are overdue?
* What stock is available for a new district request?
* Summarize state supply chain status.
* Why did the system generate this alert?



The assistant must answer using authorized, current data.



Provide source references, data timestamps, explanations, and clear uncertainty.



Support Tamil and English, and Tanglish input where feasible.



Optional voice input may be implemented with graceful fallback.



Do not expose patient-identifiable information or unauthorized data.



# 13. AI SAFETY AND HUMAN OVERSIGHT



AI must operate as a decision-support system.



AI may:



* Monitor.
* Detect.
* Predict.
* Generate alerts.
* Recommend.
* Explain.
* Summarize.



AI must not independently:



* Modify inventory quantities.
* Approve or reject district requests.
* Commit warehouse stock to an allocation.
* Dispatch medicines.
* Issue procurement orders.
* Make financial commitments.
* Confirm physical delivery.
* Override authorized human decisions.



All consequential actions must require authenticated, authorized human approval.



Store AI recommendation history and relevant human decisions.



Allow the manager to accept, dismiss, or request clarification for AI recommendations.



Do not treat AI confidence as proof of correctness.



# 14. NOTIFICATIONS



Build a functional notification center.



Notify authorized users about:



* Critical low-stock alerts.
* Predicted shortages.
* New district requests.
* Emergency supply requests.
* Pending allocation decisions.
* Dispatch delays.
* Expiry risks.
* Delivery discrepancies.
* Procurement updates.
* AI-generated insights requiring review.



Implement:



* Read and unread status.
* Notification categories.
* Priority.
* Timestamp.
* Related record navigation.
* Mark as read.
* Appropriate notification preferences.



Notifications must be scoped to the user's authorized state and role.



# 15. REPORTS & ANALYTICS



Build a supply chain reporting module.



Include:



* State warehouse inventory reports.
* Medicine availability reports.
* District demand reports.
* Allocation and redistribution reports.
* Dispatch and delivery reports.
* Expiry and wastage-risk reports.
* Procurement and replenishment reports.
* Stock movement history.
* AI forecast reports.
* Supply shortage and alert reports.



Support:



* Date-range filters.
* District and warehouse filters.
* Medicine filters.
* Category and status filters.
* Search and pagination.
* PDF and CSV export where supported.
* Print-friendly reports.



Clearly distinguish actual inventory, reported quantities, pending stock, and AI forecasts.



All reports must show the relevant reporting period and data update timestamp.



# 16. DATABASE AND DATA MODEL



Reuse the existing database and entities wherever possible.



Do not create duplicate inventory tables or a separate backend without justification.



Extend existing schemas only when necessary.



Logical entities may include:



1. Warehouses
2. Medicines / Supply Items
3. Medicine Batches
4. Inventory Balances
5. Inventory Transactions
6. District Supply Requests
7. Allocations
8. Dispatch Orders
9. Dispatch Items
10. Delivery Receipts
11. Receipt Discrepancies
12. Procurement Requests
13. Supplier Records, where applicable
14. Notifications
15. AI Alerts
16. AI Forecasts
17. AI Recommendation History
18. Audit Logs



Use appropriate primary keys, foreign keys, state and warehouse ownership, timestamps, statuses, and indexes.



Maintain inventory movement as auditable transactions.



Use database transactions and concurrency controls for stock reservation, allocation, dispatch, and receipt.



Prevent negative inventory and duplicate stock movements.



Do not allow the AI to write directly to inventory balances.



# 17. BACKEND APIs



Implement functional APIs using existing project conventions.



Suggested logical endpoints:



GET /api/supply/state/dashboard



GET /api/supply/warehouses



GET /api/supply/inventory



GET /api/supply/inventory/:itemId



GET /api/supply/inventory/:itemId/movements



GET /api/supply/district-requests



GET /api/supply/district-requests/:requestId



POST /api/supply/district-requests/:requestId/decision



GET /api/supply/allocations



POST /api/supply/allocations



GET /api/supply/dispatches



POST /api/supply/dispatches



POST /api/supply/dispatches/:dispatchId/receipt



GET /api/supply/procurement



POST /api/supply/procurement/proposals



GET /api/supply/analytics



GET /api/supply/ai/alerts



GET /api/supply/ai/forecasts



POST /api/supply/ai/chat



GET /api/supply/notifications



PATCH /api/supply/notifications/:notificationId/read



These are logical suggestions. Reuse existing endpoints and adapt to the current architecture.



Every endpoint must enforce:



* Authentication.
* Role 10 authorization.
* Assigned state and warehouse scope.
* Request validation.
* Safe stock transaction handling.
* Appropriate error handling.
* Audit logging for consequential operations.



# 18. DO'S



You MUST:



1. Inspect the existing codebase before implementation.
2. Reuse existing authentication, database, routing, components, and design system.
3. Build Role 10 as a separate authorized module.
4. Implement every required navbar page.
5. Make all forms, buttons, filters, and actions functional.
6. Connect inventory and supply workflows to the backend.
7. Implement real inventory transactions and audit history.
8. Verify stock availability before allocation.
9. Prevent double allocation and duplicate stock movements.
10. Require actual receipt confirmation before updating receiving inventory.
11. Implement automatic AI monitoring through background jobs and event triggers.
12. Implement rule-based alerts that continue working if AI services fail.
13. Generate automatic notifications for relevant supply risks.
14. Distinguish actual stock, reserved stock, incoming stock, and forecast demand.
15. Explain AI predictions and recommendations.
16. Use validated data and communicate uncertainty.
17. Require human authorization for consequential actions.
18. Enforce backend role and state access restrictions.
19. Maintain responsive layouts on mobile, tablet, laptop, and desktop.
20. Support Tamil and English and Tanglish input where feasible.
21. Include accessible controls, readable typography, and clear error messages.
22. Test all important workflows before completion.
23. Preserve all existing role modules.



# 19. DON'TS



You MUST NOT:



1. Modify or break Roles 01–09 or Roles 11–13.
2. Give Role 10 access to patient clinical records.
3. Give unrestricted cross-state or platform-wide access.
4. Build static inventory dashboards with hardcoded production numbers.
5. Create dead navbar links or non-functional buttons.
6. Make the AI depend exclusively on manual chat input.
7. Skip background monitoring or scheduled analysis.
8. Allow AI to modify actual stock balances.
9. Automatically approve requests or dispatch orders using AI.
10. Allow stock allocation beyond verified available quantity.
11. Mark goods as received without actual authorized confirmation.
12. Treat pending procurement or incoming stock as physically available stock.
13. Fabricate stock data, forecast values, confidence percentages, or supplier information.
14. Present predictions as guaranteed outcomes.
15. Automatically accuse users of fraud based on anomalies.
16. Send unauthorized patient or confidential data to AI services.
17. Store secrets in frontend code.
18. Depend only on frontend authorization.
19. Use fixed-width layouts that break on mobile.
20. Introduce unnecessary frameworks or duplicate services.
21. Claim external integrations work without configuration and testing.
22. Leave required workflows incomplete.



# 20. RESPONSIVE UI/UX REQUIREMENTS



Create a professional, modern, clean, and visually attractive government supply chain dashboard.



Use the existing project's design system.



Desktop:



* Sidebar navigation.
* Multi-column dashboard.
* Full inventory and request tables.
* Clear charts and detailed records.



Tablet:



* Collapsible sidebar.
* Responsive grids.
* Readable tables with horizontal scrolling or appropriate alternative layouts.



Mobile:



* Compact navigation or drawer.
* Single-column dashboard where appropriate.
* Stacked summary cards.
* Mobile-friendly forms and dialogs.
* Touch-friendly buttons.
* Responsive charts.
* No overlapping or clipped content.



Use flexible layouts, CSS grids, responsive breakpoints, and fluid sizing.



Test all pages at different viewport sizes.



Ensure modals, dropdowns, charts, tables, forms, and navigation work correctly.



Do not modify global CSS in ways that break other roles.



# 21. SECURITY AND PRIVACY



Implement:



* Role-based access control.
* State and warehouse data isolation.
* Secure authentication and session management.
* Backend authorization for all sensitive operations.
* Input validation and sanitization.
* Protection against SQL injection, XSS, CSRF, and unauthorized API access where applicable.
* Rate limiting for sensitive endpoints and AI requests.
* Secure file uploads and report exports.
* Safe environment variable and secret management.
* Audit logs for inventory, allocation, dispatch, procurement, and receipt actions.
* Minimum necessary data sharing with AI services.



Do not expose confidential data through URLs, browser storage, logs, or AI prompts unnecessarily.



# 22. FAILURE AND EDGE CASES



Handle:



* Network failures.
* Backend or database outages.
* AI service failures.
* Duplicate requests.
* Concurrent allocation attempts.
* Insufficient stock.
* Incorrect or missing batch details.
* Expired or quarantined stock.
* Partial deliveries.
* Missing receipt confirmations.
* Supplier delays.
* Incorrect inventory records.
* Missing historical data.
* Unavailable forecasting services.
* Expired authentication sessions.



Show meaningful error messages and recovery actions.



Do not show false success messages.



Prevent duplicate consequential operations.



If AI is unavailable, continue basic inventory management and rule-based alerts.



# 23. TESTING AND ACCEPTANCE CRITERIA



Test the complete application module.



Authentication:



* Role 10 can access assigned state and warehouse data.
* Unauthorized roles cannot access Role 10 APIs.
* Cross-state data access is blocked.



Inventory:



* Stock transactions update balances correctly.
* Negative inventory is prevented.
* Batch and expiry records are validated.
* Inventory history is maintained.



Requests and allocation:



* District requests appear correctly.
* Approval and rejection workflows function.
* Insufficient stock prevents invalid allocation.
* Concurrent allocation does not double-reserve stock.



Dispatch and receipt:



* Dispatch quantities are recorded correctly.
* Receipt confirmation updates stock correctly.
* Partial deliveries and discrepancies are handled.
* Duplicate receipts are prevented.



Automatic AI:



* Stock changes trigger the relevant analysis.
* Scheduled monitoring executes correctly.
* Shortage and expiry alerts are generated from valid data.
* Duplicate alerts are controlled.
* AI service failure does not disable critical rule-based alerts.
* Notifications reach the correct authorized users.



AI assistant:



* Responses use only authorized supply data.
* Forecasts distinguish estimates from actual stock.
* Insufficient data is handled appropriately.
* AI cannot autonomously perform restricted operations.



UI:



* Every navbar item works.
* All required pages render correctly.
* Mobile, tablet, and desktop layouts are tested.
* No horizontal overflow or broken controls.



Security:



* Backend authorization is tested.
* Invalid requests are rejected.
* Audit records are created for consequential actions.



Run unit, integration, API, and end-to-end tests.



Fix issues before marking the module complete.



# 24. IMPLEMENTATION ORDER



Phase 1: Inspect the existing project and identify reusable architecture, authentication, APIs, database entities, and design components.



Phase 2: Implement Role 10 routing, permissions, navbar, dashboard, and inventory.



Phase 3: Implement district requests, allocation, redistribution, dispatch, receipt, and replenishment workflows.



Phase 4: Implement background monitoring, scheduled jobs, event triggers, AI risk detection, and automatic notifications.



Phase 5: Implement the dedicated AI Assistant, forecasting, explainable recommendations, and reports.



Phase 6: Complete responsive UI, accessibility, security, and testing.



Phase 7: Verify every navbar item, backend workflow, stock transaction, automatic AI trigger, notification, and role permission.



Do not stop after generating the frontend.



Complete the actual backend integration, database operations, role authorization, background processing, and user workflows.



# 25. FINAL IMPLEMENTATION SUMMARY



After implementation, provide:



* Pages completed.
* APIs and database entities reused or created.
* Inventory and supply workflows implemented.
* Automatic AI triggers and scheduled jobs implemented.
* AI capabilities and limitations.
* Security and permission restrictions.
* Tests executed and actual results.
* External services requiring configuration.
* Any remaining limitations.



Do not claim an unimplemented feature is complete.



FINAL GOAL:



Deliver a complete, functional, responsive, secure, and production-oriented State Supply Chain / Warehouse Manager module.



The module must automatically monitor authorized supply chain data, detect potential problems, generate alerts and recommendations, and help the manager coordinate state-level medicine supply operations.



All consequential inventory, allocation, procurement, and dispatch decisions must remain under authorized human control.



Preserve the existing Smart Health & Supply Chain Resilience PWA and all other role modules without breaking their functionality.




# 13. ROLE 11 — State Public Health Analyst


**Role purpose (master summary):** State public-health analytics role covering aggregated health indicators, trends, data quality, anomaly/risk signals, reports, correlations with supply/emergency data, and analytical AI.


### Detailed requirements from the uploaded role specification


## ROLE 11: STATE PUBLIC HEALTH ANALYST



Build a complete, functional State Public Health Analyst module for the existing Smart Health & Supply Chain Resilience PWA.



IMPORTANT:



Before making any changes, inspect the existing codebase, framework, database, APIs, routing, authentication, authorization, design system, PHC modules, Doctor/Nurse modules, District Health Officer module, District Supply Chain Officer module, District Emergency Coordinator module, State Health Administrator module, State Supply Chain/Warehouse module, and existing AI functionality.



Reuse existing components, APIs, services, database models, authentication, authorization, reporting pipelines, notification services, and design system wherever possible.



Do not rebuild, overwrite, duplicate, or break existing modules.



Implement ONLY Role 11 — State Public Health Analyst in this phase.



Do not implement or modify other roles.



The State Public Health Analyst is responsible for state-level public health data analysis, health trend monitoring, public health insights, data quality analysis, and analytical reporting.



This role is an analytics and decision-support role, NOT a clinical, administrative, supply-chain operational, or platform administration role.



---



# 1. ROLE AND PURPOSE



The State Public Health Analyst analyses authorized, aggregated health and operational data across districts and PHCs within the assigned state.



Main responsibilities:



* Analyse state-wide and district-wise health indicators.
* Monitor disease-related trends and service utilization.
* Identify unusual changes in reported health indicators.
* Analyse public health patterns and potential risks.
* Combine health indicators with authorized supply-chain and emergency summaries.
* Identify reporting gaps and data-quality issues.
* Generate state-level and district-level analytical reports.
* Provide evidence-based insights to the State Health Administrator.
* Use AI for automated analysis, trend summaries, anomaly detection, and decision support.



The Analyst should be able to understand:



1. What is happening across the state?
2. Which districts or PHCs show significant changes?
3. How reliable and complete is the available data?
4. What patterns require further verification?
5. Which districts may need additional investigation or administrative review?
6. What information should be communicated to the State Health Administrator?



The Analyst must NOT:



* Diagnose individual patients.
* Prescribe medicines.
* Make clinical decisions.
* Declare a confirmed outbreak independently.
* Approve or issue administrative directives.
* Modify PHC or district health records.
* Modify medicine inventory.
* Allocate or dispatch medicines.
* Approve procurement.
* Manage warehouse operations.
* Manage staff attendance.
* Administer users, permissions, or the platform.



---



# 2. ROLE 11 DASHBOARD



Create a dedicated State Public Health Analyst dashboard.



Dashboard overview should contain:



## A. State Health Overview



* Total districts within the authorized state.
* Reporting districts.
* PHC reporting coverage.
* Health indicators received.
* Reporting completeness.
* Last data synchronization time.
* Data validation status.



Do not display fabricated numbers or hardcoded health statistics.



All dashboard metrics must come from the actual database or clearly labelled sample data used only in development.



## B. Health Trend Overview



Display:



* Disease-related indicators available in the system.
* Health service utilization trends.
* District-wise changes in reported indicators.
* Weekly and monthly comparisons.
* Historical trends where sufficient data exists.



## C. Public Health Alerts



Display:



* Unusual increases in health indicators.
* Potential public health risk signals.
* Districts requiring data verification.
* Missing or delayed health reports.
* AI-generated analytical alerts requiring review.



## D. Health and Supply Chain Overview



Display:



* Aggregated medicine consumption trends.
* District-level stock shortage summaries.
* Essential medicine availability trends.
* Supply delays and reported health-service impact.
* Districts with simultaneous health demand and supply concerns.



Do not expose detailed operational warehouse controls.



## E. Emergency Impact Overview



Display authorized aggregated emergency information:



* Affected districts and PHCs.
* Reported healthcare service disruption.
* Emergency-related health indicators.
* Aggregated emergency impact trends.



Do not replace the District Emergency Coordinator's operational workflow.



## F. Dashboard Navigation



Create the following navigation:



1. Public Health Dashboard
2. Health Trends
3. District Analysis
4. Public Health Alerts
5. Health and Supply Analysis
6. Emergency Impact Analysis
7. Data Quality
8. Reports
9. AI Insights
10. Notifications
11. Profile and Settings



Reuse existing routing and layout patterns.



Only show modules authorized for Role 11.



---



# 3. DATA SOURCES AND ROLE CONNECTIONS



The Analyst must receive authorized, aggregated data from existing modules.



Do not make PHC staff manually send duplicate reports to Role 11 if their information is already available through the existing reporting workflow.



## A. Doctor — Role 02



Source data:



* Authorized aggregated disease-related indicators.
* Aggregated patient visit counts.
* Approved clinical/service indicators.
* Reporting period and validation status.



Data flow:



Doctor records clinical information in the existing authorized clinical module.



The existing reporting service produces approved aggregated indicators.



Role 11 receives the authorized aggregate, not unrestricted individual patient records.



## B. Nurse / Healthcare Staff — Role 03



Source data:



* Aggregated healthcare service information.
* Authorized observations and service indicators.
* Reporting completeness information.



Data flow:



Nurse records information in the existing PHC module.



Approved indicators are included in the PHC reporting workflow and made available to Role 11 through authorized aggregation.



Do not duplicate the same patient visit across Doctor and Nurse reports.



Use existing data definitions and unique reporting rules.



## C. PHC In-charge — Role 04



Source data:



* PHC-level reports.
* PHC reporting status.
* Service availability summaries.
* Validated or reviewed PHC indicators.
* Reporting gaps and corrections.



The PHC In-charge remains responsible for PHC-level operations and reporting workflows.



Role 11 receives aggregated and authorized information.



## D. Pharmacist / PHC Storekeeper — Role 05



Source data:



* Aggregated medicine consumption.
* Medicine demand trends.
* PHC stock availability summaries.
* Stock-out periods.
* Expiry and shortage indicators where authorized.



The Pharmacist records actual stock and consumption in the existing inventory module.



Role 11 receives analytical summaries only.



Do not allow Role 11 to modify medicine stock or inventory transactions.



## E. District Health Officer — Role 06



The DHO is the primary district-level health reporting and verification connection.



Receive:



* District health summaries.
* Consolidated PHC indicators.
* District-wise disease-related trends.
* Healthcare service utilization.
* Health reporting coverage.
* Data validation and verification status.
* District health impact summaries.



Data flow:



PHC staff enter data in existing modules.



The district reporting workflow consolidates and validates relevant indicators.



Role 06 reviews district health reporting and makes authorized summaries available to Role 11.



Role 11 analyses the district reports and identifies state-level trends.



If a report is incomplete or inconsistent, Role 11 can request verification through the authorized reporting workflow.



Do not allow Role 11 to directly edit DHO or PHC source records.



## F. District Supply Chain Officer — Role 07



Receive authorized district supply summaries:



* Medicine demand.
* Medicine consumption.
* District-level shortages.
* Essential medicine availability.
* Supply request status.
* Aggregated supply fulfilment information.



Do not duplicate district supply reports already consolidated by Role 10.



## G. District Emergency Coordinator — Role 08



Receive authorized aggregated emergency impact data:



* Affected PHCs and districts.
* Healthcare service disruptions.
* Emergency-related health indicators.
* Resource gap summaries.
* Emergency response status where relevant.



Do not access unnecessary operational or patient-level emergency records.



The Emergency Coordinator remains responsible for emergency coordination.



## H. State Health Administrator — Role 09



The State Health Administrator is the primary recipient of Role 11's analytical reports and insights.



Role 11 provides:



* State health trend reports.
* District-wise analytical summaries.
* Public health risk signals.
* Data quality and reporting completeness reports.
* Health and supply-chain gap analysis.
* Emergency impact analysis.
* AI-generated draft insights reviewed by the Analyst.



Role 09 reviews the information and makes administrative decisions within their authority.



Role 11 must not independently issue administrative directives.



## I. State Supply Chain / Warehouse Manager — Role 10



Receive authorized state-level supply summaries:



* State warehouse availability summaries.
* District-level medicine availability.
* Aggregated consumption trends.
* Supply fulfilment and delivery delays.
* Shortage trends.
* State-wide supply gap indicators.



Use Role 10's existing authorized reporting interface or service.



Combine supply summaries with health indicators only when the reporting periods, geographical scope, and indicator definitions are compatible.



Role 10 remains responsible for actual inventory, allocation, dispatch, and procurement workflows.



## J. National Health Authority — Role 12



Where explicitly authorized, provide aggregated state-level health reports and analytical summaries.



Do not expose patient-level or unnecessary district-level identifiable information to national users.



Do not create an unrestricted direct connection.



All state-to-national reporting must follow configured authorization and reporting workflows.



---



# 4. DATA INGESTION AND ANALYTICAL WORKFLOW



Implement the following workflow:



PHC Data Entry
→ Existing PHC Reporting Workflow
→ District Validation and Consolidation
→ Authorized State Data Pipeline
→ Role 11 Analytics
→ AI Insights and Reports
→ Analyst Review
→ Role 09 State Health Administrator



For supply data:



PHC Pharmacist
→ District Supply Reporting
→ Role 07 DSCO
→ Role 10 State Supply Chain Manager
→ Authorized State Supply Summary
→ Role 11 Analysis



For emergency data:



PHC / District Emergency Reporting
→ Role 08 District Emergency Coordinator
→ Authorized District/State Emergency Summary
→ Role 11 Analysis



Important implementation requirements:



* Reuse existing reporting pipelines.
* Do not require redundant manual submissions.
* Do not assume external government integrations already exist.
* Use existing APIs and database models where available.
* Clearly identify missing integrations or data sources.
* Do not fabricate unavailable data.
* Preserve original source references and timestamps.
* Maintain reporting period, geography, indicator definition, and validation status.
* Support configurable reporting schedules.
* Support event-triggered data refresh when relevant source data changes.
* Support scheduled daily, weekly, or monthly analysis where appropriate.



---



# 5. HEALTH TREND ANALYSIS



Create a Health Trends module.



The Analyst should be able to select:



* Health indicator.
* Disease or service category where configured.
* State or district.
* PHC where authorized and necessary.
* Reporting period.
* Historical comparison period.



Provide:



* Time-series charts.
* District-wise comparison.
* Weekly and monthly trends.
* Percentage and absolute changes.
* Reporting coverage.
* Data source and last updated timestamp.



Calculate changes correctly.



Example:



Previous period: 100 recorded fever-related visits.



Current period: 250 recorded fever-related visits.



Calculated change: 150% increase.



The system must identify these as recorded visits, not confirmed disease incidence.



Do not calculate rates without a valid denominator.



If population data is available and authorized, use the appropriate population and reporting period.



If the denominator or baseline is unavailable, show absolute counts and clearly state the limitation.



Do not compare different reporting periods without explaining the difference.



Do not present incomplete data as a complete state-wide trend.



---



# 6. DISTRICT ANALYSIS



Create a District Analysis module.



The Analyst can:



* Select a district.
* View authorized aggregated health indicators.
* Compare district trends with state-level summaries.
* Review PHC reporting coverage.
* Identify missing reports.
* Review district-level public health alerts.
* Review aggregated health and supply gaps.
* View historical indicators where available.



Display:



* District name.
* Reporting period.
* Indicators received.
* Number of reporting PHCs.
* Reporting completeness.
* Data validation status.
* Trend changes.
* Relevant source references.
* AI-generated insights requiring review.



Do not create a political or administrative performance ranking of districts.



District comparisons must be descriptive and account for differences in population, PHC coverage, reporting completeness, and reporting periods.



Do not expose individual patient information.



---



# 7. AUTOMATIC AI ANALYTICS



AI must be integrated into the actual backend workflow.



IMPORTANT:



The Analyst should NOT have to manually upload data or repeatedly ask the AI to analyse new information.



The backend must automatically analyse available authorized data when relevant data is updated and when scheduled analytical jobs run.



AI must be a decision-support system, not an autonomous public health authority.



## A. Automatic Health Trend Detection



AI analyses available historical and current health indicators.



It can:



* Summarize increasing or decreasing trends.
* Identify districts with notable changes.
* Compare current and previous reporting periods.
* Explain which indicators contributed to an observed change.
* Highlight trends that require further verification.



Use statistical methods for numerical calculations.



Use AI for interpretation, summarization, and contextual explanation.



Do not rely on an LLM alone for mathematical calculations.



## B. Anomaly Detection



Identify unusual changes in reported health indicators.



Examples:



* Sudden increase in reported cases.
* Unexpected changes in PHC service utilization.
* Unusual district-level reporting patterns.
* Significant deviations from an established historical baseline.



Use statistical anomaly detection, configured thresholds, and historical baselines where sufficient data exists.



Distinguish between:



* Confirmed data-quality errors.
* Unusual but potentially valid observations.
* Insufficient data for analysis.



Do not label every unusual increase as an outbreak.



Do not create fabricated baselines or confidence scores.



If historical data is insufficient, show a transparent rule-based alert or indicate insufficient data.



## C. Public Health Risk Insights



AI can identify potential public health concerns based on authorized indicators.



It may:



* Highlight districts requiring review.
* Summarize multiple related indicators.
* Identify simultaneous increases across multiple PHCs.
* Suggest verification or investigation.
* Prepare a public health situation summary.



AI must never independently:



* Confirm an outbreak.
* Diagnose patients.
* Declare a disease emergency.
* Issue medical instructions.
* Order public health interventions.
* Make administrative decisions.



All important public health conclusions require authorized human review.



## D. Health and Supply Chain Correlation



Combine health indicators with authorized supply data from Role 07 and Role 10.



AI can identify patterns such as:



* Increased service demand with declining medicine availability.
* Increasing medicine consumption.
* Simultaneous health demand and supply delays.
* Districts reporting healthcare service disruption during shortages.



Example:



"Several PHCs show increased fever-related visits during the reporting period. Some of the same PHCs also report reduced availability of relevant medicines. District health and supply teams should verify the reported situation."



AI must:



* Check that the reporting periods match.
* Check that the geography matches.
* Identify the data sources.
* Explain limitations.
* Avoid claiming that one indicator caused another without supporting evidence.



AI must not modify inventory, allocate medicines, approve procurement, or initiate supply transactions.



## E. Emergency Impact Analysis



Analyse authorized aggregated emergency information.



AI can:



* Summarize affected districts and PHCs.
* Identify reported healthcare service disruption.
* Highlight emergency-related health indicators.
* Summarize reported resource gaps.
* Compare emergency impact across reporting periods.



Do not replace the Emergency Coordinator's operational role.



Do not make emergency severity or closure decisions.



## F. AI Report Generation



Generate draft reports:



1. Weekly State Health Summary.
2. Monthly State Health Report.
3. District Health Trend Report.
4. Public Health Alert Summary.
5. Health and Supply Gap Report.
6. Emergency Impact Report.
7. Data Quality and Reporting Completeness Report.



Every AI-generated report must include:



* Reporting period.
* Geographic scope.
* Data sources.
* Indicators used.
* Important observations.
* Data limitations.
* Suggested follow-up.
* Draft/review status.
* Generation timestamp.



All AI-generated official reports must be reviewed and approved by the authorized Analyst before being sent to Role 09 or Role 12.



Do not invent statistics or citations.



## G. AI Data Quality Analysis



Identify:



* Missing district reports.
* Missing PHC submissions.
* Duplicate aggregates.
* Inconsistent reporting periods.
* Unusual changes in reported counts.
* Missing or invalid indicator definitions.
* Conflicting source values.
* Stale or delayed data.



Clearly distinguish data errors from genuine public health changes.



Do not automatically modify original source data.



Allow authorized source owners to correct records through their existing workflows.



---



# 8. AUTOMATIC MONITORING AND NOTIFICATIONS



Implement automatic monitoring through backend services.



The system must not depend exclusively on opening the AI chat or dashboard.



Use:



1. Event-driven processing when authorized source data changes.
2. Scheduled analysis jobs for daily, weekly, and monthly trends.
3. Configurable rule-based checks for important indicators.
4. Background processing for expensive analytical tasks.



When a relevant change occurs:



Source Data Updated
→ Validate Data
→ Update Analytical Dataset
→ Run Statistical/Rule-Based Analysis
→ Run AI Interpretation if appropriate
→ Create or Update Insight
→ Notify Role 11
→ Analyst Reviews



Notifications may include:



* New unusual health trend.
* Potential public health risk signal.
* Missing district reports.
* Significant data quality issue.
* Health and supply gap.
* New draft report available.



Prevent duplicate alerts using appropriate deduplication rules and alert identifiers.



Allow alerts to be acknowledged, reviewed, dismissed with a reason, or escalated through authorized workflows.



Show:



* Alert source.
* Reporting period.
* Affected geography.
* Reason for the alert.
* Validation status.
* Last updated time.



If the AI service fails, continue rule-based alerts and normal dashboard functionality.



Never mark a notification as delivered unless delivery is confirmed by the notification service.



---



# 9. AI ASSISTANT FOR ROLE 11



Create an AI assistant dedicated to state public health analysis.



The assistant should answer questions using only authorized and available data.



Example questions:



* Which districts show an increase in reported fever-related visits?
* What changed compared with the previous reporting period?
* Which districts have incomplete health reports?
* Summarize the state health situation for this week.
* Which districts show simultaneous health and supply concerns?
* What emergency-related service disruptions were reported?
* Prepare a draft analytical report for the State Health Administrator.



The assistant must:



* Use existing authorized backend data services.
* Respect Role 11's state and data access boundaries.
* Identify the reporting period and sources.
* Distinguish observed data from AI-generated interpretation.
* State when information is unavailable.
* Avoid fabricated facts.
* Avoid unsupported causal claims.
* Never reveal unauthorized patient records.
* Never execute administrative or clinical actions.



AI responses must provide clear explanations and references to the underlying authorized reports or indicators.



The chat assistant is supplementary.



Automatic monitoring and alerting must operate independently of the chat interface.



---



# 10. REPORT MANAGEMENT



Create a Reports module.



Features:



* View generated reports.
* Filter by report type.
* Filter by district.
* Filter by reporting period.
* View draft, reviewed, approved, and sent statuses.
* Review AI-generated report content.
* Edit analytical commentary where authorized.
* Approve reports.
* Send approved reports to authorized recipients.
* Export reports in supported formats.
* View report history.



Report workflow:



Data Analysis
→ Draft Report
→ Analyst Review
→ Authorized Approval
→ Send to Role 09
→ Record Delivery and Audit History



For reports sent to Role 12, enforce the configured state-to-national reporting permissions.



Do not allow unreviewed AI-generated content to become an official report automatically.



---



# 11. DATABASE AND DATA MODEL



First inspect the existing database.



Reuse existing tables, collections, and models wherever possible.



Do not create duplicate representations of existing users, PHCs, districts, medicines, emergencies, or clinical records.



Where necessary, add or extend the following entities.



## A. PublicHealthIndicator



* indicator_id
* indicator_code
* indicator_name
* indicator_category
* definition
* unit
* numerator_definition
* denominator_definition
* aggregation_level
* active
* created_at
* updated_at



Use consistent indicator definitions and versioning.



## B. HealthIndicatorAggregate



* aggregate_id
* indicator_id
* state_id
* district_id
* phc_id, if authorized and necessary
* reporting_period_start
* reporting_period_end
* indicator_value
* numerator
* denominator
* source_reference
* source_role
* validation_status
* reporting_timestamp
* last_updated_at



Avoid patient-level identifiers.



Add unique constraints to prevent duplicate aggregate submissions for the same indicator, geography, and reporting period.



## C. PublicHealthInsight



* insight_id
* insight_type
* state_id
* district_id
* indicator_id
* reporting_period
* source_references
* observation
* explanation
* limitations
* suggested_follow_up
* generated_by
* review_status
* reviewed_by
* created_at
* updated_at



## D. PublicHealthAlert



* alert_id
* alert_type
* state_id
* district_id
* related_insight_id
* source_reference
* reporting_period
* reason
* severity, if assigned through authorized rules
* status
* acknowledged_by
* acknowledged_at
* created_at
* updated_at



Do not allow AI to independently assign official emergency severity.



## E. PublicHealthReport



* report_id
* report_type
* state_id
* reporting_period_start
* reporting_period_end
* geographic_scope
* source_references
* report_content
* generated_by
* review_status
* approved_by
* approved_at
* sent_to
* sent_at
* created_at
* updated_at



## F. DataQualityIssue



* issue_id
* source_reference
* indicator_id
* state_id
* district_id
* reporting_period
* issue_type
* description
* status
* assigned_to
* resolution_reference
* created_at
* updated_at



## G. AIAnalysisJob



* job_id
* job_type
* source_reference
* reporting_period
* status
* retry_count
* error_reference
* started_at
* completed_at
* created_at



## H. AIAnalysisAudit



* audit_id
* analysis_job_id
* model_or_method
* input_reference
* output_reference
* model_version
* analysis_timestamp
* review_status



Store references and minimum necessary information. Avoid duplicating sensitive clinical data into AI logs.



Add appropriate indexes, foreign keys, validation, access control, timestamps, and audit history.



Use transaction-safe processing and idempotency for background jobs.



---



# 12. BACKEND APIs



Inspect existing API conventions and reuse them.



Create or extend endpoints as necessary.



Suggested endpoints:



## Dashboard



GET /api/state-analyst/dashboard



Purpose:
Return authorized state-level health indicators, reporting coverage, trend summaries, alerts, and data synchronization status.



## Health Trends



GET /api/state-analyst/health-trends



Parameters:



* indicator_id
* district_id
* start_date
* end_date
* comparison_period



Return:



* Current values.
* Previous values.
* Calculated changes.
* Data sources.
* Reporting coverage.
* Validation status.



## District Analysis



GET /api/state-analyst/districts/{district_id}/analysis



Return authorized district-level aggregated indicators and analytical summaries.



Verify that the district belongs to the Analyst's authorized state.



## Public Health Alerts



GET /api/state-analyst/alerts



POST /api/state-analyst/alerts/{alert_id}/acknowledge



POST /api/state-analyst/alerts/{alert_id}/review



Require backend authorization and audit logging.



## AI Insights



GET /api/state-analyst/insights



POST /api/state-analyst/insights/{insight_id}/review



Use backend data services and existing AI infrastructure.



Do not trust frontend-supplied state_id, analyst_id, or access permissions.



## Reports



GET /api/state-analyst/reports



POST /api/state-analyst/reports/generate



POST /api/state-analyst/reports/{report_id}/approve



POST /api/state-analyst/reports/{report_id}/send



POST /api/state-analyst/reports/{report_id}/export



Require authorized approval and validate recipients.



## Data Quality



GET /api/state-analyst/data-quality



POST /api/state-analyst/data-quality/{issue_id}/request-verification



The Analyst may request verification but must not directly modify original PHC or district source records.



Use appropriate HTTP status codes, validation, pagination, filtering, rate limits, and error handling.



Do not expose internal stack traces or sensitive data in API errors.



---



# 13. SECURITY AND ACCESS CONTROL



Implement backend-enforced RBAC.



Role 11 can access only:



* The assigned state.
* Authorized district-level aggregate data within that state.
* Authorized health indicators.
* Approved supply-chain summaries.
* Authorized emergency impact summaries.
* Analytical insights and reports.



Enforce state-level tenant isolation.



Never trust frontend-supplied:



* analyst_id
* state_id
* district_id
* source_reference
* report_id



without backend authorization.



Prevent cross-state data access.



Do not allow unauthorized access to individual patient records, prescriptions, or identifiable clinical information.



Use minimum necessary data for analytics.



Implement:



* Secure authentication.
* Backend authorization on every protected endpoint.
* Input validation and output encoding.
* SQL injection and NoSQL injection prevention.
* Rate limiting.
* Secure session management.
* Encryption in transit and at rest.
* Secure secrets management.
* Audit logs.
* Appropriate retention and deletion policies.



AI services must receive only the minimum authorized data required for the specific analysis.



Prevent prompt injection through user input or untrusted source data.



Do not allow AI-generated content to execute database queries, access arbitrary records, or bypass authorization.



Audit:



* Report generation.
* Report approval.
* Report sharing.
* Alert review.
* Data verification requests.
* AI analysis jobs.
* Access to sensitive analytical datasets.



---



# 14. DATA QUALITY AND RESPONSIBLE AI



Treat source data as potentially incomplete, delayed, inconsistent, or incorrect.



For each analytical result, retain:



* Data source.
* Reporting period.
* Geographic scope.
* Reporting coverage.
* Validation status.
* Last updated time.
* Analysis method.
* Important limitations.



Do not:



* Invent missing values.
* Automatically treat missing reports as zero cases.
* Compare incompatible reporting periods.
* Claim causation from correlation.
* Produce unsupported confidence scores.
* Claim an outbreak based only on an unusual statistical change.
* Present AI-generated interpretations as confirmed medical facts.



If data is insufficient, state that the analysis is limited or unavailable.



AI recommendations must be explainable and reviewable.



Provide a human override and review workflow.



Ensure district comparisons account for reporting completeness, population differences, and indicator definitions.



---



# 15. UI/UX AND ACCESSIBILITY



Reuse the existing PWA design system.



The interface must be:



* Mobile-first.
* Responsive.
* Accessible.
* Suitable for state-level analytical work.
* Fast to understand.
* Consistent with the existing application.



Support:



* Tamil.
* English.
* Desktop.
* Tablet.
* Mobile.



Use accessible charts, clear legends, readable tables, meaningful labels, and non-colour-only status indicators.



Provide:



* Loading states.
* Empty states.
* Error states.
* Offline states.
* Stale-data indicators.
* Last synchronization timestamps.
* Confirmation dialogs for important actions.
* Clear report review and approval statuses.



Do not use fabricated dashboard metrics.



Do not use static charts as substitutes for actual database-driven analytics.



Charts and tables must use authorized live backend data.



Provide clear filters and sensible default reporting periods.



Avoid unnecessary animations and overly complex dashboards.



---



# 16. FAILURE HANDLING



Handle:



* Network failures.
* Backend/API failures.
* Database failures.
* Missing district reports.
* Duplicate aggregate submissions.
* Invalid indicator definitions.
* Stale data.
* Incomplete reporting periods.
* AI service failures.
* Background job failures.
* Notification failures.
* Failed report exports.
* Unauthorized data access.
* Interrupted report approval workflows.



Requirements:



* Use retries with appropriate limits.
* Use idempotent background jobs.
* Prevent duplicate alerts and reports.
* Preserve audit history.
* Show last successful synchronization time.
* Never display false success.
* Clearly distinguish unavailable data from zero values.
* Continue rule-based alerts if AI is unavailable.
* Provide retry or recovery options where appropriate.



---



# 17. TESTING AND ACCEPTANCE CRITERIA



Test the following.



## Functional Testing



* Role 11 can view the authorized state dashboard.
* District health summaries are retrieved correctly.
* Health trend calculations are correct.
* District comparisons use compatible reporting periods.
* Reporting completeness is calculated correctly.
* Supply summaries are integrated without duplicate counting.
* Emergency impact summaries are displayed correctly.
* Reports can be generated, reviewed, and approved.
* Only authorized reports can be sent.



## AI Testing



* AI identifies configured unusual patterns using available data.
* AI explanations reference the correct indicators and periods.
* AI does not invent health statistics.
* AI does not declare a confirmed outbreak.
* AI does not make clinical or administrative decisions.
* AI distinguishes incomplete data from zero values.
* AI identifies missing reporting coverage.
* AI outputs are reviewed before becoming official reports.
* AI failure does not disable core analytics or rule-based alerts.



## Security Testing



* Cross-state access is blocked.
* Unauthorized district access is blocked.
* Patient-level clinical access is denied.
* Unauthorized report approval is blocked.
* Unauthorized report sharing is blocked.
* API authorization cannot be bypassed through frontend changes.
* AI cannot bypass backend access controls.



## Integration Testing



* PHC reporting data reaches the authorized district reporting workflow.
* DHO summaries reach the state analytics pipeline.
* Supply data from Role 07 and Role 10 is consolidated correctly.
* Emergency summaries from Role 08 are available as authorized.
* Approved analytical reports reach Role 09.
* Authorized state reports can reach Role 12.



## UI and Performance Testing



* Mobile, tablet, and desktop layouts work correctly.
* Tamil and English display correctly.
* Charts handle missing data.
* Filters and pagination work.
* Dashboard performs acceptably with large aggregate datasets.
* Background analytics do not block normal application requests.



---



# 18. IMPLEMENTATION PRIORITY



## Phase 1 — Core Analytics



* State health dashboard.
* Authorized data integration.
* Health trend analysis.
* District analysis.
* Reporting coverage.
* Data quality indicators.



## Phase 2 — Reports and Coordination



* Analytical reports.
* Report review and approval.
* Role 09 reporting integration.
* Supply-chain trend integration.
* Emergency impact analysis.
* Notifications and audit logs.



## Phase 3 — Intelligent Analytics



* Automatic trend detection.
* Anomaly detection.
* Public health risk signals.
* Health and supply correlation.
* AI report drafting.
* AI assistant.
* Automated insight notifications.



## Phase 4 — Production Readiness



* Security hardening.
* Performance optimization.
* Background job reliability.
* Monitoring and alerting.
* Accessibility.
* Disaster recovery.
* Integration and end-to-end testing.



---



# 19. FINAL OBJECTIVE



Deliver a functional State Public Health Analyst module that transforms authorized, aggregated state and district health data into reliable analytical insights for public health decision support.



Core workflow:



PHC Data Entry
→ District Validation and Consolidation
→ Authorized State Data Pipeline
→ Automatic Health Analytics
→ Trend and Risk Insights
→ Analyst Review
→ Approved Analytical Report
→ State Health Administrator
→ Authorized Administrative Decision



Role boundaries:



* Role 02 — Doctor: Clinical care and clinical records.
* Role 03 — Nurse: Patient care and healthcare service records.
* Role 04 — PHC In-charge: PHC operations and reporting.
* Role 05 — Pharmacist: PHC inventory and medicine consumption.
* Role 06 — DHO: District health administration and reporting oversight.
* Role 07 — DSCO: District supply-chain operations.
* Role 08 — Emergency Coordinator: District emergency coordination.
* Role 09 — State Health Administrator: State-level health administration and decisions.
* Role 10 — State Supply Chain Manager: State-level supply operations.
* Role 11 — State Public Health Analyst: State-level health analytics, trends, and decision support.
* Role 12 — National Health Authority: Authorized national-level health oversight.
* Role 13 — Platform Administrator: Technical platform administration.



Implement functional frontend, backend APIs, database integration, data aggregation, analytics, RBAC, AI automation, validation, auditability, notifications, error handling, and responsive UI.



Do not break existing Patient, Doctor, Nurse, PHC, DHO, DSCO, Emergency Coordinator, State Health Administrator, or State Supply Chain functionality.



Do not implement other roles in this phase.



Before completion, provide a concise implementation summary covering:



1. Existing components reused.
2. New pages and workflows implemented.
3. Backend APIs and database changes.
4. AI and automatic monitoring implementation.
5. Security and access controls.
6. Tests executed and results.
7. Integrations that remain unavailable or require configuration.



Do not claim a feature is functional unless it has actually been implemented and tested.




# 14. ROLE 12 — National Health Authority / Central Administrator


**Role purpose (master summary):** National health and supply-chain oversight role covering cross-state monitoring, report review, national coordination, emergency/cross-state awareness, reporting, and national AI intelligence.


### Detailed requirements from the uploaded role specification


# ROLE 12: NATIONAL HEALTH AUTHORITY / CENTRAL ADMINISTRATOR



Build a complete, functional National Health Authority / Central Administrator module for the existing federated Smart Health & Supply Chain Resilience PWA.



IMPORTANT:
Before making changes, inspect the existing codebase, framework, database, APIs, authentication, authorization, routing, design system, and all existing role modules, especially State Health Administrator (09), State Supply Chain/Warehouse Manager (10), and State Public Health Analyst (11).



Reuse existing components, services, APIs, database models, authentication, authorization, design system, and integration patterns wherever possible.



Implement ONLY Role 12 in this phase. Do not implement other roles or replace existing role functionality.



Do not deliver a static mockup, hardcoded dashboard, or disconnected prototype. Implement functional frontend, backend APIs, database integration, authorization, validation, auditability, national reporting, AI decision support, coordination workflows, response tracking, and responsive UI.



If a required integration or data source does not exist, identify the gap and implement a clearly defined, secure integration boundary with an appropriate fallback. Never fabricate real national or state data.



---



# 1. ROLE AND PURPOSE



Role 12 is responsible for national-level health and supply-chain monitoring, authorized report review, cross-state situational awareness, national coordination, and tracking authorized responses.



The role receives authorized aggregated information from state-level roles, reviews national patterns, identifies significant issues, coordinates with authorized state officers, and prepares national-level reports.



Main responsibilities:



- Monitor aggregated health indicators across states.
- Monitor state-wise medicine availability and supply-chain performance.
- Identify critical shortages affecting multiple states.
- Review state health and supply-chain reports.
- Identify cross-state public health and supply-chain patterns.
- Review AI-generated insights and predictions.
- Request clarification or updated reports from state authorities.
- Initiate authorized national coordination requests.
- Track state responses and national action items.
- Prepare and review national health and supply-chain reports.
- Escalate matters to the configured authorized higher authority where applicable.



The role must not become responsible for:



- Individual patient clinical care.
- Doctor consultations or prescriptions.
- PHC-level pharmacy operations.
- District-level supply allocation.
- Direct state or district warehouse inventory modification.
- Autonomous cross-state medicine transfers.
- Platform administration or unrestricted user management.



Role 12 is a national operational oversight role, not automatically the highest government authority.



Any higher ministry-level authority must be represented only if explicitly included in the existing governance model. Do not invent a new mandatory role or claim an official reporting hierarchy without project configuration.



Role 13 remains the separate Platform Super Admin role. Platform administration does not grant national health decision-making authority.



---



# 2. NATIONAL ROLE HIERARCHY AND DATA FLOW



Implement the following authorized reporting structure:



PHC-level sources:
- Doctor (02)
- Nurse/Healthcare Staff (03)
- PHC In-charge (04)
- Pharmacist/PHC Storekeeper (05)



District-level sources:
- District Health Officer (06)
- District Supply Chain Officer (07)
- District Emergency Coordinator (08)



State-level reporting roles:
- State Health Administrator (09)
- State Supply Chain/Warehouse Manager (10)
- State Public Health Analyst (11)



National-level recipient:
- National Health Authority/Central Administrator (12)



Primary integration:



Role 09 → State health status, district summaries, healthcare service availability, administrative reports.



Role 10 → State warehouse summaries, medicine availability, shortages, demand, supply movements, state-level supply performance.



Role 11 → Aggregated public health trends, validated analysis, unusual patterns, data-quality findings, and health/supply-chain correlations.



Role 12 receives authorized national reporting data through backend APIs and the existing federated data architecture.



Do not require PHCs or district officers to manually submit duplicate reports directly to Role 12 when the information is already consolidated through existing modules.



Use existing state reporting workflows. Do not bypass state-level authorization or modify other roles' responsibilities.



The national integration layer must support:
- Source state and reporting authority.
- Source role and report reference.
- Reporting period.
- Submission and last-updated timestamps.
- Validation and review status.
- Data completeness and freshness.
- Authorized aggregation and access restrictions.
- Data provenance and audit history.



Use asynchronous processing or background jobs for large report aggregation where appropriate. Keep the MVP architecture consistent with the existing codebase.



---



# 3. NATIONAL DASHBOARD



Create a functional National Health and Supply Chain Dashboard.



Display authorized, verified, and appropriately aggregated information.



Dashboard sections:



A. National Health Overview
- Reporting states.
- State-wise health indicators.
- Aggregated healthcare service availability.
- Public health trends.
- District-level impacts summarized at state/national level.
- Data reporting completeness.



B. National Supply Chain Overview
- State-wise medicine availability.
- Critical medicine shortages.
- Stock-out patterns.
- State warehouse availability summaries.
- Supply-demand trends.
- Delayed supply movements.
- State escalation and coordination status.



C. Cross-State Monitoring
- States reporting critical issues.
- Similar health or supply-chain trends across states.
- Cross-state shortage patterns.
- Pending verification and clarification requests.
- Potential coordination opportunities based on verified data.



D. National Alerts
- Critical shortage alerts.
- Unusual public health trend alerts.
- Missing or delayed state reports.
- Data-quality issues.
- State response overdue.
- Cross-state coordination issues.
- AI-generated insights awaiting review.



E. National Action Tracking
- Open coordination requests.
- Pending state responses.
- Requests awaiting clarification.
- Authorized directives awaiting acknowledgement.
- Overdue action items.
- Recently resolved issues.



F. National AI Insights
- Shortage predictions.
- National demand forecasts.
- Cross-state trend analysis.
- Report quality insights.
- Coordination suggestions.
- AI-generated report summaries.



Every dashboard metric must have source, reporting period, last-updated timestamp, validation status, and relevant data-quality limitations.



Do not present stale or incomplete data as current or verified.



Dashboard navigation:



- National Dashboard
- State Reports
- Health Overview
- Supply Chain Overview
- Cross-State Monitoring
- National Alerts
- Coordination Requests
- State Responses
- National Reports
- AI Insights
- Audit History



Display only information the authenticated officer is authorized to access.



---



# 4. STATE REPORTS AND REVIEW



Role 12 can review authorized state-level reports submitted by Roles 09, 10, and 11.



Functions:
- View reports by state and reporting period.
- Search and filter reports.
- View report source and submission time.
- Review report completeness and validation status.
- Compare authorized indicators across states.
- Identify missing, delayed, inconsistent, or outdated reports.
- Request clarification or updated information.
- Track report review status.



Suggested report statuses:



Submitted
Under Review
Clarification Requested
Updated
Accepted
Rejected
Closed



A report must not be marked verified or accepted solely because an AI model processed it.



Role 12 or another authorized reviewer must make the final review decision.



When rejecting a report or requesting clarification, record the reason, responsible state role, timestamp, and audit event.



Do not silently modify the original state-submitted data. Corrections must be made through the authorized source workflow and preserve version history.



---



# 5. NATIONAL HEALTH MONITORING



Provide national-level health oversight using aggregated and authorized data.



Functions:
- Monitor state-wise health indicators.
- Review validated public health trends.
- Identify unusual patterns across states.
- Monitor healthcare service availability.
- Review aggregated district impacts reported through state channels.
- Compare reporting periods where valid baselines exist.
- Identify potential multi-state public health concerns.
- Request verification from the appropriate State Public Health Analyst or State Health Administrator.



The system must distinguish:



- Reported cases or visits.
- Validated analytical trends.
- Suspected patterns requiring investigation.
- Officially confirmed information, only when supported by authorized sources.



Do not automatically declare outbreaks, diagnose patients, or determine clinical severity.



Do not expose identifiable patient records or consultation details to Role 12 by default.



All national health analytics must use appropriate aggregation, data minimization, and privacy controls.



If data is insufficient, display that limitation instead of producing an unsupported conclusion.



---



# 6. NATIONAL SUPPLY-CHAIN OVERSIGHT



Role 12 monitors national and cross-state supply-chain conditions.



Functions:
- View state-level medicine availability summaries.
- Identify states reporting critical shortages.
- Monitor stock-out patterns across states.
- Review state-level demand and consumption trends.
- Monitor delayed or disrupted supply movements.
- Review supply-chain performance indicators.
- Identify potential cross-state coordination requirements.
- Request updated stock information or response plans from authorized State Supply Chain Managers.
- Track national supply-chain coordination issues.



Role 12 must not directly:
- Modify state warehouse inventory.
- Deduct stock from state warehouses.
- Allocate district-level inventory.
- Dispatch medicine shipments.
- Confirm PHC receipts.
- Create autonomous procurement orders.
- Override state or district stock transaction workflows.



All actual stock operations remain within the authorized existing State Supply Chain Manager, District Supply Chain Officer, and PHC Pharmacist workflows.



Cross-state redistribution suggestions must go through configured authorization, source-state approval, receiving-state approval, and existing inventory transaction processes.



Do not treat a suggested transfer as approved or completed.



---



# 7. NATIONAL COORDINATION AND ACTION MANAGEMENT



Implement a functional coordination workflow.



Role 12 can create:



- State clarification requests.
- Updated reporting requests.
- National supply-chain coordination requests.
- Cross-state coordination proposals.
- Authorized directives, if enabled by the configured governance model.
- Escalations to a configured higher authority, if applicable.



Each coordination request should include:



- Request ID.
- Title and description.
- Issue category.
- Affected state or states.
- Relevant report or alert references.
- Responsible target role.
- Priority and reason.
- Requested action.
- Created by.
- Created timestamp.
- Due date, where applicable.
- Attachments or evidence references, if supported.
- Current status.
- Response history.
- Audit history.



Possible statuses:



Draft
Submitted
Sent
Acknowledged
Under Review
Response Submitted
Response Accepted
Further Clarification Required
Escalated
Resolved
Closed
Cancelled



Workflow:



National issue detected
→ Role 12 reviews evidence
→ Role 12 creates a coordination request
→ Backend checks permissions and target authority
→ Request is delivered to the authorized state role
→ State reviews and responds through its own role module
→ Response is routed back to Role 12
→ Role 12 reviews the response
→ Accept, request clarification, escalate, or close
→ Record the complete audit trail.



Notifications should be delivered through existing notification services wherever available.



Do not create a disconnected second notification system.



A coordination request must not automatically authorize stock movement, procurement, emergency priority, or clinical decisions.



---



# 8. NATIONAL EMERGENCY AND CROSS-STATE COORDINATION



Role 12 can monitor aggregated emergency-related information received through authorized state reporting workflows.



Functions:
- View state-reported emergency impacts.
- Identify multiple states reporting related supply-chain disruptions.
- Review essential medicine shortages affecting emergency response.
- Request updated state supply availability.
- Coordinate authorized national-level information exchange.
- Track state response plans.
- Escalate unresolved national-level issues through configured governance.



Role 12 does not replace:
- District Emergency Coordinator (08).
- District Supply Chain Officer (07).
- State Supply Chain Manager (10).
- State Health Administrator (09).



Emergency priority must remain governed by authorized emergency workflows and human decisions.



AI may summarize the situation or recommend attention areas, but it must not autonomously assign emergency priority or issue official emergency declarations.



---



# 9. NATIONAL AI INTELLIGENCE SYSTEM



Create a national-level AI decision-support system named:



National Health & Supply Chain Intelligence Assistant.



AI should use authorized national and state-level aggregated data, existing reports, validated historical information, and configured data sources.



Do not use AI merely as a generic chatbot.



## A. National Shortage Detection



Identify medicines with reported or predicted shortages across states.



Analyze:
- Current verified state stock summaries.
- Historical consumption.
- Demand reports.
- Supply delays.
- State-level shortage indicators.
- Reporting completeness and data freshness.



Output:
- Medicine and affected states.
- Reported or predicted shortage status.
- Reporting period.
- Supporting data.
- Estimated shortage horizon, only when sufficient data exists.
- Confidence or uncertainty.
- Data limitations.
- Suggested review or coordination action.



Do not invent stock quantities or claim precise availability without verified data.



## B. Cross-State Health Trend Detection



Analyze authorized State Public Health Analyst reports to identify similar or unusual patterns across states.



Output:
- Observed pattern.
- Affected states.
- Reporting period.
- Data sources.
- Baseline used.
- Statistical or analytical limitations.
- Suggested verification or review.



Do not declare outbreaks or infer causation from correlations.



## C. National Demand Forecasting



Estimate future medicine demand from valid historical consumption, stock, and state-level demand data.



Support:
- Configurable forecast horizons.
- Seasonal or historical patterns when supported.
- Demand uncertainty.
- Model performance monitoring.
- Data sufficiency checks.



Output:
- Forecasted demand range.
- Forecast horizon.
- Input period.
- Model version.
- Confidence or prediction interval where technically justified.
- Known limitations.



If historical data is inadequate, show an unavailable or low-reliability result instead of fabricated predictions.



## D. Cross-State Coordination Suggestions



Identify possible coordination opportunities when verified state summaries indicate supply imbalance.



Output:
- Potential source and receiving states.
- Medicine.
- Verified available and required quantities, if accessible.
- Data freshness.
- Operational constraints.
- Suggested coordination steps.
- Required state approvals.



AI must not autonomously transfer inventory, reserve stock, approve allocation, or create dispatch transactions.



## E. Report Validation and Data Quality



Detect:
- Missing reporting fields.
- Duplicate reports.
- Conflicting quantities or reporting periods.
- Outdated data.
- Unusual values requiring review.
- Inconsistent aggregation.
- Missing state submissions.



AI can suggest clarification requests but must not silently alter source reports.



## F. National Report Assistant



Generate draft national reports using authorized source data.



Support:
- National health summaries.
- State-wise supply-chain summaries.
- Shortage reports.
- Emergency impact summaries.
- Cross-state trend reports.
- Pending response summaries.



Every generated report must include source references, reporting periods, generation timestamp, and limitations.



A human officer must review and approve reports before official publication or external distribution.



## G. Natural Language National Assistant



Allow Role 12 to ask questions such as:



- Which states have reported critical medicine shortages this month?
- Which state supply reports are overdue?
- What national supply-chain issues require review?
- Which states have unresolved coordination requests?
- Summarize verified health trends for the selected reporting period.
- Show the source and last update of this insight.



The assistant must answer only from authorized, available data and supported integrations.



Use retrieval or structured queries against permitted reports and analytics.



Do not expose data from unauthorized states, roles, or records.



If evidence is unavailable, clearly state that the system lacks sufficient data.



Prevent prompt injection and data leakage from report text, attachments, and untrusted inputs.



## AI SAFETY AND HUMAN OVERSIGHT



AI must never:
- Modify inventory.
- Approve or reject official state reports autonomously.
- Issue official directives autonomously.
- Dispatch medicine.
- Create procurement orders.
- Make clinical decisions.
- Declare outbreaks or emergencies.
- Determine official emergency priority.
- Modify state or district permissions.



Every AI recommendation must be reviewable and traceable.



Store appropriate AI interaction metadata, source references, model version, timestamps, and human review status.



Avoid storing unnecessary sensitive content.



AI failure must not block normal dashboard access, report review, coordination, or manual workflows.



Rule-based alerts and standard reporting must continue when AI services are unavailable.



---



# 10. NATIONAL REPORTS AND ANALYTICS



Provide functional report generation and filters.



Report types:
- National Health Overview.
- State-wise Health Indicators.
- National Medicine Availability.
- State Shortage Report.
- Cross-State Supply-Chain Report.
- Medicine Demand Forecast.
- Public Health Trend Report.
- Emergency Impact Report.
- State Reporting Completeness.
- National Coordination Status.
- Pending State Response Report.
- AI Insight Review Report.



Filters:
- State.
- Reporting period.
- Medicine/resource.
- Issue category.
- Report status.
- Validation status.
- Priority.
- Data freshness.



Support pagination, search, sorting, and export formats using existing project infrastructure.



Exports must respect backend authorization and data minimization.



Every report must identify its data sources, reporting period, generation time, and whether it is a draft or approved report.



---



# 11. DATABASE AND BACKEND



Inspect existing schemas and reuse appropriate models before creating new tables.



Avoid duplicating existing state reports, medicine records, inventory, users, or audit logs.



Where necessary, extend or introduce models for:



NationalReport
- report_id
- reporting_state_id
- reporting_role
- report_type
- reporting_period
- source_reference
- validation_status
- review_status
- submitted_at
- reviewed_by
- reviewed_at
- version



NationalCoordinationRequest
- request_id
- created_by
- target_role
- target_state_id
- issue_category
- priority
- requested_action
- source_references
- due_at
- status
- created_at
- updated_at



NationalCoordinationResponse
- response_id
- request_id
- responding_user
- response_summary
- evidence_reference
- status
- submitted_at
- reviewed_by
- reviewed_at



NationalAlert
- alert_id
- alert_type
- affected_state_ids
- source_reference
- priority
- data_period
- freshness_status
- status
- created_at
- acknowledged_by
- acknowledged_at



NationalAIInsight
- insight_id
- insight_type
- source_references
- affected_states
- reporting_period
- model_version
- output_summary
- confidence_or_uncertainty
- data_limitations
- review_status
- created_at
- reviewed_by
- reviewed_at



NationalAuditLog
- audit_id
- actor_id
- action
- resource_type
- resource_id
- previous_state_reference
- new_state_reference
- reason
- timestamp
- correlation_id



These are conceptual requirements, not mandatory duplicate tables. Map them to existing database models wherever possible.



Use:
- Foreign keys and appropriate indexes.
- Database transactions for critical workflows.
- Idempotency for coordination creation and state-changing APIs.
- Optimistic concurrency or locking where needed.
- Versioning for source reports and responses.
- Immutable or tamper-resistant audit history using existing infrastructure.



Do not store derived AI outputs as verified source facts.



---



# 12. API REQUIREMENTS



Reuse existing API conventions, versioning, authentication, and service architecture.



Provide or extend authorized endpoints for:



GET /api/national/dashboard
- National summary metrics and dashboard information.



GET /api/national/state-reports
- List authorized state reports with filters and pagination.



GET /api/national/state-reports/{reportId}
- Retrieve an authorized report and its source metadata.



POST /api/national/state-reports/{reportId}/review
- Accept, reject, or request clarification according to workflow permissions.



GET /api/national/health-overview
- Aggregated health indicators.



GET /api/national/supply-chain-overview
- State-level supply-chain summaries.



GET /api/national/alerts
- Retrieve national alerts.



POST /api/national/alerts/{alertId}/acknowledge
- Acknowledge an authorized alert.



POST /api/national/coordination-requests
- Create an authorized coordination request.



GET /api/national/coordination-requests
- List requests with filters.



GET /api/national/coordination-requests/{requestId}
- Retrieve request details and response history.



POST /api/national/coordination-requests/{requestId}/review
- Review a state response, request clarification, resolve, or close.



GET /api/national/reports
- List generated national reports.



POST /api/national/reports/generate
- Generate a report or enqueue a report-generation job.



POST /api/national/ai/insights
- Request authorized AI analysis.



POST /api/national/ai/assistant
- Ask questions against permitted national data.



All endpoints must include backend authentication, RBAC, state/data-scope validation, input validation, rate limiting where appropriate, and audit logging for sensitive operations.



These endpoint names are proposed contracts. Adapt them to the existing API structure rather than creating duplicate endpoints.



Return structured errors for unauthorized access, invalid requests, stale data, missing reports, conflicting state transitions, and service failures.



Never trust frontend-supplied role, state ID, source reference, or permissions.



---



# 13. SECURITY AND ACCESS CONTROL



Implement backend-enforced RBAC and national data-scope authorization.



Authorization must verify:



Authenticated user
→ Authorized Role 12 assignment
→ Active account and session
→ Permitted national scope
→ Requested state/report is authorized
→ Requested data is aggregated and permitted
→ Requested action is allowed for the role



Do not assume every Role 12 account automatically has unrestricted access to every state.



Support configurable access scopes where the existing governance model requires them.



Protect:
- State health reports.
- Aggregated public health indicators.
- Supply-chain summaries.
- Coordination requests and responses.
- AI insights and source references.
- Audit history.



Implement:
- Secure authentication and session handling.
- Least-privilege permissions.
- Server-side authorization.
- Input validation and output encoding.
- SQL/NoSQL injection prevention.
- CSRF protection where applicable.
- Rate limiting and abuse protection.
- Secure file and attachment handling.
- Encryption in transit and at rest using existing infrastructure.
- Secure secrets management.
- Audit logging for report access, sensitive exports, approvals, directives, and coordination actions.



Do not allow Role 12 to access individual patient data by default.



Do not grant Role 12 Platform Super Admin permissions.



Do not permit the frontend to bypass state-level workflow authorization.



---



# 14. UI/UX AND DESIGN SYSTEM



Reuse the existing project's design system, components, typography, spacing, colors, navigation, authentication screens, and dashboard patterns.



Do not create an unrelated visual design.



The module must be:
- Mobile-first.
- Responsive across mobile, tablet, and desktop.
- Simple for officers with different levels of technical knowledge.
- Operationally clear.
- Accessible.
- Suitable for long reporting and monitoring workflows.



## Navigation and layout



Use a responsive sidebar or drawer on larger screens and a compact navigation pattern on mobile.



Provide:
- National overview cards.
- State-wise report tables with responsive card alternatives.
- Search and filters.
- Clear state and reporting-period selectors.
- Alert and coordination status indicators.
- Report review panels.
- AI insight cards with evidence.
- Coordination request detail and response timeline.
- National analytics and charts only where they support decisions.



Avoid overwhelming the user with too many metrics on the first screen.



Prioritize:
1. Critical national issues.
2. Reports awaiting review.
3. Pending state responses.
4. Supply-chain coordination issues.
5. Health and supply-chain trends.
6. Historical analytics and AI insights.



## Human-centered design



For every workflow:
- Make the next action clear.
- Explain why an action is required.
- Show what will happen after submission.
- Confirm important actions before execution.
- Prevent accidental approvals or closures.
- Preserve user input when a recoverable error occurs.
- Show meaningful validation messages.
- Provide clear success and failure feedback.



Use clear labels and familiar terminology.



Do not rely on color alone for urgency, validation, or status.



Use text labels, icons, and accessible status indicators.



## Responsive behavior



Mobile:
- Single-column layouts.
- Compact metric cards.
- Drawer navigation.
- Readable tables converted into cards or horizontally scrollable sections when appropriate.
- Touch-friendly controls.
- Clear filters and action buttons.
- Avoid horizontal overflow.



Tablet:
- Adaptive grid and two-column layouts where useful.



Desktop:
- Full dashboard, side navigation, report tables, and detailed analytics.



## Language and accessibility



Support Tamil and English.



Use the existing localization framework if available. Do not hardcode translated strings throughout components.



Ensure:
- Keyboard navigation.
- Accessible labels.
- Screen-reader-friendly controls.
- Adequate contrast.
- Scalable text.
- Clear form errors.
- Accessible chart summaries and alternative descriptions.



Do not translate medicine names, identifiers, or official data values in a way that changes their meaning.



## Required UI states



Every data-driven screen must support:



- Loading and skeleton states.
- Empty states with helpful next steps.
- API/database error states.
- Unauthorized and forbidden states.
- Offline or disconnected states.
- Stale-data indicators with last synchronization time.
- Partial-data and incomplete-report warnings.
- Pending verification states.
- AI processing and AI-unavailable states.
- Successful submission and confirmation states.
- Conflict and duplicate-request states.



Never show false success when a backend action fails.



---



# 15. FAILURE HANDLING AND RESILIENCE



Handle:
- Network failure.
- API/database failure.
- State integration failure.
- Partial state reporting.
- Duplicate reports.
- Stale or conflicting data.
- Concurrent report reviews.
- Duplicate coordination requests.
- Failed notification delivery.
- Failed state response submission.
- AI timeout or unavailable service.
- Invalid or incomplete AI output.
- Interrupted report generation.
- Unauthorized access attempts.



Use safe retries and idempotency for critical actions.



Use background jobs for long-running aggregation, report generation, and AI processing where justified.



Show last successful synchronization time and data freshness.



Do not silently substitute fabricated or old data for current reports.



Do not mark a state response as received or accepted unless the backend confirms the operation.



AI failures must not block manual review, reporting, coordination, or state-response tracking.



Where data is unavailable, show the limitation and provide an appropriate retry or manual workflow.



---



# 16. PERFORMANCE AND SCALABILITY



Design for growth from a small pilot to national-level multi-state use without over-engineering the MVP.



Use:
- Server-side filtering and pagination.
- Indexed queries.
- Aggregated reporting tables or materialized views where justified.
- Caching for appropriate read-heavy national summaries.
- Background processing for expensive analytics.
- Queues only when required by existing architecture or workload.
- Efficient state-wise data retrieval.
- Optimized frontend assets and lazy loading.
- Appropriate database connection and transaction management.



Do not load all state reports or historical records into the browser.



Do not run expensive AI analysis on every dashboard request.



Cache only within authorization boundaries and invalidate data appropriately when new reports arrive.



---



# 17. TESTING AND ACCEPTANCE CRITERIA



Implement and run relevant tests using the existing testing framework.



Authorization:
- Role 12 can access only authorized national and state data.
- Unauthorized roles cannot access national endpoints.
- Role 12 cannot access individual patient records.
- Role 12 cannot modify state or district warehouse inventory.
- Role 12 cannot access Platform Super Admin functions.



Reporting:
- Authorized state reports appear correctly.
- Reporting periods and timestamps are accurate.
- Missing or stale data is clearly indicated.
- Conflicting reports are flagged.
- Source data is preserved.
- Report acceptance and clarification workflows are auditable.



Coordination:
- Coordination requests reach the correct authorized state role.
- State responses return to Role 12.
- Response status is tracked accurately.
- Unauthorized directives are blocked.
- Duplicate requests are prevented or handled idempotently.
- Closed requests retain their audit history.



AI:
- Insights use authorized source data.
- Source references and limitations are displayed.
- Insufficient data produces an appropriate warning.
- AI cannot autonomously issue directives or modify inventory.
- AI cannot access unauthorized states or patient records.
- AI failure does not break standard workflows.
- Predictions are evaluated against appropriate historical data before being presented as reliable.



UI/UX:
- Tamil and English work correctly.
- Mobile, tablet, and desktop layouts work.
- Loading, empty, error, stale, offline, and confirmation states are functional.
- Accessibility and keyboard navigation are tested.



Also implement appropriate unit, integration, API, authorization, UI, and end-to-end tests.



---



# 18. IMPLEMENTATION PRIORITY



Phase 1 — National Core:
- Existing authentication and Role 12 RBAC integration.
- National dashboard.
- Authorized state reports from Roles 09, 10, and 11.
- National health and supply-chain summaries.
- State reporting filters.
- Report review and data-quality indicators.



Phase 2 — Coordination:
- National alerts.
- Coordination requests.
- State clarification requests.
- State response tracking.
- National action history.
- Notifications using existing services.



Phase 3 — National Analytics:
- State comparisons.
- Cross-state trend summaries.
- National reports and exports.
- Reporting completeness analytics.
- Supply-chain performance analytics.



Phase 4 — National AI:
- AI national report assistant.
- Shortage detection.
- Report summarization.
- Data-quality insights.
- Demand forecasting when sufficient data exists.
- Cross-state coordination suggestions.
- AI evidence and review workflows.



Phase 5 — Production Readiness:
- Security hardening.
- Audit verification.
- Concurrency protection.
- Integration resilience.
- Accessibility testing.
- Performance optimization.
- Monitoring and operational documentation.



Implement in phases without breaking existing functionality. Complete the essential end-to-end workflow before adding advanced AI.



---



# 19. MONITORING AND OPERATIONS



Reuse existing logging, monitoring, and error-reporting infrastructure.



Track:
- API errors and latency.
- Database errors and query performance.
- State integration failures.
- Report-processing failures.
- Queue/job failures where applicable.
- AI service latency, errors, and usage.
- AI prediction quality when ground truth becomes available.
- Unauthorized access attempts.
- Coordination request and response activity.
- Report review and approval audit events.



Provide appropriate operational logs and health checks without exposing sensitive state or patient information.



Configure retention, backup, and recovery according to existing project policies and applicable organizational requirements.



---



# 20. FINAL ROLE SEPARATION



Maintain the following responsibilities:



Role 06 — District Health Officer:
District health administration and health-impact oversight.



Role 07 — District Supply Chain Officer:
District medicine supply requests, allocation, redistribution, dispatch, and state escalation.



Role 08 — District Emergency Coordinator:
District emergency coordination and emergency requirements.



Role 09 — State Health Administrator:
State health administration, oversight, and authorized reporting.



Role 10 — State Supply Chain/Warehouse Manager:
State warehouse inventory, state allocation, dispatch, and supply-chain operations.



Role 11 — State Public Health Analyst:
State-level health analytics, trend analysis, validation, and analytical reports.



Role 12 — National Health Authority/Central Administrator:
National health and supply-chain monitoring, report review, cross-state situational awareness, authorized coordination, and response tracking.



Role 13 — Platform Super Admin:
Platform technical administration, system configuration, and authorized platform access management.



Role 12 must not absorb or replace the operational responsibilities of Roles 06–11 or the technical administration of Role 13.



---



# FINAL OBJECTIVE



Deliver a functional, secure, responsive, and integrated National Health Authority module for the Smart Health & Supply Chain Resilience PWA.



The core workflow is:



STATE REPORTS (09, 10, 11)
→ AUTHORIZED NATIONAL DATA INTEGRATION
→ VALIDATION AND AGGREGATION
→ NATIONAL DASHBOARD
→ ROLE 12 REVIEW
→ NATIONAL AI INSIGHTS
→ HUMAN-APPROVED COORDINATION REQUEST
→ AUTHORIZED STATE RESPONSE
→ RESPONSE REVIEW
→ TRACKING AND CLOSURE
→ AUDITABLE NATIONAL REPORTING



The national AI system must transform authorized state-level information into useful national insights while preserving state authority, data privacy, human oversight, and operational accountability.



Before coding:
1. Inspect the existing codebase and report the relevant architecture and reusable modules.
2. Identify existing state reporting and API integration mechanisms.
3. Identify gaps and propose the smallest safe implementation plan.
4. Implement only Role 12.
5. Run relevant tests and report actual results.
6. Document changed files, APIs, database changes, integration assumptions, and any remaining limitations.



Do not rebuild existing modules.
Do not invent data.
Do not grant unrestricted national access by default.
Do not allow AI to make autonomous official or supply-chain decisions.
Do not deliver only a mockup.



Build the real Role 12 module by extending the existing application safely.




# 15. ROLE 13 — National Platform Administrator / Super Admin


**Role purpose (master summary):** Highest technical/platform authority responsible for platform security, availability, configuration, RBAC, organizational structure, audit, integrations, backup/recovery, AI platform management, and system operations; not the highest healthcare decision-maker.


### Detailed requirements from the uploaded role specification


# Role 13 — National Platform Administrator / Super Admin



## 1. Role & Purpose



The **National Platform Administrator / Super Admin** is the highest **technical and platform authority** of the Smart Health & Supply Chain Resilience system.



The Super Admin is responsible for ensuring that the entire platform is:



* Secure
* Available
* Properly configured
* Correctly permissioned
* Auditable
* Reliable
* Operational across all states, districts and PHCs



### Important Authority Boundary



The Super Admin has the highest **technical/platform authority**, but is **not the highest healthcare decision-maker**.



Healthcare and operational authority remains with the appropriate roles:



* National Health Authority → national healthcare administration
* State Health Administrator → state health administration
* DHO → district health administration
* DSCO → district supply-chain operations
* District Emergency Coordinator → emergency coordination
* PHC In-charge → PHC administration
* Doctor → clinical care
* Pharmacist → pharmacy operations



**Maximum platform authority does not mean unrestricted access to every healthcare function or patient record.**



---



# 2. Platform & Healthcare Hierarchy



The system maintains two related but separate authority structures.



### Healthcare / Administrative Hierarchy



**National Health Authority**
↓
**State Health Administration**
↓
**District Health Administration**
↓
**PHC Administration**
↓
**Clinical / Pharmacy Staff**
↓
**Patient**



### Technical / Platform Authority



**National Platform Administrator / Super Admin**



The Super Admin governs the **digital platform used by all these levels**.



---



# 3. Super Admin Dashboard



The Super Admin dashboard should provide system-wide platform visibility into:



* Overall platform health
* Active users
* Registered states, districts and PHCs
* User and role status
* System errors
* Security alerts
* API/integration status
* Database/system health
* Background jobs
* Notification services
* AI service status
* Audit activity
* Critical platform incidents
* Backup and recovery status



The dashboard should prioritize **system health and platform operations**, not routine clinical or supply-chain operations.



---



# 4. User & Role Management



Super Admin can:



* Create and manage platform accounts
* Activate/deactivate accounts
* Assign roles
* Manage role mappings
* Manage organization/facility assignments
* Suspend compromised or unauthorized accounts
* Support account recovery
* View user access history
* Manage platform-level RBAC configuration



### Important Permission Rule



**Role assignment must not automatically mean unrestricted permission creation.**



The architecture must follow:



**User → Role → Permission Policy → Backend Authorization**



The backend is the final authority for access control.



The frontend must never determine whether a user is authorized.



Users must not be able to:



* Assign roles to themselves
* Increase their own privileges
* Modify their own permissions
* Bypass backend authorization
* Access functions simply by manipulating frontend requests



### Critical Permission Changes



For high-risk permission changes:



* Step-up authentication should be required
* Explicit confirmation should be required
* The action must be audited
* Approval workflow can be required where appropriate



---



# 5. PHC & Organization Management



Super Admin can manage the platform's organizational structure:



* Register healthcare facilities/PHCs
* Activate/deactivate facilities
* Assign PHCs to districts
* Assign districts to states
* Maintain State → District → PHC hierarchy
* Manage organizational metadata
* Configure facility access



Organizational changes must be:



* Authorized
* Validated
* Audited
* Recoverable where appropriate



---



# 6. Platform Configuration



Super Admin can manage system-wide platform configuration such as:



* Platform settings
* Role and permission policies
* Notification configuration
* Workflow configuration
* System master data
* Security policies
* Feature/module availability
* System-wide operational settings



Critical configuration changes must use:



* Appropriate authorization
* Step-up authentication where required
* Confirmation
* Audit logging
* Approval workflow where appropriate



---



# 7. Security & Audit Management



Super Admin can access:



* Authentication logs
* Login/session activity
* Failed login attempts
* Suspicious access activity
* Permission violations
* Security alerts
* Audit logs
* System-wide access history
* Security incidents



Critical administrative actions must be audited.



Examples:



* Role changes
* Permission changes
* User activation/deactivation
* PHC creation/deactivation
* Configuration changes
* Security actions
* Critical system changes
* Temporary privileged-access grants
* Backup/recovery actions



Audit records should capture relevant information such as:



* Actor
* Action
* Target
* Timestamp
* Previous/new value where appropriate
* Session/device/IP information where appropriate
* Reason/context where required



---



# 8. Super Admin Security Boundary



Because compromise of a Super Admin account could affect the entire platform, the Super Admin itself must have strong security controls.



### Mandatory Controls



* Multi-factor authentication (MFA)
* Strong session management
* Shorter privileged-session expiry
* Automatic session timeout
* Step-up authentication for sensitive actions
* Explicit confirmation for critical changes
* Privileged-action audit logging
* Suspicious activity monitoring
* Secure recovery procedures



### Sensitive Actions



Examples:



* Changing critical permissions
* Changing Super Admin-level access
* Disabling security controls
* Modifying important system configuration
* Performing sensitive recovery operations



These actions should require stronger verification than normal platform usage.



---



# 9. Patient Data Access Boundary



Super Admin does **not** receive unrestricted access to individual patient records simply because the role has platform-level authority.



### Default Super Admin Access



Super Admin can normally access:



* Audit logs
* Security events
* Technical diagnostics
* Platform errors
* Access logs
* System performance information
* Integration status



### Individual Patient Records



Default:



**NO unrestricted patient-record access.**



If technical troubleshooting genuinely requires access:



**Limited → Authorized → Purpose-specific → Time-limited → Fully audited**



The system must record:



* Who accessed the data
* Why access was required
* What data was accessed
* When access occurred
* When access expired



Super Admin must not use technical authority to browse patient records unnecessarily.



---



# 10. System & Integration Management



Super Admin manages the technical operation of:



* APIs
* External integrations
* Data synchronization
* Notification services
* Background jobs
* Scheduled processes
* System error monitoring
* Service availability
* Integration health



The Super Admin can monitor and configure technical integrations but should not modify healthcare operational data outside authorized workflows.



---



# 11. Backup & Recovery Management



Super Admin can manage:



* Backup status
* Backup schedules/configuration
* Recovery configuration
* Restore operations
* Disaster-recovery status
* Recovery testing
* System restoration procedures



### Sensitive Backup Boundary



Backup and recovery must be separated from highly sensitive secrets.



Super Admin's normal privileges must **not automatically provide access to**:



* Backup encryption keys
* Production encryption keys
* Production secrets
* Root-level credentials
* Highly restricted secret-management systems



These must use:



* Separate restricted access
* Secure key/secret management
* Independent recovery procedures
* Strong authentication
* Appropriate audit controls



Therefore:



**Super Admin can manage recovery operations without automatically possessing every encryption key or production secret.**



---



# 12. AI Platform Management



Super Admin manages the **technical AI platform**, including:



* AI service availability
* AI model/service configuration
* AI usage monitoring
* AI error monitoring
* AI performance monitoring
* AI safety controls
* AI feature enable/disable controls



The Super Admin does **not** replace the professional role using the AI.



Examples:



* Doctor AI → clinical workflow support
* DHO AI → district health insights
* DSCO AI → supply-chain insights
* Emergency AI → emergency coordination insights



AI remains advisory and role-specific.



The Super Admin must not use AI administration to:



* Diagnose patients
* Prescribe medicines
* Make emergency clinical decisions
* Automatically approve supply operations
* Override professional decisions



---



# 13. System-Wide Monitoring



Super Admin should monitor:



* Platform downtime
* API failures
* Database failures
* Integration failures
* Authentication failures
* Notification failures
* Background-job failures
* High system load
* Security incidents
* AI service failures
* Backup/recovery failures



Critical failures should generate alerts and appropriate escalation.



---



# 14. Access Control — What Super Admin CAN Access



## 🟢 Platform Administration



* Entire platform configuration
* User management
* Role management
* Permission policies
* Organization hierarchy
* PHC registration/configuration
* System settings
* Platform monitoring



## 🟢 Security



* Security alerts
* Authentication activity
* Audit logs
* Access violations
* Security incidents
* Privileged activity monitoring



## 🟢 Technical Operations



* API/integration status
* Background jobs
* Notifications
* System health
* Error monitoring
* Backup/recovery operations



## 🟢 AI Platform



* AI service configuration
* AI service health
* AI monitoring
* AI safety controls



---



# 15. Access Control — What Super Admin SHOULD NOT Directly Manage



### 🔴 Clinical Operations



* Diagnose patients
* Prescribe medicines
* Modify consultations
* Make clinical decisions
* Override clinical decisions



### 🔴 Individual Patient Care



* Change treatment
* Decide patient priority
* Modify patient care decisions



### 🔴 PHC Pharmacy Operations



* Dispense medicines
* Perform routine pharmacy transactions
* Directly manage daily PHC stock



### 🔴 District Supply Chain



* Approve routine district supply requests
* Perform district redistribution
* Operate district warehouse workflows



### 🔴 State Supply Chain



* Directly modify state warehouse inventory
* Perform state-level supply allocation



### 🔴 Emergency Operations



* Make clinical emergency decisions
* Replace the District Emergency Coordinator
* Manage individual emergency treatment



### 🔴 Routine Staff Operations



* Mark doctor/nurse attendance
* Manage routine staff workflows
* Replace PHC administrative responsibilities



### 🔴 Unrestricted Patient Data Access



* Browse patient records without purpose
* Access all medical records by default
* Use technical privileges to bypass healthcare data boundaries



---



# 16. Conditional / Exceptional Access



Some technical situations may require temporary access beyond normal Super Admin visibility.



Examples:



* Investigating a serious system error
* Investigating a security incident
* Troubleshooting a data-access problem
* Performing controlled recovery



In such cases:



**Authorization → Purpose → Limited scope → Time limit → Audit**



must be enforced.



Exceptional access must never become permanent unrestricted access.



---



# 17. Connections With Other Roles



Super Admin connects with all roles primarily through **platform administration and technical support**.



### National Health Authority



* National platform governance support
* National organizational configuration
* System-level reporting
* Critical platform incidents



### State Health Administrator



* State organization management
* User/role administration
* Platform configuration
* Technical support



### DHO



* District/PHC organizational access
* Role/account management
* Platform support



### DSCO



* Supply-chain module access
* Role/permission management
* Technical support



### District Emergency Coordinator



* Emergency module availability
* Access management
* Critical system support



### PHC In-charge



* PHC registration/configuration
* Facility access
* User management support



### Doctor / Nurse / Pharmacist



* Account management
* Role
* Permissions
* Authentication
* Technical support



### Patient



* Account/access support
* Authentication
* Platform-related issues



The Super Admin does **not take over these roles' operational responsibilities**.



---



# 18. Database / Backend



Important entities include:



* User
* Role
* Permission
* PermissionPolicy
* Organization
* State
* District
* PHC
* UserOrganizationMapping
* AuditLog
* SecurityEvent
* PrivilegedAccessRequest
* SystemConfiguration
* Integration
* NotificationConfiguration
* AIServiceConfiguration
* SystemIncident
* BackupConfiguration
* RecoveryOperation



Sensitive credentials and encryption keys should **not** be stored as ordinary application data.



They should be handled through appropriate restricted secret/key-management mechanisms.



---



# 19. Backend Authorization



All privileged operations must be validated server-side.



The backend must verify:



* User identity
* Authentication status
* Assigned role
* Permission policy
* Organization scope
* Action scope
* Resource scope
* Privileged-action requirements



Never trust frontend values such as:



* `isSuperAdmin`
* `role=admin`
* `userId`
* `organizationId`
* `permission=true`



A user must never be able to escalate privileges by modifying requests.



---



# 20. Failure Handling



The platform must safely handle:



* Database failure
* API failure
* Authentication failure
* Integration failure
* Notification failure
* Background-job failure
* Configuration errors
* Permission conflicts
* Duplicate administrative actions
* Service downtime
* Backup failure
* Recovery failure
* Security incidents
* AI service failure



Never show a false success message.



Critical configuration and permission changes should be transactional and recoverable.



If a privileged operation fails, the system must clearly show:



**What happened → What changed → What did not change → What action is required next**



---



# 21. Testing & Acceptance Criteria



The Super Admin module must test:



### Authentication



* MFA enforcement
* Session expiry
* Step-up authentication
* Account recovery



### Authorization



* Correct role assignment
* Backend permission enforcement
* No self-privilege escalation
* No unauthorized privilege changes
* Organization-scope enforcement



### Security



* Audit logging
* Suspicious activity detection
* Sensitive-action confirmation
* Privileged-access controls



### Patient Privacy



* No default unrestricted patient access
* Limited technical access
* Time-limited access
* Complete audit trail



### Backup & Recovery



* Backup monitoring
* Restore operations
* Recovery failure handling
* Restricted key/secret access



### Platform



* PHC hierarchy management
* Configuration management
* Integration monitoring
* System incident handling



### AI



* AI service configuration
* AI monitoring
* AI safety controls
* No autonomous healthcare decisions



---



# 22. Implementation Priority



### Phase 1 — Core Platform Administration



* Authentication
* MFA
* Super Admin dashboard
* User management
* Role/RBAC management
* PHC/organization hierarchy
* Audit logs



### Phase 2 — Secure Platform Operations



* Permission policies
* Step-up authentication
* Privileged-action controls
* Security monitoring
* Configuration management
* Integration management
* System monitoring



### Phase 3 — Advanced Administration



* Conditional technical patient-data access
* Approval workflows for critical permissions
* Advanced security monitoring
* AI service management
* Backup/recovery management



### Phase 4 — Production Readiness



* High availability
* Disaster recovery
* Restricted secret/key management
* Strong privileged-access controls
* Comprehensive audit
* Performance monitoring
* Security testing
* Scalability



---



# 23. Final Role Boundary



The **National Platform Administrator / Super Admin** is responsible for:



**Users → Roles → Permissions → Organizations → Configuration → Security → Integrations → AI Platform → Backup/Recovery → System Health → Audit → Platform Reliability**



The Super Admin has **maximum technical authority**, but:



> **Technical authority does not equal unrestricted healthcare authority.**



The platform must enforce:



**Maximum Platform Control + Least-Privilege Data Access + Strong Privileged Security + Complete Auditability**



The final objective is to ensure that the entire Smart Health & Supply Chain Resilience platform remains **secure, reliable, available, properly governed, auditable and technically operational**, while preserving the independent responsibilities of healthcare and operational roles.



# 16. SOURCE COVERAGE AND CONSOLIDATION NOTES

## 16.1 Uploaded Source Coverage

This master specification was built from all 13 uploaded role documents, in this order:

1. Patient Module
2. Doctor / Medical Officer
3. Nurse / Healthcare Staff
4. PHC In-charge / Facility Manager
5. Pharmacist / PHC Storekeeper
6. District Health Officer (DHO)
7. District Supply Chain Officer
8. District Emergency Coordinator
9. State Health Administrator
10. State Supply Chain / Warehouse Manager
11. State Public Health Analyst
12. National Health Authority / Central Administrator
13. National Platform Administrator / Super Admin

## 16.2 Consolidation Rule

- Exact substantive blocks repeated across multiple role documents are moved to the consolidated cross-role section and removed from the repeated role copies.
- Role-specific details, workflows, permissions, restrictions, fields, statuses, AI behavior, API/database requirements, UI requirements, testing criteria, and acceptance criteria remain under their corresponding role.
- Similar-looking requirements with different wording or role-specific context are preserved rather than silently merged when merging them could remove a constraint.
- The result is intended to be the single working reference for implementation while keeping the original role-specific requirements traceable by role.