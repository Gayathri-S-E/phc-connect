# ROLE_API_MATRIX.md — Complete Backend API ↔ 13-Role Authorization Matrix
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Base URL:** `/api/v1`  
> **Security Protocol:** Bearer JWT in `Authorization` header (`Bearer <access_token>`)  
> **Enforcement Principle:** Authorization is 100% server-side database-driven via `Depends(require_permission(...))` and `resolve_jurisdiction(...)`.

---

## 1. Authentication & Session Module (`/api/v1/auth`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---:|:---|
| `/auth/register` | `POST` | Public | All (Anonymous) | None | Citizen self-registration |
| `/auth/login` | `POST` | Public | All 13 Roles | None | Authenticate with credentials; returns JWT pair |
| `/auth/refresh` | `POST` | Public (Refresh Token) | All 13 Roles | None | Rotate refresh token and issue new access token |
| `/auth/logout` | `POST` | Authenticated | All 13 Roles | User ID | Revoke active session |
| `/auth/me` | `GET` | Authenticated | All 13 Roles | User ID | Retrieve user profile, active scopes, and permissions |
| `/auth/change-password` | `POST` | Authenticated | All 13 Roles | User ID | Rotate password with current password verification |

---

## 2. Patient Healthcare Portal (`/api/v1/patient-portal`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---:|:---|
| `/patient-portal/profile` | `GET` | `patients.profile.read` | PATIENT | `SELF` | Retrieve personal demographic profile |
| `/patient-portal/profile` | `PATCH` | `patients.profile.update` | PATIENT | `SELF` | Update personal contact details |
| `/patient-portal/appointments` | `GET` | `appointments.view` | PATIENT | `SELF` | View personal upcoming/past appointments |
| `/patient-portal/appointments/book` | `POST` | `patients.awareness.read` | PATIENT | `SELF` | Book clinic appointment and allocate token |
| `/patient-portal/clinical-records` | `GET` | `patients.records.read` | PATIENT | `SELF` | View personal medical history, vitals, diagnoses |
| `/patient-portal/prescriptions` | `GET` | `prescriptions.read` | PATIENT | `SELF` | View issued prescriptions & dispensing status |
| `/patient-portal/feedback` | `POST` | `patients.feedback.submit` | PATIENT | `SELF` | Submit facility rating and grievance |
| `/patient-portal/wellness-assistant/chat` | `POST` | `patients.ai.wellness.chat` | PATIENT | `SELF` | AI Wellness Assistant conversation (EN/TA) |
| `/patient-portal/awareness` | `GET` | `patients.awareness.read` | PATIENT | `SELF` | Public health bulletins |
| `/patient-portal/notifications` | `GET` | `patients.notifications.read` | PATIENT | `SELF` | Real-time health alerts |

---

## 3. Doctor Clinical Portal (`/api/v1/doctor-portal`, `/consultations`, `/prescriptions`, `/labs`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---:|:---|
| `/doctor-portal/queue` | `GET` | `appointments.view` | DOCTOR | `FACILITY` | View OPD consultation queue |
| `/patients/{id}/clinical-history` | `GET` | `patients.records.read` | DOCTOR | `FACILITY` | Full clinical history of queued patient |
| `/consultations` | `POST` | `consultations.conduct` | DOCTOR | `FACILITY` | Initiate clinical consultation |
| `/consultations/{id}/finalize` | `PATCH` | `consultations.conduct` | DOCTOR | `FACILITY` | Conclude consultation, finalize ICD-10 diagnosis |
| `/prescriptions` | `POST` | `prescriptions.create` | DOCTOR | `FACILITY` | Author multi-item electronic prescription |
| `/labs/orders` | `POST` | `labs.order.create` | DOCTOR | `FACILITY` | Order diagnostic lab panels |
| `/labs/orders` | `GET` | `labs.order.read` | DOCTOR | `FACILITY` | View lab orders and test status |
| `/doctor-portal/referrals` | `POST` | `referrals.create` | DOCTOR | `FACILITY` | Dispatch patient referral |
| `/doctor-portal/attendance/today` | `GET` | `staff.attendance.read` | DOCTOR | `FACILITY` | Check today's shift attendance |
| `/doctor-portal/attendance/check-in` | `POST` | `staff.attendance.record` | DOCTOR | `FACILITY` | Record shift check-in |
| `/doctor-portal/attendance/check-out` | `POST` | `staff.attendance.record` | DOCTOR | `FACILITY` | Record shift check-out |
| `/doctor-portal/clinical-assistant/advise` | `POST` | `clinical.ai.advisory` | DOCTOR | `FACILITY` | AI Clinical advisory for drug interactions |
| `/doctor-portal/emergency-reports` | `POST` | `emergency.incident.report` | DOCTOR, PHC_IN_CHARGE | `FACILITY` | Report critical emergency incident to DEC |

