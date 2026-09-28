import uuid
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.models.facility import Facility
from app.models.organization import Organization
from app.repositories.audit_repository import AuditRepository
from app.repositories.facility_repository import FacilityRepository
from app.schemas.facility import FacilityCreate, FacilityUpdate, OrganizationCreate


class FacilityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.facility_repo = FacilityRepository(session)
        self.audit_repo = AuditRepository(session)

    async def create_organization(
        self,
        data: OrganizationCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Organization:
        existing = await self.facility_repo.get_organization_by_code(data.code)
        if existing:
            raise ConflictException(f"Organization with code '{data.code}' already exists.")

        org = Organization(
            name=data.name,
            code=data.code,
            org_type=data.org_type,
            is_active=True,
        )
        await self.facility_repo.create_organization(org)

        await self.audit_repo.record_event(
            action="ORGANIZATION_CREATED",
            resource_type="organization",
            resource_id=str(org.id),
            actor_id=actor_id,
            organization_id=org.id,
            new_state={"code": org.code, "name": org.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return org

    async def list_organizations(self) -> Sequence[Organization]:
        return await self.facility_repo.list_organizations()

    async def create_facility(
        self,
        data: FacilityCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Facility:
        org = await self.facility_repo.get_organization_by_id(data.organization_id)
        if not org:
            raise ResourceNotFoundException("Organization", str(data.organization_id))

        existing = await self.facility_repo.get_facility_by_code(data.code)
        if existing:
            raise ConflictException(f"Facility with code '{data.code}' already exists.")

        fac = Facility(
            organization_id=data.organization_id,
            name=data.name,
            code=data.code,
            facility_type=data.facility_type,
            state=data.state,
            district=data.district,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            is_active=True,
        )
        await self.facility_repo.create_facility(fac)

        await self.audit_repo.record_event(
            action="FACILITY_CREATED",
            resource_type="facility",
            resource_id=str(fac.id),
            actor_id=actor_id,
            organization_id=fac.organization_id,
            facility_id=fac.id,
            new_state={"code": fac.code, "name": fac.name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return fac

    async def get_facility(self, facility_id: uuid.UUID) -> Facility:
        fac = await self.facility_repo.get_facility_by_id(facility_id)
        if not fac:
            raise ResourceNotFoundException("Facility", str(facility_id))
        return fac

    async def update_facility(
        self,
        facility_id: uuid.UUID,
        data: FacilityUpdate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Facility:
        fac = await self.get_facility(facility_id)
        changes = data.model_dump(exclude_unset=True)
        old_state = {k: getattr(fac, k) for k in changes}
        for field, value in changes.items():
            setattr(fac, field, value)
        await self.session.flush()

        await self.audit_repo.record_event(
            action="FACILITY_UPDATED",
            resource_type="facility",
            resource_id=str(fac.id),
            actor_id=actor_id,
            organization_id=fac.organization_id,
            facility_id=fac.id,
            old_state={k: v if isinstance(v, (str, bool, type(None))) else str(v) for k, v in old_state.items()},
            new_state={k: v if isinstance(v, (str, bool, type(None))) else str(v) for k, v in changes.items()},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return fac

    async def list_facilities(
        self,
        organization_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
    ) -> Sequence[Facility]:
        return await self.facility_repo.list_facilities(organization_id=organization_id, district=district)
