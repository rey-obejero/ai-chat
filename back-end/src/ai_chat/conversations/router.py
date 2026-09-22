import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_chat.auth import get_current_user_id
from ai_chat.conversations.schemas import ConversationRead, MessageCreate, MessageRead
from ai_chat.conversations.service import (
    add_message,
    create_conversation,
    get_owned_conversation,
    list_conversations,
    list_messages,
)
from ai_chat.conversations.streaming import build_history, stream_reply
from ai_chat.llm import ChatProvider, get_chat_provider
from ai_chat.shared.db import get_session, get_session_factory
from ai_chat.shared.streaming import STREAM_HEADERS
from ai_chat.usage import enforce_quota

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
async def read_conversations(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    rows = await list_conversations(session, user_id)
    return [ConversationRead.model_validate(row) for row in rows]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def new_conversation(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ConversationRead:
    conversation = await create_conversation(session, user_id)
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def read_messages(
    conversation_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[MessageRead]:
    conversation = await get_owned_conversation(session, user_id, conversation_id)
    rows = await list_messages(session, conversation.id)
    return [MessageRead.model_validate(row) for row in rows]


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    provider: ChatProvider = Depends(get_chat_provider),
    _quota: None = Depends(enforce_quota),
) -> StreamingResponse:
    """Persist the user turn, then stream the assistant reply as SSE."""
    conversation = await get_owned_conversation(session, user_id, conversation_id)
    await add_message(session, conversation, role="user", content=payload.content)
    history = build_history(await list_messages(session, conversation.id))

    events = stream_reply(
        provider=provider,
        conversation_id=conversation.id,
        user_id=user_id,
        history=history,
        session_factory=session_factory,
    )
    return StreamingResponse(events, media_type="text/event-stream", headers=STREAM_HEADERS)
