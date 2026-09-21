"""Conversation and message persistence. Domain rules live here, not in routes."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_chat.conversations.models import Conversation, Message
from ai_chat.shared.exceptions import NotFoundError

DEFAULT_TITLE = "New conversation"
_TITLE_MAX_LENGTH = 60


async def create_conversation(session: AsyncSession, user_id: str) -> Conversation:
    conversation = Conversation(user_id=user_id)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def list_conversations(session: AsyncSession, user_id: str) -> Sequence[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc(), Conversation.id)
    )
    return result.scalars().all()


async def get_owned_conversation(
    session: AsyncSession, user_id: str, conversation_id: uuid.UUID
) -> Conversation:
    """Load a conversation, hiding other users' existence behind a 404."""
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise NotFoundError(detail="Conversation not found.")
    return conversation


async def list_messages(session: AsyncSession, conversation_id: uuid.UUID) -> Sequence[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    )
    return result.scalars().all()


async def add_message(
    session: AsyncSession, conversation: Conversation, *, role: str, content: str
) -> Message:
    """Persist one message, naming the conversation after its first user turn."""
    message = Message(conversation_id=conversation.id, role=role, content=content)
    session.add(message)
    if role == "user" and conversation.title == DEFAULT_TITLE:
        conversation.title = _derive_title(content)
    await session.commit()
    await session.refresh(message)
    return message


def _derive_title(content: str) -> str:
    first_line = content.strip().splitlines()[0].strip() if content.strip() else ""
    return first_line[:_TITLE_MAX_LENGTH] or DEFAULT_TITLE
