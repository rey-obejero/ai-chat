import uuid

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_chat.auth import get_current_user_id
from ai_chat.conversations.models import ASSISTANT_ROLE, USER_ROLE, Conversation, Message
from ai_chat.conversations.schemas import (
    ConversationRead,
    MessageCreate,
    MessageEdit,
    MessageRead,
    MessageRegenerate,
)
from ai_chat.conversations.service import (
    add_message,
    begin_generation,
    create_conversation,
    find_message_by_client_id,
    find_owned_message,
    get_owned_conversation,
    get_owned_message,
    list_conversations,
    list_messages,
    replace_content,
    truncate_after,
)
from ai_chat.conversations.streaming import (
    build_history,
    replay_reply,
    stream_reply,
)
from ai_chat.llm import ChatProvider, get_chat_provider
from ai_chat.shared.config import Settings
from ai_chat.shared.db import get_session, get_session_factory
from ai_chat.shared.exceptions import (
    ConversationBusyError,
    InvalidOperationError,
    NotFoundError,
)
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
    request: Request,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    provider: ChatProvider = Depends(get_chat_provider),
    _quota: None = Depends(enforce_quota),
) -> StreamingResponse:
    """Persist the user turn, then stream the assistant reply as SSE."""
    conversation = await get_owned_conversation(session, user_id, conversation_id)
    existing = await find_message_by_client_id(
        session, conversation.id, payload.client_id, role=USER_ROLE
    )
    if existing is not None:
        replayed = await _already_written_response(session, conversation, existing)
        if replayed is not None:
            return replayed
        # The first attempt's user turn landed but its reply never did, so this
        # streams one without writing the message twice.

    await begin_generation(session, conversation, settings=_settings(request))
    if existing is None:
        try:
            await add_message(
                session,
                conversation,
                role=USER_ROLE,
                content=payload.content,
                client_id=payload.client_id,
            )
        except IntegrityError:
            # The key landed between our lookup and the insert. The write is a
            # no-op: hand back the stored reply, or report the writer that holds
            # the gate (H2, H3).
            await session.rollback()
            landed = await find_message_by_client_id(
                session, conversation.id, payload.client_id, role=USER_ROLE
            )
            replayed = (
                await _already_written_response(session, conversation, landed)
                if landed is not None
                else None
            )
            if replayed is None:
                raise ConversationBusyError(detail="A reply is already being generated.") from None
            return replayed
    else:
        # Nothing to insert, but the claim still has to be committed before the
        # stream starts: it is held across connections, not across this session.
        await session.commit()

    return await _stream_response(
        session,
        conversation,
        request=request,
        user_id=user_id,
        session_factory=session_factory,
        provider=provider,
        # The send's key names its user turn; the reply it triggers is not keyed.
        client_id=None,
    )


@router.post("/{conversation_id}/messages/{message_id}/edit")
async def edit_message(
    conversation_id: uuid.UUID,
    message_id: str,
    payload: MessageEdit,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    provider: ChatProvider = Depends(get_chat_provider),
    _quota: None = Depends(enforce_quota),
) -> StreamingResponse:
    """Rewrite a user turn, drop everything after it, then stream a new reply.

    The turn is addressed either by its server uuid — what ``GET /messages``
    returns — or, for a turn sent in this session, by the key its send used
    (``client_id``); a client-owned local id in the path is simply ignored.
    Either way ``client_id`` is the write's key, so a retried edit replays the
    reply it already produced instead of spending tokens again (H3).
    """
    conversation = await get_owned_conversation(session, user_id, conversation_id)

    # The reply is looked up before the target: a retry carries the same key,
    # and replaying it must not depend on the turn still being resolvable (H3).
    existing = await find_message_by_client_id(
        session, conversation.id, payload.client_id, role=ASSISTANT_ROLE
    )
    if existing is not None:
        replayed = await _already_written_response(session, conversation, existing)
        if replayed is not None:
            return replayed

    message = await _resolve_user_turn(session, conversation, message_id, payload.client_id)

    await begin_generation(session, conversation, settings=_settings(request))
    await replace_content(session, message, payload.content)
    await truncate_after(session, conversation, message)
    await session.commit()

    return await _stream_response(
        session,
        conversation,
        request=request,
        user_id=user_id,
        session_factory=session_factory,
        provider=provider,
        client_id=payload.client_id,
    )


