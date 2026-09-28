import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException
from app.models.facility import Facility
from app.models.identity import ScopeLevel


async def check_scope_access(
    current_user,
    target_facility_id: Optional[uuid.UUID],
    permission_code: str,
    session: AsyncSession,
    target_patient_user_id: Optional[uuid.UUID] = None,
) -> bool:
    """
    Enforces the complete authorization chain:
    User -> Role -> Permission -> Scope -> Resource (Facility / District / State / Self)
    """
    # 1. Citizen Self-access (if accessing own patient record)
    if target_patient_user_id is not None and target_patient_user_id == current_user.id:
        return True

    # 2. Check permission presence
    if not current_user.has_permission(permission_code):
        raise PermissionDeniedException(f"Missing required permission: '{permission_code}'")

    # 3. Resolve effective scope level for this permission
    scope = current_user.get_highest_scope(permission_code)

    # 4. GLOBAL scope: unrestricted access across all facilities
    if scope == ScopeLevel.GLOBAL:
        return True

    # 5. SELF scope: restricted strictly to personal records
    if scope == ScopeLevel.SELF:
        if target_patient_user_id is not None and target_patient_user_id == current_user.id:
            return True
        raise PermissionDeniedException("Access denied: Your account is restricted to your own personal records.")

    # For FACILITY, DISTRICT, and STATE scopes, target_facility_id is required
    if target_facility_id is None:
        return True

    # 6. FACILITY scope: restricted to user's assigned facility
    if scope == ScopeLevel.FACILITY:
        if current_user.facility_id is None or current_user.facility_id != target_facility_id:
            raise PermissionDeniedException(
                "Cross-facility access denied: Your authorized scope is restricted to your assigned health facility."
            )
        return True

    # 7. DISTRICT and STATE scopes: verify administrative boundaries
    if current_user.facility_id is None:
        raise PermissionDeniedException("User must be associated with an active facility to exercise district or state scope.")

    user_facility = await session.get(Facility, current_user.facility_id)
    target_facility = await session.get(Facility, target_facility_id)

    if not user_facility or not target_facility:
        raise PermissionDeniedException("Facility context could not be verified for geographic scope.")

    if scope == ScopeLevel.DISTRICT:
        if (
            user_facility.state.strip().lower() != target_facility.state.strip().lower()
            or user_facility.district.strip().lower() != target_facility.district.strip().lower()
        ):
            raise PermissionDeniedException(
                f"District scope denied: Facility '{target_facility.name}' is outside your authorized district '{user_facility.district}'."
            )
        return True

    if scope == ScopeLevel.STATE:
        if user_facility.state.strip().lower() != target_facility.state.strip().lower():
            raise PermissionDeniedException(
                f"State scope denied: Facility '{target_facility.name}' is outside your authorized state '{user_facility.state}'."
            )
        return True

    return True