---

## 4. Nurse Clinical Operations Portal (`/api/v1/nurse-portal`, `/patients`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---:|:---|
| `/nurse-portal/queue` | `GET` | `appointments.view` | NURSE | `FACILITY` | View triage queue and arriving patients |
| `/patients` | `POST` | `patients.profile.create` | NURSE | `FACILITY` | Register new walk-in patient |
| `/nurse-portal/vitals` | `POST` | `patients.vitals.record` | NURSE | `FACILITY` | Record vital signs & compute EWS |
| `/nurse-portal/triage-assistant/score` | `POST` | `clinical.ai.advisory` | NURSE | `FACILITY` | Compute triage score recommendation |
| `/nurse-portal/samples` | `GET` | `labs.order.read` | NURSE | `FACILITY` | View pending lab specimen collections |
| `/nurse-portal/samples/{id}/collect` | `POST` | `labs.sample.collect` | NURSE | `FACILITY` | Mark lab sample collected |
| `/nurse-portal/cold-chain` | `GET` | `cold_chain.read` | NURSE, PHC_IN_CHARGE | `FACILITY` | View cold chain assets & logs |
| `/nurse-portal/cold-chain/log` | `POST` | `cold_chain.log` | NURSE, PHC_IN_CHARGE | `FACILITY` | Log refrigerator temperature |
| `/appointments/{id}/status` | `PATCH` | `appointments.manage` | NURSE | `FACILITY` | Check in arriving patient / update roster |
| `/nurse-portal/attendance/check-in` | `POST` | `staff.attendance.record` | NURSE | `FACILITY` | Shift check-in |
| `/nurse-portal/attendance/check-out` | `POST` | `staff.attendance.record` | NURSE | `FACILITY` | Shift check-out |

---

## 5. Facility Administration Portal (`/api/v1/facility-admin`, `/dashboards/phc`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---:|:---|
| `/dashboards/phc` | `GET` | `facility.report.view` | PHC_IN_CHARGE | `FACILITY` | Operational overview KPIs |
| `/facility-admin/staff-attendance` | `GET` | `staff.attendance.admin` | PHC_IN_CHARGE | `FACILITY` | Staff attendance matrix by date range |
| `/facility-admin/cold-chain/equipment` | `GET` | `cold_chain.manage` | PHC_IN_CHARGE | `FACILITY` | List registered cold chain equipment |
| `/facility-admin/cold-chain/equipment` | `POST` | `cold_chain.manage` | PHC_IN_CHARGE | `FACILITY` | Register new ILR/refrigerator |
| `/facility-admin/outreach-camps` | `GET` | `outreach.camp.manage` | PHC_IN_CHARGE | `FACILITY` | View village outreach camps |
| `/facility-admin/outreach-camps` | `POST` | `outreach.camp.manage` | PHC_IN_CHARGE | `FACILITY` | Schedule new outreach camp |
| `/facility-admin/outreach-camps/{id}` | `PATCH` | `outreach.camp.manage` | PHC_IN_CHARGE | `FACILITY` | Update camp logistics and attendees |
| `/facility-admin/complaints` | `GET` | `facility.complaint.manage` | PHC_IN_CHARGE | `FACILITY` | View patient grievances |
| `/facility-admin/complaints/{id}/status` | `PATCH` | `facility.complaint.manage` | PHC_IN_CHARGE | `FACILITY` | Update grievance status & resolution notes |
| `/facility-admin/reports/monthly` | `GET` | `facility.report.view` | PHC_IN_CHARGE | `FACILITY` | Generate aggregate monthly HMIS report |

