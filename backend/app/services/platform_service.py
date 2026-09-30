"""Role 13 platform administration: system health, security telemetry, and permission-driven navigation.

The platform dashboard reports technical state only. Integrations that are not
connected (SMS/push gateways, external AI model, backup service) are reported
as NOT_CONFIGURED rather than pretending to be healthy.
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import SystemPermissions as P
from app.models.audit import AuditLog
from app.models.facility import Facility
from app.models.governance import AIInteraction
from app.models.identity import Role, User, UserSession
from app.models.intelligence import Alert
from app.models.public_health import AIAnalysisJob
from app.services.common import utcnow

SECURITY_ACTIONS = ["AUTH_LOGIN_FAILED", "USER_ROLE_ASSIGNED", "USER_ROLE_REVOKED", "ROLE_PERMISSIONS_ASSIGNED",
                    "ROLE_CREATED", "ROLE_UPDATED", "AUTH_PASSWORD_CHANGED"]

# Navigation catalogue: each item is shown only if the user holds its permission.
# Grouped by section so every role sees a coherent menu without role-name checks.
NAV_CATALOGUE: List[Dict] = [
    # Role 01: Patient
    {"section": "patient", "key": "patient.home", "path": "/patient", "icon": "home", "permission": P.PATIENTS_AWARENESS_READ},
    {"section": "patient", "key": "patient.appointments", "path": "/patient/appointments", "icon": "calendar", "permission": P.APPOINTMENTS_VIEW},
    {"section": "patient", "key": "patient.records", "path": "/patient/records", "icon": "file", "permission": P.PATIENTS_RECORDS_READ},
    {"section": "patient", "key": "patient.prescriptions", "path": "/patient/prescriptions", "icon": "pill", "permission": P.PRESCRIPTIONS_READ},
    {"section": "patient", "key": "patient.feedback", "path": "/patient/feedback", "icon": "chat", "permission": P.PATIENTS_FEEDBACK_SUBMIT},
    {"section": "patient", "key": "patient.assistant", "path": "/patient/assistant", "icon": "chat", "permission": P.PATIENTS_AI_WELLNESS_CHAT},

    # Role 02: Doctor (Clinical)
    {"section": "clinical", "key": "clinical.queue", "path": "/clinical/queue", "icon": "users", "permission": P.CONSULTATIONS_CONDUCT},
    {"section": "clinical", "key": "clinical.patients", "path": "/clinical/patients", "icon": "user",
     "permission": (P.CONSULTATIONS_CONDUCT, P.PATIENTS_VITALS_RECORD, P.PATIENTS_PROFILE_CREATE, P.LABS_SAMPLE_COLLECT)},
    {"section": "clinical", "key": "clinical.labs", "path": "/clinical/labs", "icon": "flask", "permission": P.LABS_ORDER_READ},
    {"section": "clinical", "key": "clinical.inventory", "path": "/clinical/inventory", "icon": "box", "permission": P.INVENTORY_ITEM_READ},

    # Role 03: Nurse (Clinical)
    {"section": "clinical", "key": "clinical.triage", "path": "/clinical/triage", "icon": "activity", "permission": P.PATIENTS_VITALS_RECORD},
    {"section": "clinical", "key": "clinical.registration", "path": "/clinical/registration", "icon": "user", "permission": P.PATIENTS_PROFILE_CREATE},
    {"section": "clinical", "key": "clinical.coldchain", "path": "/clinical/coldchain", "icon": "box", "permission": P.COLD_CHAIN_READ},
    {"section": "clinical", "key": "clinical.immunization", "path": "/clinical/immunization", "icon": "activity", "permission": P.CLINICAL_AI_ADVISORY},

    # Role 04: PHC In-Charge (Facility)
    {"section": "facility", "key": "facility.dashboard", "path": "/facility", "icon": "building", "permission": P.FACILITY_REPORT_VIEW},
    {"section": "facility", "key": "facility.attendance", "path": "/facility/attendance", "icon": "users", "permission": P.STAFF_ATTENDANCE_ADMIN},
    {"section": "facility", "key": "facility.coldchain", "path": "/facility/coldchain", "icon": "box", "permission": P.COLD_CHAIN_MANAGE},
    {"section": "facility", "key": "facility.camps", "path": "/facility/camps", "icon": "map", "permission": P.OUTREACH_CAMP_MANAGE},
    {"section": "facility", "key": "facility.grievances", "path": "/facility/grievances", "icon": "clipboard", "permission": P.FACILITY_COMPLAINT_MANAGE},

    # Role 05: Pharmacist
    {"section": "pharmacy", "key": "pharmacy.dispense", "path": "/pharmacy/dispense", "icon": "pill", "permission": P.PRESCRIPTIONS_DISPENSE},
    {"section": "pharmacy", "key": "pharmacy.inventory", "path": "/pharmacy/inventory", "icon": "box", "permission": P.INVENTORY_STOCK_ADJUST},
    {"section": "pharmacy", "key": "pharmacy.alerts", "path": "/pharmacy/alerts", "icon": "alert", "permission": P.SHORTAGES_INCIDENT_REPORT},
    {"section": "pharmacy", "key": "pharmacy.receipts", "path": "/pharmacy/receipts", "icon": "truck", "permission": P.INVENTORY_TRANSFER_RECEIVE},
    {"section": "pharmacy", "key": "pharmacy.druginfo", "path": "/pharmacy/druginfo", "icon": "file", "permission": P.AI_FORECAST_VIEW},

    # Role 06: District Health Officer
    {"section": "district", "key": "district.dashboard", "path": "/district", "icon": "map", "permission": P.GOVERNANCE_DISTRICT_VIEW},
    {"section": "district", "key": "district.facilities", "path": "/district/facilities", "icon": "building", "permission": P.GOVERNANCE_DISTRICT_VIEW},
    {"section": "district", "key": "governance.actions", "path": "/governance/actions", "icon": "list", "permission": P.GOVERNANCE_ACTION_CREATE},
    {"section": "district", "key": "governance.alerts", "path": "/governance/alerts", "icon": "bell", "permission": P.GOVERNANCE_ALERT_MANAGE},
    {"section": "district", "key": "district.supply_impacts", "path": "/district/supply-impacts", "icon": "alert", "permission": P.SUPPLY_IMPACT_READ},

    # Role 07: District Supply Officer
    {"section": "supply", "key": "supply.requests", "path": "/supply/requests", "icon": "clipboard", "permission": P.SUPPLY_REQUEST_REVIEW},
    {"section": "supply", "key": "supply.transfers", "path": "/supply/transfers", "icon": "truck", "permission": P.INVENTORY_TRANSFER_APPROVE},
    {"section": "supply", "key": "supply.warehouse", "path": "/supply/warehouse", "icon": "box", "permission": P.DASHBOARDS_SUPPLY_VIEW},
    {"section": "supply", "key": "supply.impacts", "path": "/supply/impacts", "icon": "alert", "permission": P.SUPPLY_IMPACT_SHARE},

    # Role 08: District Emergency Coordinator
    {"section": "emergency", "key": "emergency.dashboard", "path": "/emergency", "icon": "siren", "permission": P.EMERGENCY_INCIDENT_READ},
    {"section": "emergency", "key": "emergency.incidents", "path": "/emergency/incidents", "icon": "alert", "permission": P.EMERGENCY_INCIDENT_READ},
    {"section": "emergency", "key": "emergency.tasks", "path": "/emergency/tasks", "icon": "check", "permission": P.EMERGENCY_INCIDENT_MANAGE},
    {"section": "emergency", "key": "emergency.resources", "path": "/emergency/resources", "icon": "truck", "permission": P.EMERGENCY_INCIDENT_RESOLVE},

    # Role 09: State Health Admin
    {"section": "state", "key": "state.dashboard", "path": "/state", "icon": "map", "permission": P.GOVERNANCE_STATE_VIEW},
    {"section": "state", "key": "state.districts", "path": "/state/districts", "icon": "building", "permission": P.GOVERNANCE_STATE_VIEW},
    {"section": "state", "key": "governance.approvals", "path": "/governance/approvals", "icon": "check", "permission": P.GOVERNANCE_APPROVAL_DECIDE},
    {"section": "state", "key": "governance.schemes", "path": "/governance/schemes", "icon": "target", "permission": P.GOVERNANCE_SCHEME_MANAGE},
    {"section": "state", "key": "governance.reports", "path": "/governance/reports", "icon": "file", "permission": P.GOVERNANCE_REPORT_REVIEW},
    {"section": "state", "key": "governance.insights", "path": "/governance/insights", "icon": "chart", "permission": P.ANALYTICS_INDICATOR_READ},

    # Role 10: State Supply Manager
    {"section": "supply", "key": "supply.dashboard", "path": "/supply", "icon": "truck", "permission": P.SUPPLY_ALLOCATION_MANAGE},
    {"section": "supply", "key": "supply.escalated", "path": "/supply/escalated", "icon": "clipboard", "permission": P.SUPPLY_REQUEST_REVIEW},
    {"section": "supply", "key": "supply.warehouse", "path": "/supply/warehouse", "icon": "box", "permission": P.WAREHOUSE_MANAGE},
    {"section": "supply", "key": "supply.monitoring", "path": "/supply/monitoring", "icon": "activity", "permission": P.AI_RISK_ANALYZE},
    {"section": "supply", "key": "supply.shortages", "path": "/supply/shortages", "icon": "alert", "permission": P.SHORTAGES_INCIDENT_RESOLVE},

    # Role 11: State Public Health Analyst
    {"section": "analytics", "key": "analytics.dashboard", "path": "/analytics", "icon": "chart", "permission": P.ANALYTICS_INDICATOR_READ},
    {"section": "analytics", "key": "analytics.indicators", "path": "/analytics/indicators", "icon": "target", "permission": P.ANALYTICS_INDICATOR_MANAGE},
    {"section": "analytics", "key": "analytics.aggregates", "path": "/analytics/aggregates", "icon": "list", "permission": P.ANALYTICS_AGGREGATE_SUBMIT},
    {"section": "analytics", "key": "analytics.trends", "path": "/analytics/trends", "icon": "activity", "permission": P.ANALYTICS_INSIGHT_REVIEW},
    {"section": "analytics", "key": "analytics.jobs", "path": "/analytics/jobs", "icon": "server", "permission": P.ANALYTICS_DATA_QUALITY_MANAGE},
    {"section": "analytics", "key": "analytics.dataquality", "path": "/analytics/dataquality", "icon": "shield", "permission": P.ANALYTICS_DATA_QUALITY_MANAGE},

    # Role 12: National Health Authority
    {"section": "national", "key": "national.dashboard", "path": "/national", "icon": "globe", "permission": P.GOVERNANCE_NATIONAL_VIEW},
    {"section": "national", "key": "national.states", "path": "/national/states", "icon": "building", "permission": P.GOVERNANCE_NATIONAL_VIEW},
    {"section": "national", "key": "national.supply_grid", "path": "/national/supply-grid", "icon": "truck", "permission": P.GOVERNANCE_NATIONAL_VIEW},
    {"section": "national", "key": "governance.actions", "path": "/governance/actions", "icon": "list", "permission": P.GOVERNANCE_ACTION_CREATE},

    # Cross-role: capacity (beds/attendance), supply intelligence and Google-powered tools
    {"section": "patient", "key": "patient.nearest", "path": "/facilities/nearest", "icon": "map", "permission": P.PATIENTS_AWARENESS_READ},
    {"section": "capacity", "key": "capacity.dashboard", "path": "/capacity", "icon": "activity", "permission": P.BEDS_READ},
    {"section": "capacity", "key": "capacity.beds", "path": "/capacity/beds", "icon": "building", "permission": P.BEDS_OCCUPANCY_UPDATE},
    {"section": "intelligence", "key": "intelligence.warnings", "path": "/intelligence/warnings", "icon": "alert", "permission": P.AI_RISK_ANALYZE},
    {"section": "intelligence", "key": "intelligence.redistribution", "path": "/intelligence/redistribution", "icon": "truck", "permission": P.AI_RISK_ANALYZE},
    {"section": "intelligence", "key": "intelligence.federation", "path": "/intelligence/federation", "icon": "globe", "permission": P.AI_FORECAST_VIEW},
    {"section": "intelligence", "key": "intelligence.google", "path": "/admin/google", "icon": "server", "permission": P.GOVERNANCE_REPORT_GENERATE},

    # Role 13: Super / Platform Administrator
    {"section": "platform", "key": "platform.dashboard", "path": "/platform", "icon": "server", "permission": P.PLATFORM_DASHBOARD_VIEW},
    {"section": "platform", "key": "platform.security", "path": "/platform/security", "icon": "shield", "permission": P.PLATFORM_SECURITY_READ},
    {"section": "platform", "key": "platform.users", "path": "/platform/users", "icon": "users", "permission": P.IDENTITY_USER_READ},
    {"section": "platform", "key": "platform.roles", "path": "/platform/roles", "icon": "lock", "permission": P.IDENTITY_ROLE_MANAGE},
    {"section": "platform", "key": "platform.audit", "path": "/platform/audit", "icon": "shield", "permission": P.AUDIT_LOG_READ},
]


def navigation_for(permissions: Set[str]) -> List[Dict]:
    seen_paths = set()
    items = []
    for item in NAV_CATALOGUE:
        required = item["permission"]
        # A tuple means "any of these": used where a shared permission (e.g. patients.profile.read, which patients also
        # hold for their own record) must not be enough to reveal a staff-only screen.
        allowed = any(p in permissions for p in required) if isinstance(required, tuple) else required in permissions
        if allowed:
            if item["path"] not in seen_paths:
                seen_paths.add(item["path"])
                items.append({k: v for k, v in item.items() if k != "permission"})
    return items


class PlatformService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _count(self, stmt) -> int:
        return (await self.session.execute(stmt)).scalar_one() or 0

    async def dashboard(self) -> dict:
        t0 = time.perf_counter()
        db_ok = True
        try:
            await self.session.execute(text("SELECT 1"))
        except Exception:  # reported as DOWN on the dashboard, not hidden
            db_ok = False
        db_ms = round((time.perf_counter() - t0) * 1000, 2)
        now = utcnow()
        day = now - timedelta(days=1)
        facility_types = dict((await self.session.execute(
            select(Facility.facility_type, func.count()).group_by(Facility.facility_type))).all())
        last_job = (await self.session.execute(select(AIAnalysisJob).order_by(AIAnalysisJob.started_at.desc()).limit(1))).scalar_one_or_none()
        return {
            "as_of": now,
            "environment": settings.ENVIRONMENT,
            "database": {"status": "UP" if db_ok else "DOWN", "latency_ms": db_ms},
            "users": {
                "total": await self._count(select(func.count(User.id))),
                "active": await self._count(select(func.count(User.id)).where(User.is_active.is_(True))),
                "active_sessions": await self._count(select(func.count(UserSession.id)).where(
                    UserSession.is_revoked.is_(False), UserSession.expires_at > now)),
            },
            "roles": await self._count(select(func.count(Role.id)).where(Role.is_active.is_(True))),
            "geography": {
                "states": await self._count(select(func.count(func.distinct(func.lower(Facility.state))))),
                "districts": await self._count(select(func.count(func.distinct(func.lower(Facility.state) + "/" + func.lower(Facility.district))))),
                "facilities": await self._count(select(func.count(Facility.id))),
                "active_facilities": await self._count(select(func.count(Facility.id)).where(Facility.is_active.is_(True))),
                "by_type": {(k.value if hasattr(k, "value") else k): v for k, v in facility_types.items()},
            },
            "security_24h": {
                "failed_logins": await self._count(select(func.count(AuditLog.id)).where(
                    AuditLog.action == "AUTH_LOGIN_FAILED", AuditLog.created_at >= day)),
                "successful_logins": await self._count(select(func.count(AuditLog.id)).where(
                    AuditLog.action == "AUTH_LOGIN_SUCCESS", AuditLog.created_at >= day)),
                "privilege_changes": await self._count(select(func.count(AuditLog.id)).where(
                    AuditLog.action.in_(SECURITY_ACTIONS[1:6]), AuditLog.created_at >= day)),
            },
            "audit_events_24h": await self._count(select(func.count(AuditLog.id)).where(AuditLog.created_at >= day)),
            "operational_alerts_unacknowledged": await self._count(select(func.count(Alert.id)).where(Alert.is_acknowledged.is_(False))),
            "ai": {
                "provider": "RULE_BASED (no external model configured)",
                "interactions_24h": await self._count(select(func.count(AIInteraction.id)).where(AIInteraction.created_at >= day)),
                "refusals_24h": await self._count(select(func.count(AIInteraction.id)).where(
                    AIInteraction.created_at >= day, AIInteraction.refused.is_(True))),
            },
            "background_jobs": {
                "scheduler_enabled": settings.ENABLE_BACKGROUND_JOBS,
                "last_analysis": {"status": last_job.status.value, "started_at": last_job.started_at,
                                  "error": last_job.error_reference} if last_job else None,
            },
            "integrations": {
                "sms_gateway": "NOT_CONFIGURED",
                "push_notifications": "NOT_CONFIGURED",
                "external_ai_model": "NOT_CONFIGURED",
                "backup_service": "MANAGED_OUTSIDE_APPLICATION",
            },
        }

    async def security_events(self, limit: int = 100) -> List[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.action.in_(SECURITY_ACTIONS)).order_by(AuditLog.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
