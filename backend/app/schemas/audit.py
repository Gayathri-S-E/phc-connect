import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    facility_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
