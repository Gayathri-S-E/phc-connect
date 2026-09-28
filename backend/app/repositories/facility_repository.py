import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility
from app.models.organization import Organization


class FacilityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_organization_by_id(self, org_id: uuid.UUID) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.id == org_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_organization_by_code(self, code: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_organization(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        return organization

    async def list_organizations(self) -> Sequence[Organization]:
        stmt = select(Organization).where(Organization.is_active.is_(True)).order_by(Organization.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_facility_by_id(self, facility_id: uuid.UUID) -> Optional[Facility]:
        stmt = select(Facility).where(Facility.id == facility_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_facility_by_code(self, code: str) -> Optional[Facility]:
        stmt = select(Facility).where(Facility.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_facility(self, facility: Facility) -> Facility:
        self.session.add(facility)
        await self.session.flush()
        return facility

    async def list_facilities(
        self,
        organization_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
    ) -> Sequence[Facility]:
        stmt = select(Facility).where(Facility.is_active.is_(True))
        if organization_id:
            stmt = stmt.where(Facility.organization_id == organization_id)
        if district:
            stmt = stmt.where(Facility.district == district)
        stmt = stmt.order_by(Facility.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
