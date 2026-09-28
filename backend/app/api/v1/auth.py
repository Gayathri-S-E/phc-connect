from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext, RequestContext, get_current_user, get_db_session, get_request_context
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterPatientRequest,
    TokenResponse,
)
from app.schemas.common import DataResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=DataResponse[TokenResponse], status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Authenticate credentials and issue JWT access and refresh token pair."""
    service = AuthService(session)
    tokens, _ = await service.authenticate_user(payload, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return DataResponse(data=tokens)


@router.post("/refresh", response_model=DataResponse[TokenResponse], status_code=status.HTTP_200_OK)
async def refresh_tokens(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Rotate refresh token and issue fresh access token."""
    service = AuthService(session)
    tokens = await service.refresh_tokens(payload.refresh_token, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return DataResponse(data=tokens)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: RefreshRequest | None = None,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Revoke session and invalidate tokens."""
    service = AuthService(session)
    refresh_token = payload.refresh_token if payload else None
    await service.logout(current_user.id, refresh_token=refresh_token)
    return {"message": "Successfully logged out."}


@router.post("/register", response_model=DataResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterPatientRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Register citizen/patient portal account."""
    service = AuthService(session)
    user = await service.register_patient(payload, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return DataResponse(data=UserResponse.model_validate(user))


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: PasswordChangeRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """Change password after verifying the current one; all refresh sessions are revoked."""
    service = AuthService(session)
    await service.change_password(current_user.user, payload, ip_address=ctx.ip_address, user_agent=ctx.user_agent)
    return {"message": "Password changed. Please sign in again on other devices."}


@router.get("/me",response_model=DataResponse[CurrentUserResponse], status_code=status.HTTP_200_OK)
async def get_me(
    current_user: AuthenticatedUserContext = Depends(get_current_user),
):
    """Retrieve authenticated user profile, active roles, and granted database permissions."""
    resp = CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.user.full_name,
        phone_number=current_user.user.phone_number,
        organization_id=current_user.organization_id,
        facility_id=current_user.facility_id,
        is_active=current_user.user.is_active,
        is_verified=current_user.user.is_verified,
        roles=current_user.roles,
        permissions=list(current_user.permissions),
    )
    return DataResponse(data=resp)