@router.post("/{conversation_id}/messages/{message_id}/regenerate")
async def regenerate_message(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    request: Request,
    payload: MessageRegenerate | None = Body(default=None),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
    provider: ChatProvider = Depends(get_chat_provider),
    _quota: None = Depends(enforce_quota),
) -> StreamingResponse:
    """Delete an assistant turn and everything after it, then stream a new reply."""
    conversation = await get_owned_conversation(session, user_id, conversation_id)
    client_id = payload.client_id if payload is not None else None

    # Look the key up before the target: a retry names a message the first
    # attempt deleted, so resolving it first would 404 a write that landed (H3).
    existing = await find_message_by_client_id(
        session, conversation.id, client_id, role=ASSISTANT_ROLE
    )
    if existing is not None:
        replayed = await _already_written_response(session, conversation, existing)
        if replayed is not None:
            return replayed

    message = await get_owned_message(session, conversation, message_id)
    if message.role != ASSISTANT_ROLE:
        raise InvalidOperationError(detail="Only assistant messages can be regenerated.")

    await begin_generation(session, conversation, settings=_settings(request))
    await truncate_after(session, conversation, message, include=True)
    await session.commit()

    return await _stream_response(
        session,
        conversation,
        request=request,
        user_id=user_id,
        session_factory=session_factory,
        provider=provider,
        client_id=client_id,
    )


def _settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def _resolve_user_turn(
    session: AsyncSession,
    conversation: Conversation,
    message_id: str,
    client_id: uuid.UUID | None,
) -> Message:
    """The user turn an edit targets, by server uuid or by the key its send used.

    The uuid wins when it names a message of this conversation, so a path that
    is one still means exactly that row — including the 409 when that row is not
    a user's. A path that is the client's own local id resolves nothing and
    falls through to the key.
    """
    identifier = _as_uuid(message_id)
    if identifier is not None:
        message = await find_owned_message(session, conversation, identifier)
        if message is not None:
            if message.role != USER_ROLE:
                raise InvalidOperationError(detail="Only user messages can be edited.")
            return message

    message = await find_message_by_client_id(session, conversation.id, client_id, role=USER_ROLE)
    if message is None:
        raise NotFoundError(detail="Message not found.")
    return message


def _as_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


async def _stream_response(
    session: AsyncSession,
    conversation: Conversation,
    *,
    request: Request,
    user_id: str,
    session_factory: async_sessionmaker[AsyncSession],
    provider: ChatProvider,
    client_id: uuid.UUID | None,
) -> StreamingResponse:
    """The one SSE shape every streaming route shares, gate and disconnect included."""
    history = build_history(await list_messages(session, conversation.id))
    return StreamingResponse(
        stream_reply(
            provider=provider,
            conversation_id=conversation.id,
            user_id=user_id,
            history=history,
            session_factory=session_factory,
            client_id=client_id,
            is_disconnected=request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )


async def _already_written_response(
    session: AsyncSession, conversation: Conversation, existing: Message
) -> StreamingResponse | None:
    """Replay the reply a retried write already produced, when there is one (H3).

    ``None`` means the message landed but no reply followed it, so the caller
    should carry on and stream one.
    """
    reply = existing
    if reply.role != ASSISTANT_ROLE:
        messages = await list_messages(session, conversation.id)
        for index, row in enumerate(messages):
            if row.id == existing.id:
                following = messages[index + 1] if index + 1 < len(messages) else None
                reply = following or existing
                break
        if reply.role != ASSISTANT_ROLE:
            return None
    return StreamingResponse(
        replay_reply(reply), media_type="text/event-stream", headers=STREAM_HEADERS
    )
