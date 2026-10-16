"""Conversation and message persistence. Domain rules live here, not in routes."""

from __future__ import annotations

import base64
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, exists, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ai_chat.conversations.exceptions import InvalidCursorError
from ai_chat.conversations.models import SYSTEM_ROLE, USER_ROLE, Conversation, Message
from ai_chat.llm import default_model, is_served, model_label, validate_model
from ai_chat.shared.config import Settings, get_settings
from ai_chat.shared.exceptions import ConversationBusyError, NotFoundError

DEFAULT_TITLE = "New conversation"
_TITLE_MAX_LENGTH = 60

# A model change is disclosed in the transcript rather than applied silently
# (FR-23): one caption names the new model, the other says why an old choice is
# gone. The wording is content, so it lives here and nowhere else.
MODEL_CAPTION = "Model set to {label}"
UNAVAILABLE_MODEL_CAPTION = "{model} is no longer available; using {label}."

# One page of the list. The sidebar shows no pager today, but the endpoint is
# cursor-paginated, so outgrowing a screenful needs no contract change: one row
# past the page is read to know whether a next page exists.
PAGE_SIZE = 100

# `ILIKE` reads these as wildcards. A literal `%` in a search term must match
# `%`, not everything, so the term is escaped against this character before it
# becomes a pattern.
_LIKE_ESCAPE = "\\"


@dataclass(frozen=True, slots=True)
class ConversationPage:
    """One page of the list, plus the cursor that resumes after it."""

    items: Sequence[Conversation]
    next_cursor: str | None


async def create_conversation(
    session: AsyncSession,
    user_id: str,
    *,
    model: str | None = None,
    settings: Settings | None = None,
) -> Conversation:
    """Open a conversation, optionally on one of the served models (FR-23).

    The choice is validated here rather than in the schema, because what is
    served is configuration and not a fixed list: an id this deployment does
    not serve is refused now, so a conversation never stores one (M5).
    """
    if model is not None:
        validate_model(settings or get_settings(), model)
    conversation = Conversation(user_id=user_id, model=model)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def search_conversations(
    session: AsyncSession,
    user_id: str,
    *,
    query: str | None = None,
    include_archived: bool = False,
    cursor: str | None = None,
    limit: int = PAGE_SIZE,
) -> ConversationPage:
    """The owner's conversations, pinned first then most recently active (FR-11).

    ``query`` is a substring match over the title and the transcript, so it
    works for scripts a word-based index does not tokenize (FR-15). The term is
    escaped and bound, and never logged or stored: the search is stateless.
    ``cursor`` resumes after the last row of the previous page.
    """
    statement = select(Conversation).where(Conversation.user_id == user_id)
    if not include_archived:
        # Archived rows are out of the default list, not gone (FR-17).
        statement = statement.where(Conversation.is_archived.is_(False))

    term = (query or "").strip()
    if term:
        pattern = f"%{_escape_like(term)}%"
        statement = statement.where(
            or_(
                Conversation.title.ilike(pattern, escape=_LIKE_ESCAPE),
                exists(
                    select(Message.id).where(
                        Message.conversation_id == Conversation.id,
                        Message.content.ilike(pattern, escape=_LIKE_ESCAPE),
                    )
                ),
            )
        )

    statement = statement.order_by(
        Conversation.is_pinned.desc(),
        Conversation.last_activity_at.desc(),
        Conversation.id,
    )
    if cursor is not None:
        statement = statement.where(_resumes_after(_decode_cursor(cursor)))

    result = await session.execute(statement.limit(limit + 1))
    rows = result.scalars().all()
    items = rows[:limit]
    return ConversationPage(
        items=items,
        next_cursor=_encode_cursor(items[-1]) if len(rows) > limit and items else None,
    )


def _escape_like(term: str) -> str:
    """Make a search term literal: only `\\`, `%`, and `_` are special to `LIKE`."""
    return (
        term.replace(_LIKE_ESCAPE, _LIKE_ESCAPE * 2)
        .replace("%", f"{_LIKE_ESCAPE}%")
        .replace("_", f"{_LIKE_ESCAPE}_")
    )


def _encode_cursor(conversation: Conversation) -> str:
    """An opaque cursor for the sort key: the pinned tier, then `(last_activity_at, id)`.

    The pinned flag leads because it leads the ordering; without it a page
    boundary inside the pinned tier would re-read or skip rows on the next page.
    """
    raw = (
        f"{int(conversation.is_pinned)}|"
        f"{conversation.last_activity_at.isoformat()}|"
        f"{conversation.id}"
    )
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[bool, datetime, uuid.UUID]:
    """Read a cursor minted by ``_encode_cursor``; anything else is a 400."""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        pinned, activity_at, identifier = (
            base64.urlsafe_b64decode(padded).decode("utf-8").split("|")
        )
        return pinned == "1", datetime.fromisoformat(activity_at), uuid.UUID(identifier)
    except (ValueError, UnicodeDecodeError) as error:
        raise InvalidCursorError(detail="Invalid cursor.") from error