---

## 6. Pharmacy & Storekeeper Portal (`/api/v1/pharmacist-portal`, `/inventory`, `/prescriptions`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/pharmacist-portal/queue` | `GET` | `prescriptions.read` | PHARMACIST | `FACILITY` | Prescriptions pending dispensing |
| `/prescriptions/{id}/dispense` | `POST` | `prescriptions.dispense` | PHARMACIST | `FACILITY` | Dispense prescription via atomic FEFO deduction |
| `/inventory` | `GET` | `inventory.item.read` | PHARMACIST, DSCO, STATE_SUPPLY | `FACILITY` / `DISTRICT` / `STATE` | Real-time facility inventory balances |
| `/inventory/batches/expiring` | `GET` | `inventory.item.read` | PHARMACIST | `FACILITY` | Batches expiring within 30/60/90 days |
| `/inventory/adjustments` | `POST` | `inventory.stock.adjust` | PHARMACIST, STATE_SUPPLY | `FACILITY` / `STATE` | Physical count reconciliation / loss write-off |
| `/supply-requests` | `POST` | `supply.request.create` | PHARMACIST | `FACILITY` | Raise replenishment supply request to district |
| `/supply-requests` | `GET` | `supply.request.read` | PHARMACIST, DSCO, STATE_SUPPLY | `FACILITY` / `DISTRICT` / `STATE` | Query facility/district supply requests |
| `/supply-requests/{id}/receipts/{transfer_id}/verify` | `POST` | `supply.receipt.verify` | PHARMACIST | `FACILITY` | Verify physical receipt of incoming transfer |
| `/pharmacist-portal/attendance/check-in` | `POST` | `staff.attendance.record` | PHARMACIST | `FACILITY` | Pharmacist shift check-in |

---

## 7. District Governance & Oversight (`/api/v1/district`, `/governance`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/district/dashboard` | `GET` | `governance.district.view` | DISTRICT_HEALTH_OFFICER | `DISTRICT` | District aggregate healthcare overview |
| `/district/facilities/{facility_id}` | `GET` | `governance.district.view` | DISTRICT_HEALTH_OFFICER | `DISTRICT` | PHC performance trend comparison |
| `/district/analytics` | `GET` | `governance.district.view` | DISTRICT_HEALTH_OFFICER | `DISTRICT` | District health trend analytics |
| `/governance/actions` | `GET` | `governance.action.create` | DHO, DEC, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | View administrative directives |
| `/governance/actions` | `POST` | `governance.action.create` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | Issue binding administrative directive |
| `/governance/actions/{id}/transition` | `PATCH` | `governance.action.manage` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | Update directive lifecycle state |
| `/governance/alerts` | `GET` | `governance.alert.read` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | View health alerts & outbreak notices |
| `/governance/alerts/{id}/transition` | `POST` | `governance.alert.manage` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | Acknowledge/resolve health alert |
| `/governance/schemes` | `GET` | `governance.scheme.read` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | Monitor national/state health schemes |
| `/supply-requests/health-impacts` | `GET` | `supply.impact.read` | DISTRICT_HEALTH_OFFICER | `DISTRICT` | Review medicine shortage impact assessments |
| `/governance/reports/generate` | `POST` | `governance.report.generate` | DHO, STATE_ADMIN, NHA | `DISTRICT` / `STATE` / `GLOBAL` | Generate formal governance report |
| `/governance/ai-assistant` | `POST` | `governance.ai.assist` | DHO, DSCO, DEC, STATE_ADMIN, STATE_SUPPLY, ANALYST, NHA | Contextual Scope | Grounded role-specific AI governance briefing |

