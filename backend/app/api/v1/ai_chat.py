"""Common AI Foundation endpoints. One set of routes serves every role assistant; access is decided per assistant
by role + permission on the backend (see app/ai/registry.py), never by the URL or by anything in the message."""
import uuid
from typing import List

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.engine import ChatEngine
from app.ai.llm import LLMClient, gemini_configured, get_llm_client
from app.ai.registry import assistants_for_user
from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
)
from app.core.config import settings
from app.schemas.ai_chat import (
    AIAssistantInfo,
    AIChatRequest,
    AIChatResponse,
    AIConversationDetail,
    AIConversationSummary,
    AIMessageView,
    AIPendingActionView,
)
from app.schemas.common import DataResponse

router = APIRouter(prefix="/ai", tags=["Common AI Foundation (role assistants)"])


def _engine(session: AsyncSession, user: AuthenticatedUserContext, ctx: RequestContext, llm: LLMClient) -> ChatEngine:
    return ChatEngine(session, llm, user, ip_address=ctx.ip_address, user_agent=ctx.user_agent)


@router.get("/assistants", response_model=DataResponse[List[AIAssistantInfo]])
async def list_my_assistants(current_user: AuthenticatedUserContext = Depends(get_current_user)):
    """Assistants this account may use (decided by role + permission), with starter questions."""
    configured = gemini_configured()
    return DataResponse(data=[
        AIAssistantInfo(key=a.key, title=a.title, starters=a.starters, configured=configured)
        for a in assistants_for_user(current_user)
    ])


@router.post("/{assistant}/chat", response_model=DataResponse[AIChatResponse])
async def chat(
    assistant: str,
    payload: AIChatRequest,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    result = await _engine(session, current_user, ctx, llm).chat(
        assistant.upper(), payload.message, payload.conversation_id, payload.language)
    return DataResponse(data=AIChatResponse(**result))


@router.get("/{assistant}/conversations", response_model=DataResponse[List[AIConversationSummary]])
async def list_conversations(
    assistant: str,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    rows = await _engine(session, current_user, ctx, llm).list_conversations(assistant.upper())
    return DataResponse(data=[AIConversationSummary.model_validate(r) for r in rows])


@router.get("/conversations/{conversation_id}", response_model=DataResponse[AIConversationDetail])
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    conv, msgs, pending = await _engine(session, current_user, ctx, llm).get_conversation(conversation_id)
    return DataResponse(data=AIConversationDetail(
        conversation=AIConversationSummary.model_validate(conv),
        messages=[AIMessageView.model_validate(m) for m in msgs],
        pending_actions=[
            AIPendingActionView(id=a.id, tool=a.tool_name, summary=a.summary, status=a.status.value, expires_at=a.expires_at)
            for a in pending
        ],
    ))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    await _engine(session, current_user, ctx, llm).delete_conversation(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/actions/{action_id}/confirm", response_model=DataResponse[AIPendingActionView])
async def confirm_action(
    action_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    """The only path that changes data on the assistant's behalf: explicit, single-use, same user, re-authorised."""
    data = await _engine(session, current_user, ctx, llm).confirm_action(action_id)
    return DataResponse(data=AIPendingActionView(**data))


@router.post("/actions/{action_id}/cancel", response_model=DataResponse[AIPendingActionView])
async def cancel_action(
    action_id: uuid.UUID,
    current_user: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    ctx: RequestContext = Depends(get_request_context),
    llm: LLMClient = Depends(get_llm_client),
):
    data = await _engine(session, current_user, ctx, llm).cancel_action(action_id)
    return DataResponse(data=AIPendingActionView(**data))