def _resumes_after(keys: tuple[bool, datetime, uuid.UUID]) -> ColumnElement[bool]:
    """Rows strictly after a cursor, in the list's own order (keyset, not offset)."""
    pinned, activity_at, identifier = keys
    later = or_(
        Conversation.last_activity_at < activity_at,
        and_(Conversation.last_activity_at == activity_at, Conversation.id > identifier),
    )
    if pinned:
        # Everything after a pinned row is either a lower pinned row or any
        # unpinned row, because the pinned tier is ordered first as a whole.
        return or_(
            and_(Conversation.is_pinned.is_(True), later),
            Conversation.is_pinned.is_(False),
        )
    return and_(Conversation.is_pinned.is_(False), later)


async def get_owned_conversation(
    session: AsyncSession, user_id: str, conversation_id: uuid.UUID
) -> Conversation:
    """Load a conversation, hiding other users' existence behind a 404."""
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise NotFoundError(detail="Conversation not found.")
    return conversation


async def update_conversation(
    session: AsyncSession,
    conversation: Conversation,
    *,
    title: str | None = None,
    model: str | None = None,
    is_pinned: bool | None = None,
    is_favourite: bool | None = None,
    is_archived: bool | None = None,
    settings: Settings | None = None,
) -> Conversation:
    """Apply a partial update; ``None`` means "leave this field alone".

    Renaming and the three presentation states all land here (FR-11, FR-17).
    None of them is a message, so none of them moves the conversation in the
    activity ordering. A model change is the exception: it writes the caption
    that discloses the switch (FR-23).
    """
    if title is not None:
        conversation.title = title
    if is_pinned is not None:
        conversation.is_pinned = is_pinned
    if is_favourite is not None:
        conversation.is_favourite = is_favourite
    if is_archived is not None:
        conversation.is_archived = is_archived
    if model is not None:
        await change_model(session, conversation, model, settings or get_settings())
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def change_model(
    session: AsyncSession,
    conversation: Conversation,
    model: str,
    settings: Settings,
) -> None:
    """Set a conversation's model, disclosing the change in the transcript.

    A silent switch is structurally impossible: the transcript gains a
    system-role caption naming the new model, so what a reply used stays legible
    after the fact. Saving the model the conversation already has writes
    nothing, so a repeated save is not a repeated caption.
    """
    validate_model(settings, model)
    if conversation.model == model:
        return
    conversation.model = model
    await add_message(
        session,
        conversation,
        role=SYSTEM_ROLE,
        content=MODEL_CAPTION.format(label=model_label(settings, model)),
    )


async def resolve_model(
    session: AsyncSession,
    conversation: Conversation,
    settings: Settings,
) -> str:
    """The model this conversation's next reply goes to (FR-23).

    The stored choice wins for as long as the deployment serves it. A choice it
    no longer serves is never handed to a provider: the default applies, the
    fallback is disclosed like any other change, and it is persisted — so it is
    disclosed once, not on every turn (M5).
    """
    stored = conversation.model
    if stored is not None and is_served(settings, stored):
        return stored

    fallback = default_model(settings)
    if stored is not None:
        conversation.model = fallback
        await add_message(
            session,
            conversation,
            role=SYSTEM_ROLE,
            content=UNAVAILABLE_MODEL_CAPTION.format(
                model=stored, label=model_label(settings, fallback)
            ),
        )
    return fallback


async def delete_conversation(session: AsyncSession, conversation: Conversation) -> None:
    """Delete a conversation and its transcript (FR-16).

    The messages are deleted explicitly rather than left to the foreign key's
    ``ON DELETE CASCADE``: a database that does not enforce foreign keys (the
    test engine, and anything running with them off) would otherwise keep an
    orphaned transcript. The ledger is untouched — a spend already made is kept
    when its conversation goes (ADR-0024).
    """
    await session.execute(
        delete(Message)
        .where(Message.conversation_id == conversation.id)
        .execution_options(synchronize_session=False)
    )
    await session.delete(conversation)
    await session.commit()


async def touch_activity(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> None:
    """Stamp a conversation as active, which is what the list orders by (FR-11).

    One `UPDATE` keyed by id, so it is also the tolerant form: a conversation
    deleted while a stream is running simply matches no row, and the stream's
    bookkeeping still succeeds (ADR-0052). The caller commits, so the stamp
    lands in the same transaction as the message that caused it.
    """
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(last_activity_at=now or datetime.now(UTC))
        .execution_options(synchronize_session="evaluate")
    )


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
    now = datetime.now(UTC)
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        client_id=client_id,
        # Explicit, so the message and the activity stamp it causes are the
        # same instant rather than two reads of the clock.
        created_at=now,
    )
    session.add(message)
    if role == USER_ROLE and conversation.title == DEFAULT_TITLE:
        conversation.title = _derive_title(content)
    await touch_activity(session, conversation.id, now=now)
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
    """Clear the claim once a stream has ended, however it ended (H2, H4).

    The claim lives on the conversation's row, so clearing it is a no-op when
    that row is already gone: deleting a conversation mid-stream cannot leave a
    stream's cleanup failing (ADR-0052).
    """
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
