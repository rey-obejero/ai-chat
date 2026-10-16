"""Conversation and message persistence. Domain rules live here, not in routes."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ai_chat.conversations.models import USER_ROLE, Conversation, Message
from ai_chat.shared.config import Settings, get_settings
from ai_chat.shared.exceptions import ConversationBusyError, NotFoundError

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


async def find_owned_message(
    session: AsyncSession, conversation: Conversation, message_id: uuid.UUID
) -> Message | None:
    """One message of a conversation, or ``None`` when it is not one of them."""
    message = await session.get(Message, message_id)
    if message is None or message.conversation_id != conversation.id:
        return None
    return message


async def get_owned_message(
    session: AsyncSession, conversation: Conversation, message_id: uuid.UUID
) -> Message:
    """Load one message of a conversation, hiding foreign existence behind a 404."""
    message = await find_owned_message(session, conversation, message_id)
    if message is None:
        raise NotFoundError(detail="Message not found.")
    return message


async def find_message_by_client_id(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    client_id: uuid.UUID | None,
    *,
    role: str,
) -> Message | None:
    """The row a retried write already produced, if any (H3).

    The key names one logical turn and is scoped by ``role``: a send keys its
    user turn, an edit keys the reply it produces (with the key of the turn it
    rewrites), a regenerate keys its reply. So a client that reuses one key
    across two turns of a conversation still cannot silence the second write,
    and a lookup never has to guess which row was meant.
    """
    if client_id is None:
        return None
    result = await session.execute(
        select(Message).where(
            Message.conversation_id == conversation_id,
            Message.role == role,
            Message.client_id == client_id,
        )
    )
    return result.scalar_one_or_none()


async def add_message(
    session: AsyncSession,
    conversation: Conversation,
    *,
    role: str,
    content: str,
    client_id: uuid.UUID | None = None,
) -> Message:
    """Persist one message, naming the conversation after its first user turn.

    ``client_id`` makes the write idempotent: the unique constraint on
    ``(conversation_id, client_id)`` rejects a retry with ``IntegrityError``,
    which the route turns into the already-stored reply instead of a duplicate.
    """
    message = Message(
        conversation_id=conversation.id, role=role, content=content, client_id=client_id
    )
    session.add(message)
    if role == USER_ROLE and conversation.title == DEFAULT_TITLE:
        conversation.title = _derive_title(content)
    await session.commit()
    await session.refresh(message)
    return message


async def replace_content(session: AsyncSession, message: Message, content: str) -> None:
    """Rewrite a message in place. The caller commits, so it chooses the unit of work."""
    message.content = content


async def truncate_after(
    session: AsyncSession, conversation: Conversation, message: Message, *, include: bool = False
) -> None:
    """Delete the messages that follow ``message``, and it too when ``include``.

    Later-ness is ``(created_at, id)`` — the same ordering ``list_messages``
    uses — so a rewrite leaves a linear transcript, whatever the clock did.
    """
    await session.execute(
        delete(Message)
        .where(
            Message.conversation_id == conversation.id,
            _follows(message, include=include),
        )
        .execution_options(synchronize_session=False)
    )


def _follows(message: Message, *, include: bool) -> ColumnElement[bool]:
    boundary = Message.id >= message.id if include else Message.id > message.id
    return or_(
        Message.created_at > message.created_at,
        and_(Message.created_at == message.created_at, boundary),
    )


async def begin_generation(
    session: AsyncSession,
    conversation: Conversation,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> None:
    """Atomically claim the conversation for one in-flight stream (H2).

    A single conditional ``UPDATE`` is the check-and-set: two writers cannot
    both win, and a claim older than ``stream_grace_seconds`` is treated as
    abandoned so a crashed worker self-heals. The caller commits, so the claim
    and the first row mutation land in one transaction; a lost race raises
    ``ConversationBusyError`` and leaves nothing behind.
    """
    settings = settings or get_settings()
    now = now or datetime.now(UTC)
    result = await session.execute(
        update(Conversation)
        .where(
            Conversation.id == conversation.id,
            or_(
                Conversation.generating_at.is_(None),
                Conversation.generating_at < now - timedelta(seconds=settings.stream_grace_seconds),
            ),
        )
        .values(generating_at=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        raise ConversationBusyError(detail="A reply is already being generated.")
    conversation.generating_at = now


async def end_generation(session: AsyncSession, conversation_id: uuid.UUID) -> None:
    """Clear the claim once a stream has ended, however it ended (H2, H4)."""
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(generating_at=None)
        .execution_options(synchronize_session=False)
    )
    await session.commit()


def _derive_title(content: str) -> str:
    first_line = content.strip().splitlines()[0].strip() if content.strip() else ""
    return first_line[:_TITLE_MAX_LENGTH] or DEFAULT_TITLE
