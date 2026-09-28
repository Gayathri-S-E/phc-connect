import hashlib
import ipaddress
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException, BadRequestException, ConflictException, ResourceNotFoundException
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.models.identity import User, UserSession
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RegisterPatientRequest, TokenResponse


def _hash_token(token: str) -> str:
    """Create SHA-256 hash of refresh token for safe database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _valid_ip(value: str | None) -> str | None:
    # user_sessions.ip_address is INET; X-Forwarded-For is client-controlled.
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    async def authenticate_user(
        self,
        credentials: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Tuple[TokenResponse, User]:
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            # Record audit of failed login attempt
            await self.audit_repo.record_event(
                action="AUTH_LOGIN_FAILED",
                resource_type="user",
                resource_id=credentials.email,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationException("User account is inactive. Please contact support.")

        # Create token pair
        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "email": user.email,
                "org_id": str(user.organization_id) if user.organization_id else None,
                "fac_id": str(user.facility_id) if user.facility_id else None,
            },
        )
        refresh_token = create_refresh_token(subject=user.id)

        # Store hashed refresh token in user_sessions
        session_obj = UserSession(
            user_id=user.id,
            refresh_token_hash=_hash_token(refresh_token),
            user_agent=user_agent,
            ip_address=_valid_ip(ip_address),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.user_repo.create_session(session_obj)

        # Audit successful login
        await self.audit_repo.record_event(
            action="AUTH_LOGIN_SUCCESS",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return (
            TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            user,
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationException("Invalid token type.")
            user_id_str = payload.get("sub")
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise AuthenticationException("Invalid or expired refresh token.")

        token_hash = _hash_token(refresh_token)
        session_obj = await self.user_repo.get_session_by_token_hash(token_hash)
        if not session_obj or session_obj.is_revoked:
            raise AuthenticationException("Refresh token revoked or session expired.")

        expires_at = session_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise AuthenticationException("Refresh token revoked or session expired.")

        # Rotate token: revoke old session
        await self.user_repo.revoke_session(session_obj)

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationException("User account not found or inactive.")

        # Issue new pair
        new_access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "email": user.email,
                "org_id": str(user.organization_id) if user.organization_id else None,
                "fac_id": str(user.facility_id) if user.facility_id else None,
            },
        )
        new_refresh_token = create_refresh_token(subject=user.id)

        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=_hash_token(new_refresh_token),
            user_agent=user_agent,
            ip_address=_valid_ip(ip_address),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.user_repo.create_session(new_session)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, user_id: uuid.UUID, refresh_token: str | None = None) -> None:
        if refresh_token:
            token_hash = _hash_token(refresh_token)
            session_obj = await self.user_repo.get_session_by_token_hash(token_hash)
            if session_obj:
                await self.user_repo.revoke_session(session_obj)

    async def change_password(
        self,
        user: User,
        data: PasswordChangeRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect.")
        if data.current_password == data.new_password:
            raise BadRequestException("New password must differ from the current password.")

        user.hashed_password = get_password_hash(data.new_password)
        await self.user_repo.update(user)
        await self.session.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id, UserSession.is_revoked.is_(False))
            .values(is_revoked=True)
        )

        await self.audit_repo.record_event(
            action="AUTH_PASSWORD_CHANGED",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            organization_id=user.organization_id,
            facility_id=user.facility_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def register_patient(
        self,
        data: RegisterPatientRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists.")

        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            phone_number=data.phone_number,
            is_active=True,
            is_verified=False,
        )
        await self.user_repo.create(user)

        await self.audit_repo.record_event(
            action="PATIENT_USER_REGISTERED",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user
