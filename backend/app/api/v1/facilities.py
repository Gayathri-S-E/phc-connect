import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, RequestContext, get_current_user, get_db_session, get_request_context, require_permission
from app.core.permissions import SystemPermissions
from app.schemas.common import DataResponse
from app.schemas.facility import FacilityCreate, FacilityResponse, FacilityUpdate, OrganizationCreate, OrganizationResponse
from app.services.facility_service import FacilityService

router = APIRouter(tags=["Facilities & Organizations"])


@router.get("/organizations", response_model=DataResponse[List[OrganizationResponse]])
async def list_organizations(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List all registered health authorities, ministries, and district offices."""
    service = FacilityService(session)
    orgs = await service.list_organizations()
    return DataResponse(data=[OrganizationResponse.model_validate(o) for o in orgs])


@router.post(
    "/organizations",
    response_model=DataResponse[OrganizationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_FACILITY_MANAGE))],
)
async def create_organization(
    payload: OrganizationCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Provision a new organization or administrative health division."""
    service = FacilityService(session)
    org = await service.create_organization(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=OrganizationResponse.model_validate(org))


@router.get("/facilities", response_model=DataResponse[List[FacilityResponse]])
async def list_facilities(
    organization_id: Optional[uuid.UUID] = Query(None),
    district: Optional[str] = Query(None),
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List operational facilities (PHCs, CHCs, Warehouses) filtered by organization or district."""
    service = FacilityService(session)
    facilities = await service.list_facilities(organization_id=organization_id, district=district)
    return DataResponse(data=[FacilityResponse.model_validate(f) for f in facilities])


@router.post(
    "/facilities",
    response_model=DataResponse[FacilityResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_FACILITY_MANAGE))],
)
async def create_facility(
    payload: FacilityCreate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Provision a new Primary Health Centre (PHC) or supply warehouse."""
    service = FacilityService(session)
    fac = await service.create_facility(
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=FacilityResponse.model_validate(fac))


@router.get("/facilities/{facility_id}", response_model=DataResponse[FacilityResponse])
async def get_facility(
    facility_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed profile and coordinates of a facility."""
    service = FacilityService(session)
    fac = await service.get_facility(facility_id)
    return DataResponse(data=FacilityResponse.model_validate(fac))


@router.patch(
    "/facilities/{facility_id}",
    response_model=DataResponse[FacilityResponse],
    dependencies=[Depends(require_permission(SystemPermissions.IDENTITY_FACILITY_MANAGE))],
)
async def update_facility(
    facility_id: uuid.UUID,
    payload: FacilityUpdate,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Update facility operational metadata."""
    service = FacilityService(session)
    fac = await service.update_facility(
        facility_id,
        payload,
        actor_id=current_user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return DataResponse(data=FacilityResponse.model_validate(fac))
