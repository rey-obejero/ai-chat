import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.auth import get_current_user_id
from ai_chat.conversations.schemas import ConversationRead, MessageRead
from ai_chat.conversations.service import (
    create_conversation,
    get_owned_conversation,
    list_conversations,
    list_messages,
)
from ai_chat.shared.db import get_session

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
