import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func

from app.core.exceptions import PermissionDeniedException
from app.models.identity import ScopeLevel


def norm(value: Optional[str]) -> Optional[str]:
    return value.strip().lower() if value else None


@dataclass
class Jurisdiction:
    """Geographic boundary derived server-side from the user's facility and role scope.

    state/district of None mean "not restricted at this level" (GLOBAL = national view).
    """
    scope: ScopeLevel
    state: Optional[str]
    district: Optional[str]
    facility_id: Optional[uuid.UUID]

    @property
    def label(self) -> str:
        if self.scope == ScopeLevel.GLOBAL:
            return "NATIONAL"
        if self.scope == ScopeLevel.STATE:
            return f"STATE:{self.state}"
        if self.scope == ScopeLevel.DISTRICT:
            return f"DISTRICT:{self.state}/{self.district}"
        return f"FACILITY:{self.facility_id}"

    @property
    def is_facility_bound(self) -> bool:
        return self.scope in (ScopeLevel.FACILITY, ScopeLevel.SELF)

    def covers(self, state: Optional[str], district: Optional[str] = None) -> bool:
        if self.scope == ScopeLevel.GLOBAL:
            return True
        if norm(self.state) != norm(state):
            return False
        if self.scope == ScopeLevel.STATE:
            return True
        return norm(self.district) == norm(district)

    def ensure_covers(self, state: Optional[str], district: Optional[str] = None) -> None:
        if not self.covers(state, district):
            where = f"{district}, {state}" if district else f"{state}"
            raise PermissionDeniedException(f"'{where}' is outside your authorized jurisdiction ({self.label}).")

    def filter(self, stmt, state_col, district_col=None):
        """Restrict a SELECT to this jurisdiction using case-insensitive state/district columns."""
        if self.scope == ScopeLevel.GLOBAL:
            return stmt
        stmt = stmt.where(func.lower(func.trim(state_col)) == norm(self.state))
        if self.scope != ScopeLevel.STATE and district_col is not None:
            stmt = stmt.where(func.lower(func.trim(district_col)) == norm(self.district))
        return stmt
