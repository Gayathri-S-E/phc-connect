"""District emergency coordination (Role 08).

Priority is set only by an authorized human; resolution needs every task
closed plus an explicit confirmation reference; supply needs go through the
shared SupplyRequest workflow owned by the District Supply Chain Officer.
Staff and resource views are read-only and limited to affected facilities.
"""
import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.core.jurisdiction import Jurisdiction
from app.models.emergency import (
    EmergencyAffectedFacility,
    EmergencyEscalation,
    EmergencyIncident,
    EmergencyStatus,
    EmergencyTask,
    EmergencyTaskStatus,
    EmergencyUpdate,
)
from app.models.facility import Facility
from app.models.governance import ActionPriority, ActionStatus, ActionUpdateType, GovernanceAction, GovernanceActionUpdate, GovernanceLevel
from app.models.healthcare import Medication, Patient, StaffAttendance
from app.models.identity import Role, ScopeLevel, User, UserRole
from app.models.pharmacy import InventoryItem
from app.models.supply_chain import SupplyRequest
from app.schemas.emergency import (
    AffectedFacilityUpsert,
    EmergencyCreate,
    EmergencyEscalationCreate,
    EmergencyPrioritySet,
    EmergencyResolve,
    EmergencyResourceRequestCreate,
    EmergencyStatusUpdate,
    EmergencyTaskCreate,
    EmergencyTaskUpdate,
)
from app.schemas.supply_requests import SupplyRequestCreate
from app.services.common import AuditCtx, AuditMixin, make_reference, paginate, utcnow
from app.services.health_aggregation_service import ACTIVE_EMERGENCY_STATES, PRESENT_STATES
from app.services.supply_request_service import OPEN_REQUEST_STATES, SupplyRequestService

STATUS_FLOW = {
    "ACKNOWLEDGED": {EmergencyStatus.PENDING},
    "RESPONSE_STARTED": {EmergencyStatus.ACKNOWLEDGED, EmergencyStatus.PENDING},
    "IN_PROGRESS": {EmergencyStatus.RESPONSE_STARTED, EmergencyStatus.ACKNOWLEDGED, EmergencyStatus.ESCALATED},
    "CLOSED": {EmergencyStatus.RESOLVED},
}
TASK_FLOW = {
    "ACCEPTED": {EmergencyTaskStatus.OPEN},
    "IN_PROGRESS": {EmergencyTaskStatus.OPEN, EmergencyTaskStatus.ACCEPTED},
    "COMPLETED": {EmergencyTaskStatus.ACCEPTED, EmergencyTaskStatus.IN_PROGRESS, EmergencyTaskStatus.OPEN},
    "CANCELLED": {EmergencyTaskStatus.OPEN, EmergencyTaskStatus.ACCEPTED, EmergencyTaskStatus.IN_PROGRESS},
}
ESCALATION_LEVEL = {
    "DISTRICT_HEALTH_OFFICER": GovernanceLevel.DISTRICT,
    "DISTRICT_SUPPLY_OFFICER": GovernanceLevel.DISTRICT,
    "STATE_HEALTH_ADMIN": GovernanceLevel.STATE,
    "STATE_SUPPLY_MANAGER": GovernanceLevel.STATE,
}
PRIORITY_MAP = {"LOW": ActionPriority.LOW, "MODERATE": ActionPriority.MEDIUM, "HIGH": ActionPriority.HIGH,
                "CRITICAL": ActionPriority.CRITICAL, "UNASSIGNED": ActionPriority.HIGH}
OPEN_TASKS = {EmergencyTaskStatus.OPEN, EmergencyTaskStatus.ACCEPTED, EmergencyTaskStatus.IN_PROGRESS}


