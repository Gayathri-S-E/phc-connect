from typing import Set


class SystemPermissions:
    """Canonical permission codes seeded into the database permissions table."""

    # Identity & Governance
    IDENTITY_USER_CREATE = "identity.user.create"
    IDENTITY_USER_READ = "identity.user.read"
    IDENTITY_USER_UPDATE = "identity.user.update"
    IDENTITY_USER_DEACTIVATE = "identity.user.deactivate"
    IDENTITY_ROLE_ASSIGN = "identity.role.assign"
    IDENTITY_ROLE_MANAGE = "identity.role.manage"
    IDENTITY_FACILITY_MANAGE = "identity.facility.manage"
    AUDIT_LOG_READ = "audit.log.read"
    SYSTEM_CONFIG_MANAGE = "system.config.manage"

    # Healthcare Core
    PATIENTS_PROFILE_CREATE = "patients.profile.create"
    PATIENTS_PROFILE_READ = "patients.profile.read"
    PATIENTS_PROFILE_UPDATE = "patients.profile.update"
    PATIENTS_RECORDS_READ = "patients.records.read"
    PATIENTS_VITALS_RECORD = "patients.vitals.record"
    APPOINTMENTS_MANAGE = "appointments.manage"
    APPOINTMENTS_VIEW = "appointments.view"
    CONSULTATIONS_CONDUCT = "consultations.conduct"
    PRESCRIPTIONS_CREATE = "prescriptions.create"
    PRESCRIPTIONS_READ = "prescriptions.read"
    PRESCRIPTIONS_DISPENSE = "prescriptions.dispense"
    LABS_ORDER_CREATE = "labs.order.create"
    LABS_ORDER_READ = "labs.order.read"
    LABS_SAMPLE_COLLECT = "labs.sample.collect"
    LABS_RESULT_RECORD = "labs.result.record"
    LABS_RESULT_VERIFY = "labs.result.verify"
    REFERRALS_CREATE = "referrals.create"
    REFERRALS_READ = "referrals.read"
    REFERRALS_UPDATE = "referrals.update"
    PATIENTS_FEEDBACK_SUBMIT = "patients.feedback.submit"
    PATIENTS_FEEDBACK_READ = "patients.feedback.read"
    PATIENTS_FEEDBACK_MANAGE = "patients.feedback.manage"
    PATIENTS_AWARENESS_READ = "patients.awareness.read"
    PATIENTS_AI_WELLNESS_CHAT = "patients.ai.wellness.chat"
    PATIENTS_NOTIFICATIONS_READ = "patients.notifications.read"
    STAFF_ATTENDANCE_RECORD = "staff.attendance.record"
    STAFF_ATTENDANCE_READ = "staff.attendance.read"
    STAFF_ATTENDANCE_ADMIN = "staff.attendance.admin"
    CLINICAL_AI_ADVISORY = "clinical.ai.advisory"
    COLD_CHAIN_READ = "cold_chain.read"
    COLD_CHAIN_LOG = "cold_chain.log"
    COLD_CHAIN_MANAGE = "cold_chain.manage"
    OUTREACH_CAMP_READ = "outreach.camp.read"
    OUTREACH_CAMP_MANAGE = "outreach.camp.manage"
    FACILITY_REPORT_VIEW = "facility.report.view"
    FACILITY_COMPLAINT_MANAGE = "facility.complaint.manage"

    # Inventory & Pharmacy
    INVENTORY_ITEM_READ = "inventory.item.read"
    INVENTORY_ITEM_CREATE = "inventory.item.create"
    INVENTORY_STOCK_ADJUST = "inventory.stock.adjust"
    INVENTORY_MOVEMENT_RECORD = "inventory.movement.record"
    INVENTORY_TRANSFER_REQUEST = "inventory.transfer.request"
    INVENTORY_TRANSFER_APPROVE = "inventory.transfer.approve"
    INVENTORY_TRANSFER_DISPATCH = "inventory.transfer.dispatch"
    INVENTORY_TRANSFER_RECEIVE = "inventory.transfer.receive"
    WAREHOUSE_MANAGE = "warehouse.manage"

    # Procurement & Supply Chain
    PROCUREMENT_REQUEST_CREATE = "procurement.request.create"
    PROCUREMENT_REQUEST_APPROVE = "procurement.request.approve"
    PROCUREMENT_ORDER_CREATE = "procurement.order.create"
    PROCUREMENT_ORDER_APPROVE = "procurement.order.approve"
    PROCUREMENT_ORDER_READ = "procurement.order.read"
    SUPPLIERS_MANAGE = "suppliers.manage"
    SHIPMENTS_CREATE = "shipments.create"
    SHIPMENTS_UPDATE = "shipments.update"
    SHIPMENTS_READ = "shipments.read"
    SHORTAGES_INCIDENT_REPORT = "shortages.incident.report"
    SHORTAGES_INCIDENT_ESCALATE = "shortages.incident.escalate"
    SHORTAGES_INCIDENT_RESOLVE = "shortages.incident.resolve"

    # Intelligence & Observability
    DASHBOARDS_CLINICAL_VIEW = "dashboards.clinical.view"
    DASHBOARDS_SUPPLY_VIEW = "dashboards.supply.view"
    AI_FORECAST_VIEW = "ai.forecast.view"
    AI_RISK_ANALYZE = "ai.risk.analyze"
    ALERTS_READ = "alerts.read"
    ALERTS_ACKNOWLEDGE = "alerts.acknowledge"

    @classmethod
    def all_permissions(cls) -> Set[str]:
        return {
            val for key, val in cls.__dict__.items()
            if not key.startswith("_") and isinstance(val, str)
        }
