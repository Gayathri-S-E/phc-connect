"""Assistant registry: one isolated configuration per role, one shared engine.

Adding a role assistant = writing one AssistantConfig module and adding it here. Nothing else changes."""
from typing import Dict, List, Optional

from app.ai.base import AssistantConfig
from app.ai.doctor import DOCTOR_ASSISTANT
from app.ai.nurse import NURSE_ASSISTANT
from app.ai.patient import PATIENT_ASSISTANT
from app.api.deps import AuthenticatedUserContext

_ASSISTANTS: Dict[str, AssistantConfig] = {a.key: a for a in (PATIENT_ASSISTANT, DOCTOR_ASSISTANT, NURSE_ASSISTANT)}


def get_assistant(key: str) -> Optional[AssistantConfig]:
    return _ASSISTANTS.get(key.upper())


def assistants_for_user(user: AuthenticatedUserContext) -> List[AssistantConfig]:
    return [a for a in _ASSISTANTS.values() if a.allowed_for(user)]