---

## 8. District Supply Chain Resilience (`/api/v1/supply-requests`, `/inventory/transfers`, `/ai`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/supply-requests/{id}/decision` | `POST` | `supply.request.review` | DISTRICT_SUPPLY_OFFICER | `DISTRICT` | Approve, reject, or defer PHC supply request |
| `/supply-requests/{id}/allocate` | `POST` | `supply.allocation.manage` | DSCO, STATE_SUPPLY_MANAGER | `DISTRICT` / `STATE` | Allocate transfer shipment from warehouse |
| `/inventory/transfers` | `GET` | `inventory.item.read` | DSCO, PHARMACIST, STATE_SUPPLY | `DISTRICT` / `FACILITY` / `STATE` | View inter-facility transfer requests |
| `/inventory/transfers` | `POST` | `inventory.transfer.request` | DSCO, PHARMACIST | `DISTRICT` / `FACILITY` | Initiate inter-facility transfer |
| `/inventory/transfers/{id}/approve` | `POST` | `inventory.transfer.approve` | DISTRICT_SUPPLY_OFFICER | `DISTRICT` | Authorize inter-facility stock transfer |
| `/inventory/transfers/{id}/dispatch` | `POST` | `inventory.transfer.dispatch` | DSCO, STATE_SUPPLY_MANAGER | `DISTRICT` / `STATE` | Dispatch stock transfer consignment |
| `/supply-requests/{id}/escalate` | `POST` | `shortages.incident.escalate` | DISTRICT_SUPPLY_OFFICER | `DISTRICT` | Escalate district stockout to State Warehouse |
| `/supply-requests/{id}/health-impact` | `POST` | `supply.impact.share` | DISTRICT_SUPPLY_OFFICER | `DISTRICT` | Share drug shortage impact assessment with DHO |
| `/ai/forecast` | `POST` | `ai.forecast.view` | DSCO, STATE_SUPPLY_MANAGER | `DISTRICT` / `STATE` | 30/60/90-day predictive demand curves |
| `/ai/risk-analysis` | `POST` | `ai.risk.analyze` | DSCO, STATE_SUPPLY_MANAGER | `DISTRICT` / `STATE` | Facility stockout vulnerability score |

---

## 9. District Emergency Coordination (`/api/v1/emergencies`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/emergencies/dashboard` | `GET` | `emergency.incident.read` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Live emergency command overview |
| `/emergencies` | `GET` | `emergency.incident.read` | DEC, DHO, STATE_ADMIN | `DISTRICT` / `STATE` | List district emergency incidents |
| `/emergencies` | `POST` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Formally declare new emergency incident |
| `/emergencies/{id}` | `GET` | `emergency.incident.read` | DEC, DHO, STATE_ADMIN | `DISTRICT` / `STATE` | Incident details, tasks, affected sites |
| `/emergencies/{id}/status` | `PATCH` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Transition lifecycle (ACTIVE, CONTAINED) |
| `/emergencies/{id}/priority` | `PATCH` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Update emergency severity |
| `/emergencies/{id}/facilities` | `PUT` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Attach affected PHCs and relief posts |
| `/emergencies/{id}/tasks` | `POST` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Assign emergency response task |
| `/emergencies/{id}/tasks/{task_id}` | `PATCH` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Update emergency task progress |
| `/emergencies/{id}/resources` | `POST` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Rapid emergency resource requisition |
| `/emergencies/{id}/escalate` | `POST` | `emergency.incident.manage` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Escalate incident to State Disaster Cell |
| `/emergencies/{id}/resolve` | `POST` | `emergency.incident.resolve` | DISTRICT_EMERGENCY_COORDINATOR | `DISTRICT` | Formally resolve emergency incident |

---