class EmergencyService(AuditMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _facility_in(self, facility_id: uuid.UUID, state: str, district: str) -> Facility:
        f = await self.session.get(Facility, facility_id)
        if not f:
            raise ResourceNotFoundException("Facility", str(facility_id))
        if f.state.lower() != state.lower() or f.district.lower() != district.lower():
            raise PermissionDeniedException(f"Facility '{f.name}' is outside the emergency's district.")
        return f

    def _visible(self, stmt, j: Jurisdiction, actor_id: uuid.UUID):
        if j.is_facility_bound:
            affected = select(EmergencyAffectedFacility.incident_id).where(EmergencyAffectedFacility.facility_id == j.facility_id)
            return stmt.where(or_(EmergencyIncident.reported_by == actor_id, EmergencyIncident.id.in_(affected)))
        return j.filter(stmt, EmergencyIncident.state, EmergencyIncident.district)

    async def _note(self, inc: EmergencyIncident, actor_id: uuid.UUID, old: Optional[EmergencyStatus], note: str):
        self.session.add(EmergencyUpdate(incident_id=inc.id, actor_id=actor_id, from_status=old.value if old else None,
                                         to_status=inc.status.value, note=note))

    # ------------------------------------------------------------------ incidents
    async def report(self, data: EmergencyCreate, j: Jurisdiction, actor_id: uuid.UUID, ctx: AuditCtx) -> EmergencyIncident:
        if j.scope == ScopeLevel.GLOBAL or j.scope == ScopeLevel.STATE:
            if not data.affected_facility_ids:
                raise BadRequestException("State/national users must name at least one affected facility.")
            first = await self.session.get(Facility, data.affected_facility_ids[0])
            if not first:
                raise ResourceNotFoundException("Facility", str(data.affected_facility_ids[0]))
            j.ensure_covers(first.state)
            state, district = first.state, first.district
        else:
            state, district = j.state, j.district
        inc = EmergencyIncident(
            reference=make_reference("EMG"), state=state, district=district, emergency_type=data.emergency_type,
            title=data.title, description=data.description, affected_area=data.affected_area, source=data.source,
            reported_by=actor_id, status=EmergencyStatus.PENDING, started_at=utcnow(),
        )
        self.session.add(inc)
        await self.session.flush()
        for fid in dict.fromkeys(data.affected_facility_ids):
            f = await self._facility_in(fid, state, district)
            if j.is_facility_bound and f.id != j.facility_id:
                raise PermissionDeniedException("PHC users can only report their own facility as affected.")
            self.session.add(EmergencyAffectedFacility(incident_id=inc.id, facility_id=f.id))
        await self._note(inc, actor_id, None, f"Emergency reported by {data.source}.")
        await self.session.flush()
        await self._audit("EMERGENCY_REPORTED", "emergency_incident", inc.id, actor_id, ctx,
                          new_state={"reference": inc.reference, "type": data.emergency_type.value, "district": district})
        return await self.get(inc.id, j, actor_id)

    async def list(self, j: Jurisdiction, actor_id: uuid.UUID, status: Optional[EmergencyStatus], active_only: bool,
                   page: int, page_size: int):
        stmt = self._visible(select(EmergencyIncident), j, actor_id)
        if status:
            stmt = stmt.where(EmergencyIncident.status == status)
        elif active_only:
            stmt = stmt.where(EmergencyIncident.status.in_(ACTIVE_EMERGENCY_STATES))
        return await paginate(self.session, stmt, EmergencyIncident.started_at.desc(), page, page_size)

    async def get(self, incident_id: uuid.UUID, j: Jurisdiction, actor_id: uuid.UUID) -> EmergencyIncident:
        stmt = self._visible(
            select(EmergencyIncident).where(EmergencyIncident.id == incident_id).options(
                selectinload(EmergencyIncident.affected_facilities), selectinload(EmergencyIncident.tasks),
                selectinload(EmergencyIncident.escalations), selectinload(EmergencyIncident.updates),
            ).execution_options(populate_existing=True), j, actor_id)
        inc = (await self.session.execute(stmt)).scalar_one_or_none()
        if not inc:
            raise ResourceNotFoundException("EmergencyIncident", str(incident_id))
        return inc

    def _ensure_active(self, inc: EmergencyIncident) -> None:
        if inc.status in (EmergencyStatus.RESOLVED, EmergencyStatus.CLOSED):
            raise BadRequestException(f"Emergency is {inc.status.value}; coordination actions are closed.")

    async def update_status(self, incident_id, data: EmergencyStatusUpdate, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        allowed = STATUS_FLOW[data.status]
        if inc.status not in allowed:
            raise BadRequestException(f"Cannot move emergency from {inc.status.value} to {data.status}.")
        old = inc.status
        inc.status = EmergencyStatus(data.status)
        if data.status == "ACKNOWLEDGED" or (inc.acknowledged_at is None and data.status == "RESPONSE_STARTED"):
            inc.acknowledged_at = utcnow()
            inc.coordinator_id = inc.coordinator_id or actor_id
        await self._note(inc, actor_id, old, data.note)
        await self.session.flush()
        await self._audit(f"EMERGENCY_{data.status}", "emergency_incident", inc.id, actor_id, ctx,
                          old_state={"status": old.value}, new_state={"status": inc.status.value})
        return await self.get(inc.id, j, actor_id)

    async def set_priority(self, incident_id, data: EmergencyPrioritySet, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        old = inc.priority
        inc.priority = data.priority
        inc.priority_set_by = actor_id
        await self._note(inc, actor_id, inc.status, f"Priority set to {data.priority.value} by authorized user: {data.reason}")
        await self.session.flush()
        await self._audit("EMERGENCY_PRIORITY_SET", "emergency_incident", inc.id, actor_id, ctx,
                          old_state={"priority": old.value}, new_state={"priority": data.priority.value, "reason": data.reason})
        return await self.get(inc.id, j, actor_id)

    async def resolve(self, incident_id, data: EmergencyResolve, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        open_tasks = [t for t in inc.tasks if t.status in OPEN_TASKS]
        if open_tasks:
            raise ConflictException(f"{len(open_tasks)} emergency task(s) are still open; complete or cancel them first.")
        old = inc.status
        inc.status = EmergencyStatus.RESOLVED
        inc.resolved_at = utcnow()
        inc.resolution_confirmed_by = actor_id
        inc.resolution_summary = f"{data.resolution_summary}\nConfirmation: {data.confirmation_reference}"
        await self._note(inc, actor_id, old, f"Resolved (confirmation {data.confirmation_reference}).")
        await self.session.flush()
        await self._audit("EMERGENCY_RESOLVED", "emergency_incident", inc.id, actor_id, ctx,
                          old_state={"status": old.value},
                          new_state={"status": inc.status.value, "confirmation": data.confirmation_reference})
        return await self.get(inc.id, j, actor_id)

    async def upsert_affected(self, incident_id, data: AffectedFacilityUpsert, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        f = await self._facility_in(data.facility_id, inc.state, inc.district)
        row = next((a for a in inc.affected_facilities if a.facility_id == f.id), None)
        if row:
            row.service_disruption, row.notes = data.service_disruption, data.notes
        else:
            self.session.add(EmergencyAffectedFacility(incident_id=inc.id, facility_id=f.id,
                                                       service_disruption=data.service_disruption, notes=data.notes))
        await self._note(inc, actor_id, inc.status, f"{f.name}: service disruption {data.service_disruption}.")
        await self.session.flush()
        await self._audit("EMERGENCY_AFFECTED_FACILITY_SET", "emergency_incident", inc.id, actor_id, ctx,
                          facility_id=f.id, new_state={"service_disruption": data.service_disruption})
        return await self.get(inc.id, j, actor_id)

    # ------------------------------------------------------------------ tasks
    async def create_task(self, incident_id, data: EmergencyTaskCreate, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        if data.facility_id:
            await self._facility_in(data.facility_id, inc.state, inc.district)
        if data.assigned_user_id:
            user = await self.session.get(User, data.assigned_user_id)
            if not user or not user.is_active or not user.facility_id:
                raise BadRequestException("Assigned user must be an active staff member with a facility.")
            await self._facility_in(user.facility_id, inc.state, inc.district)
        self.session.add(EmergencyTask(incident_id=inc.id, facility_id=data.facility_id, assigned_role=data.assigned_role,
                                       assigned_user_id=data.assigned_user_id, description=data.description,
                                       created_by=actor_id))
        if inc.status in (EmergencyStatus.PENDING, EmergencyStatus.ACKNOWLEDGED):
            old = inc.status
            inc.status = EmergencyStatus.RESPONSE_STARTED
            inc.acknowledged_at = inc.acknowledged_at or utcnow()
            inc.coordinator_id = inc.coordinator_id or actor_id
            await self._note(inc, actor_id, old, "Response started with first coordination task.")
        await self.session.flush()
        await self._audit("EMERGENCY_TASK_CREATED", "emergency_incident", inc.id, actor_id, ctx,
                          new_state={"assigned_role": data.assigned_role, "assigned_user": str(data.assigned_user_id)})
        return await self.get(inc.id, j, actor_id)

    async def update_task(self, task_id: uuid.UUID, data: EmergencyTaskUpdate, j, actor_id, can_manage: bool,
                          ctx) -> EmergencyIncident:
        task = await self.session.get(EmergencyTask, task_id)
        if not task:
            raise ResourceNotFoundException("EmergencyTask", str(task_id))
        is_assignee = task.assigned_user_id == actor_id
        if not can_manage and not is_assignee:
            raise PermissionDeniedException("Only the coordinator or the assigned staff member can update this task.")
        inc = await self.get(task.incident_id, j if can_manage else _open_view(), actor_id)
        self._ensure_active(inc)
        if task.status not in TASK_FLOW[data.status]:
            raise BadRequestException(f"Cannot move task from {task.status.value} to {data.status}.")
        old = task.status
        task.status = EmergencyTaskStatus(data.status)
        if data.status in ("COMPLETED", "CANCELLED"):
            task.completion_note = data.note
            task.completed_at = utcnow()
        await self._note(inc, actor_id, inc.status, f"Task '{task.description[:60]}' {old.value} → {data.status}: {data.note}")
        await self.session.flush()
        await self._audit(f"EMERGENCY_TASK_{data.status}", "emergency_task", task.id, actor_id, ctx,
                          old_state={"status": old.value}, new_state={"status": data.status})
        return await self.get(inc.id, j if can_manage else _open_view(), actor_id)

    # ------------------------------------------------------------------ escalation & supply
    async def escalate(self, incident_id, data: EmergencyEscalationCreate, j, actor_id, ctx) -> EmergencyIncident:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        level = ESCALATION_LEVEL[data.to_role]
        action = GovernanceAction(
            reference=make_reference("ACT"), level=level, state=inc.state,
            district=inc.district, category="EMERGENCY_ESCALATION",
            title=f"Emergency {inc.reference}: {inc.title}", description=data.reason,
            priority=PRIORITY_MAP[inc.priority.value], status=ActionStatus.PENDING,
            assigned_role=data.to_role, created_by=actor_id, source_reference=inc.reference,
        )
        self.session.add(action)
        await self.session.flush()
        self.session.add(GovernanceActionUpdate(action_id=action.id, actor_id=actor_id,
                                                update_type=ActionUpdateType.ESCALATION,
                                                to_status=ActionStatus.PENDING.value,
                                                note=f"Escalated from emergency {inc.reference}: {data.reason}"))
        self.session.add(EmergencyEscalation(incident_id=inc.id, from_role="DISTRICT_EMERGENCY_COORDINATOR",
                                             to_role=data.to_role, reason=data.reason, escalated_by=actor_id,
                                             governance_action_id=action.id))
        old = inc.status
        inc.status = EmergencyStatus.ESCALATED
        await self._note(inc, actor_id, old, f"Escalated to {data.to_role}: {data.reason}")
        await self.session.flush()
        await self._audit("EMERGENCY_ESCALATED", "emergency_incident", inc.id, actor_id, ctx,
                          new_state={"to_role": data.to_role, "action": action.reference})
        return await self.get(inc.id, j, actor_id)

    async def request_resources(self, incident_id, data: EmergencyResourceRequestCreate, j, actor_id, ctx) -> SupplyRequest:
        inc = await self.get(incident_id, j, actor_id)
        self._ensure_active(inc)
        if not any(a.facility_id == data.facility_id for a in inc.affected_facilities):
            raise BadRequestException("Resources can only be requested for a facility affected by this emergency.")
        req = await SupplyRequestService(self.session).create(
            SupplyRequestCreate(requesting_facility_id=data.facility_id, medication_id=data.medication_id,
                                requested_quantity=data.quantity, priority=data.priority,
                                reason=f"[Emergency {inc.reference}] {data.reason}", emergency_incident_id=inc.id),
            j, actor_id, ctx,
        )
        await self._note(inc, actor_id, inc.status, f"Emergency supply request {req.reference} sent to District Supply Chain Officer.")
        await self.session.flush()
        return req

    # ------------------------------------------------------------------ read models
    async def staff_availability(self, incident_id, j, actor_id) -> List[dict]:
        inc = await self.get(incident_id, j, actor_id)
        rows = []
        patient_users = select(Patient.user_id).where(Patient.user_id.is_not(None))
        for a in inc.affected_facilities:
            f = await self.session.get(Facility, a.facility_id)
            assigned = (await self.session.execute(select(func.count(User.id)).where(
                User.facility_id == f.id, User.is_active.is_(True), User.id.not_in(patient_users)))).scalar_one()
            present = (await self.session.execute(
                select(User.id, User.full_name, StaffAttendance.status, StaffAttendance.shift)
                .join(StaffAttendance, StaffAttendance.user_id == User.id)
                .where(StaffAttendance.facility_id == f.id, StaffAttendance.attendance_date == date.today(),
                       StaffAttendance.status.in_(PRESENT_STATES))
            )).all()
            people = []
            for uid, name, status, shift in present:
                roles = (await self.session.execute(select(Role.name).join(UserRole, UserRole.role_id == Role.id)
                                                    .where(UserRole.user_id == uid))).scalars().all()
                people.append({"user_id": uid, "name": name, "roles": list(roles), "attendance": status.value,
                               "shift": shift})
            rows.append({"facility_id": f.id, "facility_name": f.name, "staff_assigned": assigned,
                         "staff_present_today": len(people), "present_staff": people})
        return rows

    async def resource_status(self, incident_id, j, actor_id) -> List[dict]:
        inc = await self.get(incident_id, j, actor_id)
        rows = []
        for a in inc.affected_facilities:
            f = await self.session.get(Facility, a.facility_id)
            available = InventoryItem.quantity_on_hand - InventoryItem.quantity_reserved
            items = (await self.session.execute(
                select(Medication.generic_name, available, InventoryItem.reorder_level)
                .join(Medication, InventoryItem.medication_id == Medication.id)
                .where(InventoryItem.facility_id == f.id, available <= InventoryItem.reorder_level)
            )).all()
            reqs = (await self.session.execute(select(SupplyRequest).where(
                SupplyRequest.requesting_facility_id == f.id, SupplyRequest.emergency_incident_id == inc.id,
            ))).scalars().all()
            rows.append({
                "facility_id": f.id, "facility_name": f.name,
                "low_or_out_items": [{"medicine": n, "available": int(q), "reorder_level": r} for n, q, r in items],
                "open_supply_requests": [{"reference": r.reference, "status": r.status.value,
                                          "requested_quantity": r.requested_quantity} for r in reqs],
            })
        return rows

    async def dashboard(self, j: Jurisdiction, actor_id: uuid.UUID) -> dict:
        base = self._visible(select(EmergencyIncident), j, actor_id).subquery()
        by_status = dict((await self.session.execute(select(base.c.status, func.count()).group_by(base.c.status))).all())
        active_ids = select(base.c.id).where(base.c.status.in_(ACTIVE_EMERGENCY_STATES))
        by_priority = dict((await self.session.execute(
            select(base.c.priority, func.count()).where(base.c.status.in_(ACTIVE_EMERGENCY_STATES)).group_by(base.c.priority)
        )).all())

        async def count(stmt) -> int:
            return (await self.session.execute(stmt)).scalar_one() or 0

        recent, _ = await self.list(j, actor_id, None, True, 1, 5)
        return {
            "as_of": utcnow(), "scope": j.label,
            "active_emergencies": sum(n for s, n in by_status.items() if s in ACTIVE_EMERGENCY_STATES),
            "by_status": {(s.value if hasattr(s, "value") else s): n for s, n in by_status.items()},
            "by_priority": {(p.value if hasattr(p, "value") else p): n for p, n in by_priority.items()},
            "affected_facilities": await count(select(func.count(func.distinct(EmergencyAffectedFacility.facility_id)))
                                               .where(EmergencyAffectedFacility.incident_id.in_(active_ids))),
            "severely_disrupted_facilities": await count(
                select(func.count(func.distinct(EmergencyAffectedFacility.facility_id))).where(
                    EmergencyAffectedFacility.incident_id.in_(active_ids),
                    EmergencyAffectedFacility.service_disruption.in_(["SEVERE", "CLOSED"]))),
            "open_tasks": await count(select(func.count(EmergencyTask.id)).where(
                EmergencyTask.incident_id.in_(active_ids), EmergencyTask.status.in_(OPEN_TASKS))),
            "open_escalations": await count(select(func.count(EmergencyEscalation.id)).where(
                EmergencyEscalation.incident_id.in_(active_ids), EmergencyEscalation.status.in_(["SENT", "ACKNOWLEDGED"]))),
            "emergency_supply_requests_open": await count(select(func.count(SupplyRequest.id)).where(
                SupplyRequest.emergency_incident_id.in_(active_ids), SupplyRequest.status.in_(OPEN_REQUEST_STATES))),
            "recent": recent,
        }


def _open_view() -> Jurisdiction:
    """Assignee access to their own task's incident is authorized by assignment, not geography."""
    return Jurisdiction(ScopeLevel.GLOBAL, None, None, None)
