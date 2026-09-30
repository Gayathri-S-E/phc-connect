"""Contracts shared by every role assistant.

A role assistant is *configuration*: who may use it, what it may say, and which backend tools it may call.
It never contains its own chat loop, provider client or auth logic (those live in engine.py / llm.py / deps).
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUserContext

IST = timezone(timedelta(hours=5, minutes=30))
SUPPORTED_LANGUAGES = ("en", "ta", "hi")
LANGUAGE_NAMES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}


class ToolError(Exception):
    """A safe-to-show reason a tool could not do what was asked (missing data, not allowed, invalid input)."""


@dataclass
class ToolContext:
    session: AsyncSession
    user: AuthenticatedUserContext
    language: str = "en"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    state: Dict[str, Any] = field(default_factory=dict)  # per-request cache (e.g. the resolved patient)


ToolHandler = Callable[[ToolContext, Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class ToolSpec:
    """`kind='read'`: `handler` returns data. `kind='action'`: `handler` only validates and returns
    {"summary": str, "args": normalized args}; `execute` runs later, only after the user confirms."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: ToolHandler
    source: str  # human-readable label shown to the user as the data source
    permission: Optional[str] = None
    kind: str = "read"
    execute: Optional[ToolHandler] = None

    def declaration(self) -> Dict[str, Any]:
        decl: Dict[str, Any] = {"name": self.name, "description": self.description}
        if self.parameters.get("properties"):
            decl["parameters"] = self.parameters
        return decl


@dataclass
class AssistantConfig:
    key: str
    title: str
    role_codes: frozenset  # the user must hold one of these roles ...
    permission: str  # ... and this permission
    role_prompt: str
    tools: Dict[str, ToolSpec]
    starters: Dict[str, List[str]]
    emergency_guard: bool = False  # patient-facing: short-circuit emergencies before any model call
    context_loader: Optional[Callable[[ToolContext], Awaitable[str]]] = None

    def allowed_for(self, user: AuthenticatedUserContext) -> bool:
        return bool(self.role_codes.intersection(user.roles)) and user.has_permission(self.permission)


def now_ist() -> datetime:
    return datetime.now(IST)


def obj(properties: Optional[Dict[str, Any]] = None, required: Optional[List[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "object", "properties": properties or {}}
    if required:
        schema["required"] = required
    return schema


def parse_uuid(value: Any, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        raise ToolError(f"'{label}' is not a valid identifier. Please pick it from the list I showed you.")