## 10. State Health Administration (`/api/v1/state`, `/governance`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/state/dashboard` | `GET` | `governance.state.view` | STATE_HEALTH_ADMIN | `STATE` | Statewide health overview & district ranks |
| `/state/analytics` | `GET` | `governance.state.view` | STATE_HEALTH_ADMIN | `STATE` | State epidemiological trend curves |
| `/governance/approvals` | `GET` | `governance.approval.decide` | STATE_HEALTH_ADMIN | `STATE` | Pending executive approvals inbox |
| `/governance/approvals/{id}/decision` | `POST` | `governance.approval.decide` | STATE_HEALTH_ADMIN | `STATE` | Formally approve or reject executive request |
| `/governance/schemes` | `POST` | `governance.scheme.manage` | STATE_HEALTH_ADMIN | `STATE` | Create new state health scheme |
| `/governance/schemes/{id}/targets` | `POST` | `governance.scheme.manage` | STATE_HEALTH_ADMIN | `STATE` | Configure district target quotas |
| `/governance/reports` | `GET` | `governance.report.review` | STATE_HEALTH_ADMIN, NHA | `STATE` / `GLOBAL` | View submitted governance reports |
| `/governance/reports/{id}/review` | `POST` | `governance.report.review` | STATE_HEALTH_ADMIN, NHA | `STATE` / `GLOBAL` | Sign off and endorse monthly report |

---

## 11. State Supply Chain & Warehousing (`/api/v1/supply-requests/state`, `/procurement`, `/shipments`, `/suppliers`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/supply-requests/state/dashboard` | `GET` | `dashboards.supply.view` | STATE_SUPPLY_MANAGER | `STATE` | State Central Warehouse dashboard |
| `/supply-requests/state/overview` | `GET` | `dashboards.supply.view` | STATE_SUPPLY_MANAGER | `STATE` | Escalated district requests summary |
| `/procurement/orders` | `GET` | `procurement.order.read` | STATE_SUPPLY_MANAGER | `STATE` | List commercial Purchase Orders |
| `/procurement/orders` | `POST` | `procurement.order.create` | STATE_SUPPLY_MANAGER | `STATE` | Issue bulk PO to pharma vendor |
| `/procurement/orders/{id}/approve` | `POST` | `procurement.order.approve` | STATE_HEALTH_ADMIN, SUPER_ADMIN | `STATE` / `GLOBAL` | Executive PO sign-off (SoD enforced) |
| `/suppliers` | `GET` | `suppliers.manage` | STATE_SUPPLY_MANAGER | `STATE` | List registered pharma suppliers |
| `/suppliers` | `POST` | `suppliers.manage` | STATE_SUPPLY_MANAGER | `STATE` | Onboard new approved supplier |
| `/shipments` | `GET` | `shipments.read` | STATE_SUPPLY_MANAGER, DSCO | `STATE` / `DISTRICT` | Track active logistics shipments |
| `/shipments` | `POST` | `shipments.create` | STATE_SUPPLY_MANAGER | `STATE` | Create transit shipment manifest |
| `/shipments/{id}/events` | `POST` | `shipments.update` | STATE_SUPPLY_MANAGER | `STATE` | Log shipment checkpoint & cold chain temp |
| `/shortages/{id}/resolve` | `POST` | `shortages.incident.resolve` | STATE_SUPPLY_MANAGER, DSCO | `STATE` / `DISTRICT` | Link fulfillment shipment and close shortage |

---

## 12. State Public Health Analytics (`/api/v1/public-health`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/public-health/dashboard` | `GET` | `analytics.indicator.read` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Epidemiological surveillance dashboard |
| `/public-health/indicators` | `GET` | `analytics.indicator.read` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | List canonical health indicators |
| `/public-health/indicators` | `POST` | `analytics.indicator.manage` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Register new health indicator definition |
| `/public-health/aggregates` | `GET` | `analytics.indicator.read` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | View district monthly aggregates |
| `/public-health/aggregates` | `POST` | `analytics.aggregate.submit` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Submit verified epidemiological aggregates |
| `/public-health/aggregates/validate` | `POST` | `analytics.data_quality.manage` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Run statistical validation on aggregates |
| `/public-health/trends` | `GET` | `analytics.indicator.read` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Longitudinal disease trend queries |
| `/public-health/analysis/run` | `POST` | `analytics.insight.review` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Launch statistical modeling job |
| `/public-health/analysis/jobs/{job_id}` | `GET` | `analytics.insight.review` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Inspect analysis job output |
| `/public-health/data-quality` | `GET` | `analytics.data_quality.manage` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Data quality audit issue ledger |
| `/public-health/data-quality/{issue_id}/action` | `POST` | `analytics.data_quality.manage` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Issue data quality clarification notice |
| `/public-health/insights` | `GET` | `analytics.insight.review` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Published policy insights |
| `/public-health/insights` | `POST` | `analytics.insight.review` | STATE_PUBLIC_HEALTH_ANALYST | `STATE` | Publish new scientific insight note |

