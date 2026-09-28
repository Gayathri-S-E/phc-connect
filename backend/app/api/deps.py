import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AuthenticationException, PermissionDeniedException
from app.core.security import decode_token
from app.models.identity import ScopeLevel, User
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUserContext:
    user: User
    id: uuid.UUID
    email: str
    organization_id: Optional[uuid.UUID]
    facility_id: Optional[uuid.UUID]
    roles: List[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    scope_levels: Dict[str, ScopeLevel] = field(default_factory=dict)
    permission_scopes: Dict[str, List[ScopeLevel]] = field(default_factory=dict)

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.permissions

    def get_highest_scope(self, permission_code: Optional[str] = None) -> ScopeLevel:
        if permission_code and permission_code in self.permission_scopes:
            scopes = self.permission_scopes[permission_code]
        else:
            scopes = list(self.scope_levels.values())

        if not scopes:
            return ScopeLevel.SELF

        priority = [ScopeLevel.GLOBAL, ScopeLevel.STATE, ScopeLevel.DISTRICT, ScopeLevel.FACILITY, ScopeLevel.SELF]
        for p in priority:
            if p in scopes:
                return p
        return ScopeLevel.SELF

    @property
    def scope(self) -> ScopeLevel:
        return self.get_highest_scope()


@dataclass
class RequestContext:
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


async def get_request_context(request: Request) -> RequestContext:
    forwarded = request.headers.get("x-forwarded-for")
    ip_address = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return RequestContext(ip_address=ip_address, user_agent=user_agent)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUserContext:
    if not auth or not auth.credentials:
        raise AuthenticationException("Authorization header with Bearer token is required.")

    try:
        payload = decode_token(auth.credentials)
        if payload.get("type") != "access":
            raise AuthenticationException("Invalid token type. Access token required.")
        user_id_str = payload.get("sub")
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise AuthenticationException("Could not validate credentials or token expired.")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise AuthenticationException("User account not found or deactivated.")

    # Calculate effective roles and permissions from database
    role_names: List[str] = []
    effective_permissions: Set[str] = set()
    scopes: Dict[str, ScopeLevel] = {}
    permission_scopes: Dict[str, List[ScopeLevel]] = {}

    for user_role in user.user_roles:
        role = user_role.role
        if role and role.is_active:
            role_names.append(role.code)
            scopes[role.code] = user_role.scope_level
            for role_perm in role.role_permissions:
                perm = role_perm.permission
                if perm and perm.is_active:
                    effective_permissions.add(perm.code)
                    permission_scopes.setdefault(perm.code, []).append(user_role.scope_level)

    return AuthenticatedUserContext(
        user=user,
        id=user.id,
        email=user.email,
        organization_id=user.organization_id,
        facility_id=user.facility_id,
        roles=role_names,
        permissions=effective_permissions,
        scope_levels=scopes,
        permission_scopes=permission_scopes,
    )



def require_permission(permission_code: str) -> Callable:
    """Enforces dynamic database-driven permission on FastAPI route."""
    async def permission_dependency(
        current_user: AuthenticatedUserContext = Depends(get_current_user),
    ) -> AuthenticatedUserContext:
        if not current_user.has_permission(permission_code):
            raise PermissionDeniedException(
                f"Missing required permission: '{permission_code}'"
            )
        return current_user

    return permission_dependency
