"""Seed catalogue for the 13 agreed roles (main.md §1.1) plus supporting technical roles.

This is only the *initial* policy written into the database by the seed
scripts; at runtime authorization always reads roles/permissions from the DB,
so administrators can change grants without code changes. `default_scope`
is the scope level used when the demo seed assigns the role.
"""
from typing import Dict, List

from app.core.permissions import SystemPermissions as P

_PLATFORM = {
    P.IDENTITY_USER_CREATE, P.IDENTITY_USER_READ, P.IDENTITY_USER_UPDATE, P.IDENTITY_USER_DEACTIVATE,
    P.IDENTITY_ROLE_ASSIGN, P.IDENTITY_ROLE_MANAGE, P.IDENTITY_FACILITY_MANAGE, P.AUDIT_LOG_READ,
    P.SYSTEM_CONFIG_MANAGE, P.PLATFORM_DASHBOARD_VIEW, P.PLATFORM_SECURITY_READ,
}
_GOV_READ = {P.GOVERNANCE_ALERT_READ, P.GOVERNANCE_AI_ASSIST, P.ALERTS_READ}

ROLES_CONFIG: List[Dict] = [
    # ---------------------------------------------------------------- Role 13 (platform, not clinical)
    {
        "code": "SUPER_ADMIN",
        "name": "National Platform Administrator / Super Admin",
        "description": "Technical platform authority: users, RBAC, facilities, configuration, security and audit. "
                       "Holds no clinical or healthcare decision authority.",
        "default_scope": "GLOBAL",
        "permissions": set(_PLATFORM),
    },
    {
        "code": "SYSTEM_ADMIN",
        "name": "System Administrator",
        "description": "Administrative authority for user provisioning, facilities, and dynamic RBAC.",
        "default_scope": "GLOBAL",
        "permissions": {
            P.IDENTITY_USER_CREATE, P.IDENTITY_USER_READ, P.IDENTITY_USER_UPDATE, P.IDENTITY_USER_DEACTIVATE,
            P.IDENTITY_ROLE_ASSIGN, P.IDENTITY_ROLE_MANAGE, P.IDENTITY_FACILITY_MANAGE, P.AUDIT_LOG_READ,
            P.SYSTEM_CONFIG_MANAGE, P.ALERTS_READ, P.ALERTS_ACKNOWLEDGE, P.PLATFORM_DASHBOARD_VIEW,
        },
    },
    {
        "code": "AUDITOR",
        "name": "Compliance & Security Auditor",
        "description": "Read-only access to audit logs, security telemetry, and compliance reports.",
        "default_scope": "GLOBAL",
        "permissions": {P.AUDIT_LOG_READ, P.IDENTITY_USER_READ, P.INVENTORY_ITEM_READ, P.PROCUREMENT_ORDER_READ,
                        P.SHIPMENTS_READ, P.PLATFORM_SECURITY_READ},
    },
    # ---------------------------------------------------------------- Role 01
    {
        "code": "PATIENT",
        "name": "Citizen / Patient",
        "description": "Personal health portal access for clinical history, appointments, feedback, and AI wellness.",
        "default_scope": "SELF",
        "permissions": {
            P.PATIENTS_PROFILE_READ, P.PATIENTS_PROFILE_UPDATE, P.PATIENTS_RECORDS_READ, P.APPOINTMENTS_VIEW,
            P.PRESCRIPTIONS_READ, P.PATIENTS_FEEDBACK_SUBMIT, P.PATIENTS_FEEDBACK_READ, P.PATIENTS_AWARENESS_READ,
            P.PATIENTS_AI_WELLNESS_CHAT, P.PATIENTS_NOTIFICATIONS_READ,
        },
    },
    # ---------------------------------------------------------------- Role 02
    {
        "code": "DOCTOR",
        "name": "Medical Officer",
        "description": "Primary healthcare physician conducting consultations, writing prescriptions, and ordering lab tests.",
        "default_scope": "FACILITY",
        "permissions": {
            P.PATIENTS_PROFILE_READ, P.PATIENTS_RECORDS_READ, P.APPOINTMENTS_VIEW, P.CONSULTATIONS_CONDUCT,
            P.PRESCRIPTIONS_CREATE, P.PRESCRIPTIONS_READ, P.LABS_ORDER_CREATE, P.LABS_ORDER_READ,
            P.REFERRALS_CREATE, P.REFERRALS_READ, P.REFERRALS_UPDATE, P.INVENTORY_ITEM_READ,
            P.DASHBOARDS_CLINICAL_VIEW, P.ALERTS_READ, P.STAFF_ATTENDANCE_RECORD, P.STAFF_ATTENDANCE_READ,
            P.CLINICAL_AI_ADVISORY, P.EMERGENCY_INCIDENT_REPORT, P.GOVERNANCE_ACTION_RESPOND,
        },
    },
    # ---------------------------------------------------------------- Role 03
    {
        "code": "NURSE",
        "name": "Nurse / Healthcare Staff",
        "description": "Triage vitals recording, patient intake, appointment roster management.",
        "default_scope": "FACILITY",
        "permissions": {
            P.PATIENTS_PROFILE_CREATE, P.PATIENTS_PROFILE_READ, P.PATIENTS_PROFILE_UPDATE, P.PATIENTS_VITALS_RECORD,
            P.APPOINTMENTS_MANAGE, P.APPOINTMENTS_VIEW, P.PRESCRIPTIONS_READ, P.INVENTORY_ITEM_READ, P.ALERTS_READ,
            P.STAFF_ATTENDANCE_RECORD, P.STAFF_ATTENDANCE_READ, P.CLINICAL_AI_ADVISORY, P.LABS_SAMPLE_COLLECT,
            P.LABS_ORDER_READ, P.COLD_CHAIN_READ, P.COLD_CHAIN_LOG, P.GOVERNANCE_ACTION_RESPOND,
        },
    },
    {
        "code": "LAB_TECHNICIAN",
        "name": "Laboratory Technician",
        "description": "Performs laboratory diagnostic tests and records results.",
        "default_scope": "FACILITY",
        "permissions": {P.LABS_ORDER_READ, P.LABS_SAMPLE_COLLECT, P.LABS_RESULT_RECORD, P.LABS_RESULT_VERIFY,
                        P.PATIENTS_PROFILE_READ, P.STAFF_ATTENDANCE_RECORD, P.STAFF_ATTENDANCE_READ},
    },
    # ---------------------------------------------------------------- Role 04
    {
        "code": "PHC_IN_CHARGE",
        "name": "PHC In-charge / Facility Manager",
        "description": "Facility administration, staff supervision, cold chain, outreach, complaints and operational reporting.",
        "default_scope": "FACILITY",
        "permissions": {
            P.STAFF_ATTENDANCE_READ, P.STAFF_ATTENDANCE_ADMIN, P.STAFF_ATTENDANCE_RECORD, P.COLD_CHAIN_READ,
            P.COLD_CHAIN_LOG, P.COLD_CHAIN_MANAGE, P.OUTREACH_CAMP_READ, P.OUTREACH_CAMP_MANAGE,
            P.FACILITY_REPORT_VIEW, P.FACILITY_COMPLAINT_MANAGE, P.PATIENTS_FEEDBACK_READ, P.PATIENTS_FEEDBACK_MANAGE,
            P.APPOINTMENTS_VIEW, P.INVENTORY_ITEM_READ, P.DASHBOARDS_CLINICAL_VIEW, P.DASHBOARDS_SUPPLY_VIEW,
            P.ALERTS_READ, P.ALERTS_ACKNOWLEDGE, P.SUPPLY_REQUEST_READ, P.EMERGENCY_INCIDENT_REPORT,
            P.EMERGENCY_INCIDENT_READ, P.GOVERNANCE_ACTION_RESPOND, P.GOVERNANCE_SCHEME_READ,
        },
    },
    # ---------------------------------------------------------------- Role 05
    {
        "code": "PHARMACIST",
        "name": "Pharmacist / PHC Storekeeper",
        "description": "Dispensing, FEFO batches, facility inventory, supply requests and receipt verification.",
        "default_scope": "FACILITY",
        "permissions": {
            P.PRESCRIPTIONS_READ, P.PRESCRIPTIONS_DISPENSE, P.INVENTORY_ITEM_READ, P.INVENTORY_ITEM_CREATE,
            P.INVENTORY_STOCK_ADJUST, P.INVENTORY_MOVEMENT_RECORD, P.INVENTORY_TRANSFER_REQUEST,
            P.INVENTORY_TRANSFER_RECEIVE, P.SHORTAGES_INCIDENT_REPORT, P.ALERTS_READ, P.DASHBOARDS_SUPPLY_VIEW,
            P.AI_FORECAST_VIEW, P.SUPPLY_REQUEST_CREATE, P.SUPPLY_REQUEST_READ, P.SUPPLY_RECEIPT_VERIFY,
            P.STAFF_ATTENDANCE_RECORD, P.STAFF_ATTENDANCE_READ,
        },
    },
    {
        "code": "INVENTORY_OFFICER",
        "name": "Facility / Warehouse Storekeeper",
        "description": "Warehouse receipts, physical counts, stock movements, transfer receipt and dispatch.",
        "default_scope": "FACILITY",
        "permissions": {
            P.INVENTORY_ITEM_READ, P.INVENTORY_ITEM_CREATE, P.INVENTORY_STOCK_ADJUST, P.INVENTORY_MOVEMENT_RECORD,
            P.INVENTORY_TRANSFER_REQUEST, P.INVENTORY_TRANSFER_RECEIVE, P.INVENTORY_TRANSFER_DISPATCH,
            P.SHORTAGES_INCIDENT_REPORT, P.ALERTS_READ, P.DASHBOARDS_SUPPLY_VIEW, P.SUPPLY_REQUEST_CREATE,
            P.SUPPLY_REQUEST_READ, P.SUPPLY_RECEIPT_VERIFY,
        },
    },
    # ---------------------------------------------------------------- Role 06
    {
        "code": "DISTRICT_HEALTH_OFFICER",
        "name": "District Health Officer (DHO)",
        "description": "District health administration and oversight using aggregated PHC information.",
        "default_scope": "DISTRICT",
        "permissions": _GOV_READ | {
            P.GOVERNANCE_DISTRICT_VIEW, P.GOVERNANCE_ACTION_CREATE, P.GOVERNANCE_ACTION_MANAGE,
            P.GOVERNANCE_ALERT_MANAGE, P.GOVERNANCE_REPORT_GENERATE, P.GOVERNANCE_APPROVAL_REQUEST,
            P.GOVERNANCE_SCHEME_READ, P.GOVERNANCE_SCHEME_REPORT, P.SUPPLY_IMPACT_READ, P.SUPPLY_REQUEST_READ,
            P.EMERGENCY_INCIDENT_READ, P.EMERGENCY_INCIDENT_RESOLVE, P.ANALYTICS_AGGREGATE_SUBMIT,
            P.ANALYTICS_INDICATOR_READ, P.DASHBOARDS_CLINICAL_VIEW,
        },
    },
    # ---------------------------------------------------------------- Role 07
    {
        "code": "DISTRICT_SUPPLY_OFFICER",
        "name": "District Supply Chain Officer",
        "description": "District medicine supply: request review, district allocation, redistribution, state escalation.",
        "default_scope": "DISTRICT",
        "permissions": _GOV_READ | {
            P.INVENTORY_ITEM_READ, P.INVENTORY_TRANSFER_APPROVE, P.INVENTORY_TRANSFER_DISPATCH,
            P.PROCUREMENT_REQUEST_CREATE, P.PROCUREMENT_REQUEST_APPROVE, P.SHORTAGES_INCIDENT_ESCALATE,
            P.SHORTAGES_INCIDENT_RESOLVE, P.SHIPMENTS_READ, P.DASHBOARDS_SUPPLY_VIEW, P.AI_FORECAST_VIEW,
            P.AI_RISK_ANALYZE, P.ALERTS_ACKNOWLEDGE, P.SUPPLY_REQUEST_READ, P.SUPPLY_REQUEST_REVIEW,
            P.SUPPLY_IMPACT_SHARE, P.GOVERNANCE_ACTION_RESPOND,
        },
    },
    # ---------------------------------------------------------------- Role 08
    {
        "code": "DISTRICT_EMERGENCY_COORDINATOR",
        "name": "District Emergency Coordinator",
        "description": "Coordinates district emergency response, staff/resource needs and escalation.",
        "default_scope": "DISTRICT",
        "permissions": _GOV_READ | {
            P.EMERGENCY_INCIDENT_REPORT, P.EMERGENCY_INCIDENT_READ, P.EMERGENCY_INCIDENT_MANAGE,
            P.EMERGENCY_INCIDENT_RESOLVE, P.SUPPLY_REQUEST_READ, P.GOVERNANCE_ACTION_RESPOND,
            P.GOVERNANCE_REPORT_GENERATE,
        },
    },
    # ---------------------------------------------------------------- Role 09
    {
        "code": "STATE_HEALTH_ADMIN",
        "name": "State Health Administrator",
        "description": "State health administration: district oversight, alerts, approvals, schemes and reports.",
        "default_scope": "STATE",
        "permissions": _GOV_READ | {
            P.GOVERNANCE_STATE_VIEW, P.GOVERNANCE_ACTION_CREATE, P.GOVERNANCE_ACTION_MANAGE, P.GOVERNANCE_ALERT_MANAGE,
            P.GOVERNANCE_REPORT_GENERATE, P.GOVERNANCE_REPORT_REVIEW, P.GOVERNANCE_APPROVAL_DECIDE,
            P.GOVERNANCE_SCHEME_READ, P.GOVERNANCE_SCHEME_MANAGE, P.SUPPLY_IMPACT_READ, P.EMERGENCY_INCIDENT_READ,
            P.ANALYTICS_INDICATOR_READ,
        },
    },
    # ---------------------------------------------------------------- Role 10
    {
        "code": "STATE_SUPPLY_MANAGER",
        "name": "State Supply Chain / Warehouse Manager",
        "description": "State warehouse inventory, district request review, allocation, dispatch and replenishment.",
        "default_scope": "STATE",
        "permissions": _GOV_READ | {
            P.INVENTORY_ITEM_READ, P.INVENTORY_ITEM_CREATE, P.INVENTORY_STOCK_ADJUST, P.INVENTORY_MOVEMENT_RECORD,
            P.INVENTORY_TRANSFER_APPROVE, P.INVENTORY_TRANSFER_DISPATCH, P.WAREHOUSE_MANAGE,
            P.PROCUREMENT_REQUEST_CREATE, P.PROCUREMENT_ORDER_CREATE, P.PROCUREMENT_ORDER_READ, P.SUPPLIERS_MANAGE,
            P.SHIPMENTS_CREATE, P.SHIPMENTS_UPDATE, P.SHIPMENTS_READ, P.SHORTAGES_INCIDENT_RESOLVE,
            P.DASHBOARDS_SUPPLY_VIEW, P.AI_FORECAST_VIEW, P.AI_RISK_ANALYZE, P.ALERTS_ACKNOWLEDGE,
            P.SUPPLY_REQUEST_READ, P.SUPPLY_REQUEST_REVIEW, P.SUPPLY_ALLOCATION_MANAGE, P.GOVERNANCE_ACTION_RESPOND,
        },
    },
    # ---------------------------------------------------------------- Role 11
    {
        "code": "STATE_PUBLIC_HEALTH_ANALYST",
        "name": "State Public Health Analyst",
        "description": "Public-health analytics on aggregated data: trends, insights review, data quality, reports.",
        "default_scope": "STATE",
        "permissions": _GOV_READ | {
            P.ANALYTICS_INDICATOR_READ, P.ANALYTICS_INDICATOR_MANAGE, P.ANALYTICS_AGGREGATE_SUBMIT,
            P.ANALYTICS_INSIGHT_REVIEW, P.ANALYTICS_DATA_QUALITY_MANAGE, P.GOVERNANCE_ALERT_MANAGE,
            P.GOVERNANCE_REPORT_GENERATE,
        },
    },
    # ---------------------------------------------------------------- Role 12
    {
        "code": "NATIONAL_HEALTH_AUTHORITY",
        "name": "National Health Authority / Central Administrator",
        "description": "National oversight of state-level aggregates, coordination requests, reports and alerts.",
        "default_scope": "GLOBAL",
        "permissions": _GOV_READ | {
            P.GOVERNANCE_NATIONAL_VIEW, P.GOVERNANCE_ACTION_CREATE, P.GOVERNANCE_ACTION_MANAGE,
            P.GOVERNANCE_ALERT_MANAGE, P.GOVERNANCE_REPORT_GENERATE, P.GOVERNANCE_REPORT_REVIEW,
            P.GOVERNANCE_SCHEME_READ, P.ANALYTICS_INDICATOR_READ, P.ANALYTICS_INSIGHT_REVIEW,
        },
    },
]

ROLE_BY_CODE = {r["code"]: r for r in ROLES_CONFIG}