---

## 13. National Health Authority (`/api/v1/national`, `/governance`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/national/dashboard` | `GET` | `governance.national.view` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | Pan-India comparative health index |
| `/national/analytics` | `GET` | `governance.national.view` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | Macro multi-state disease trends |
| `/governance/schemes` | `GET` | `governance.scheme.read` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | National health mission progress |
| `/governance/actions` | `POST` | `governance.action.create` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | Issue inter-state coordination directive |
| `/governance/reports` | `GET` | `governance.report.review` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | Consolidated state health reports |
| `/governance/reports/generate` | `POST` | `governance.report.generate` | NATIONAL_HEALTH_AUTHORITY | `GLOBAL` | Generate national executive health brief |

---

## 14. Platform Administration & Governance (`/api/v1/platform`, `/users`, `/roles`, `/facilities`, `/audit-logs`)

| Endpoint | Method | Required Permission | Allowed Roles | Scope Enforcement | Description |
|:---|:---:|:---|:---|:---|:---|
| `/platform/dashboard` | `GET` | `platform.dashboard.view` | SUPER_ADMIN | `GLOBAL` | System telemetry, uptime, DB latency |
| `/platform/security-events` | `GET` | `platform.security.read` | SUPER_ADMIN | `GLOBAL` | Security incidents & failed logins stream |
| `/navigation/me` | `GET` | Authenticated | All 13 Roles | User Permissions | Dynamic authorized navigation menu items |
| `/users` | `GET` | `identity.user.read` | SUPER_ADMIN | `GLOBAL` | Search and list system users |
| `/users` | `POST` | `identity.user.create` | SUPER_ADMIN | `GLOBAL` | Provision new staff account |
| `/users/{id}` | `PATCH` | `identity.user.update` | SUPER_ADMIN | `GLOBAL` | Edit user profile or active status |
| `/users/{id}/roles` | `POST` | `identity.role.assign` | SUPER_ADMIN | `GLOBAL` | Assign role with administrative scope |
| `/users/{id}/roles/{role_id}` | `DELETE` | `identity.role.assign` | SUPER_ADMIN | `GLOBAL` | Revoke role assignment from user |
| `/roles` | `GET` | `identity.role.manage` | SUPER_ADMIN | `GLOBAL` | List all dynamic roles |
| `/roles` | `POST` | `identity.role.manage` | SUPER_ADMIN | `GLOBAL` | Create new customizable role |
| `/roles/{id}/permissions` | `POST` | `identity.role.manage` | SUPER_ADMIN | `GLOBAL` | Assign atomic permissions to role |
| `/permissions` | `GET` | `identity.role.manage` | SUPER_ADMIN | `GLOBAL` | List all system permission codes |
| `/facilities` | `GET` | Authenticated | All Staff | Scoped | List health facilities & warehouses |
| `/facilities` | `POST` | `identity.facility.manage` | SUPER_ADMIN | `GLOBAL` | Register new PHC, CHC, or warehouse |
| `/facilities/{id}` | `PATCH` | `identity.facility.manage` | SUPER_ADMIN | `GLOBAL` | Update facility operational metadata |
| `/audit-logs` | `GET` | `audit.log.read` | SUPER_ADMIN | `GLOBAL` | Search immutable security audit trail |
