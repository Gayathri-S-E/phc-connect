import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)  # the tighter limit is enforced in the safety layer
    conversation_id: Optional[uuid.UUID] = None
    language: Optional[str] = Field(default=None, max_length=5)


class AIPendingActionView(BaseModel):
    id: uuid.UUID
    tool: str
    summary: str
    status: str
    expires_at: datetime
    result: Optional[Dict[str, Any]] = None
    already_completed: Optional[bool] = None
    message: Optional[str] = None


class AIChatResponse(BaseModel):
    conversation_id: uuid.UUID
    assistant: str
    answer: str
    language: str
    emergency: bool = False
    refused: bool = False
    sources: List[str] = []
    tools_used: List[str] = []
    pending_action: Optional[AIPendingActionView] = None
    generated_at: datetime


class AIAssistantInfo(BaseModel):
    key: str
    title: str
    starters: Dict[str, List[str]]
    configured: bool


class AIConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assistant: str
    title: str
    language: str
    updated_at: datetime


class AIMessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime


class AIConversationDetail(BaseModel):
    conversation: AIConversationSummary
    messages: List[AIMessageView]
    pending_actions: List[AIPendingActionView]
