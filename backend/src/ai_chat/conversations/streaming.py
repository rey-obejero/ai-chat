"""Streams an assistant reply and persists it, in the AI SDK wire format."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from datetime import UTC, datetime

import anyio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_chat.conversations import service
from ai_chat.conversations.models import ASSISTANT_ROLE, Message
from ai_chat.llm import ChatMessage, ChatProvider, LLMProviderError, Role, TokenUsage
from ai_chat.shared import streaming as sse
from ai_chat.usage import record

logger = logging.getLogger(__name__)


def build_history(messages: Sequence[Message]) -> list[ChatMessage]:
    return [ChatMessage(role=Role(message.role), content=message.content) for message in messages]


def with_system_prompt(
    history: Sequence[ChatMessage], system_prompt: str | None
) -> list[ChatMessage]:
    """The account's prompt as the first message the provider sees.

    It leads rather than follows because a provider that honours only one system
    message would otherwise drop it in favour of whatever caption the transcript
    last held; leading also keeps the instructions away from the turns they
    shape. Nothing is prepended when the account has asked for nothing.
    """
    if not system_prompt:
        return list(history)
    return [ChatMessage(role=Role.SYSTEM, content=system_prompt), *history]


async def replay_reply(message: Message) -> AsyncIterator[str]:
    """Re-emit an already-persisted reply, so a retried write is invisible (H3)."""
    text_id = f"text_{message.id.hex}"
    yield sse.start(str(message.id))
    yield sse.text_start(text_id)
    if message.content:
        yield sse.text_delta(text_id, message.content)
    yield sse.text_end(text_id)
    yield sse.finish()
    yield sse.DONE


async def stream_reply(
    *,
    provider: ChatProvider,
    conversation_id: uuid.UUID,
    user_id: str,
    history: Sequence[ChatMessage],
    model: str,
    session_factory: async_sessionmaker[AsyncSession],
    system_prompt: str | None = None,
    client_id: uuid.UUID | None = None,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
) -> AsyncIterator[str]:
    """Yield stream parts for one reply, persisting it when it completes.

    ``model`` is the conversation's effective model and ``system_prompt`` the
    account's composed instructions; both are resolved by the route, because
    both come from stored state the route has already read.

    A failure mid-stream is reported as an ``error`` part rather than an
    exception, because the response status has already been committed by then.

    A client disconnect (Stop, a closed tab, a dropped connection) stops the
    provider stream, keeps whatever was produced, and always clears the
    conversation's generation gate (H4).
    """
    message_id = uuid.uuid4()
    # When this stream began. The reply is stamped with it rather than with the
    # moment it happened to finish, so a write that lands mid-stream — a model
    # switch's caption is the one that does — sorts after the answer it
    # interrupted instead of in front of it, claiming an answer it did not make.
    started_at = datetime.now(UTC)
    text_id = f"text_{uuid.uuid4().hex}"
    collected: list[str] = []
    usage: TokenUsage | None = None
    # A partial is kept when the reader vanishes mid-reply; it is dropped when
    # the provider or the write failed, because the client hears about that
    # through an `error` part instead.
    keep_partial = True
    chunks = provider.stream_chat(with_system_prompt(history, system_prompt), model=model)

    try:
        yield sse.start(str(message_id))
        yield sse.text_start(text_id)

        disconnected = False
        try:
            async for chunk in chunks:
                if is_disconnected is not None and await is_disconnected():
                    disconnected = True
                    break
                if chunk.usage is not None:
                    usage = chunk.usage
                if chunk.content:
                    collected.append(chunk.content)
                    yield sse.text_delta(text_id, chunk.content)
        except LLMProviderError:
            keep_partial = False
            logger.warning("Provider failed for conversation %s", conversation_id, exc_info=True)
            yield sse.error("The language model provider failed.")
            yield sse.DONE
            return
        except Exception:
            keep_partial = False
            logger.exception("Unexpected streaming failure for conversation %s", conversation_id)
            yield sse.error("The reply could not be completed.")
            yield sse.DONE
            return

        if disconnected:
            # Nobody is left to read an error part, so stop spending here and
            # let the `finally` store the partial as the reply (H4).
            if usage is not None:
                await _record_usage_quietly(
                    session_factory, user_id=user_id, conversation_id=conversation_id, usage=usage
                )
            return

        yield sse.text_end(text_id)

        content = "".join(collected)
        if content:
            try:
                await _persist_assistant_message(
                    session_factory, message_id, conversation_id, content, started_at, client_id
                )
            except Exception:
                keep_partial = False
                logger.exception("Failed to persist the reply for conversation %s", conversation_id)
                yield sse.error("The reply could not be saved.")
                yield sse.DONE
                return
            keep_partial = False

        if usage is not None:
            await _record_usage_quietly(
                session_factory, user_id=user_id, conversation_id=conversation_id, usage=usage
            )

        yield sse.finish()
        yield sse.DONE
    finally:
        # Shielded: the client's disconnect cancels this task, and the provider
        # still has to be stopped, the partial stored, and the gate cleared.
        with anyio.CancelScope(shield=True):
            await _aclose(chunks)
            if keep_partial:
                await _persist_partial(
                    session_factory, message_id, conversation_id, collected, started_at, client_id
                )
            await _clear_gate(session_factory, conversation_id)


async def _aclose(chunks: object) -> None:
    """Cancel the provider stream, whichever async-iterator shape it is."""
    close = getattr(chunks, "aclose", None)
    if close is None:
        return
    try:
        await close()
    except Exception:
        logger.exception("Failed to close the provider stream")


async def _persist_partial(
    session_factory: async_sessionmaker[AsyncSession],
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    collected: Sequence[str],
    started_at: datetime,
    client_id: uuid.UUID | None,
) -> None:
    """Keep the text produced before a disconnect; the tokens are spent anyway."""
    content = "".join(collected)
    if not content:
        return
    try:
        await _persist_assistant_message(
            session_factory, message_id, conversation_id, content, started_at, client_id
        )
    except Exception:
        logger.exception("Failed to keep the partial reply for conversation %s", conversation_id)


async def _record_usage_quietly(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: str,
    conversation_id: uuid.UUID,
    usage: TokenUsage,
) -> None:
    try:
        await _record_usage(
            session_factory,
            user_id=user_id,
            conversation_id=conversation_id,
            usage=usage,
        )
    except Exception:
        # The tokens are already spent; accounting must not fail a reply
        # that has otherwise succeeded.
        logger.exception("Failed to record usage for conversation %s", conversation_id)


async def _clear_gate(
    session_factory: async_sessionmaker[AsyncSession], conversation_id: uuid.UUID
) -> None:
    try:
        async with session_factory() as session:
            await service.end_generation(session, conversation_id)
    except Exception:
        logger.exception("Failed to clear the generation gate for conversation %s", conversation_id)


async def _persist_assistant_message(
    session_factory: async_sessionmaker[AsyncSession],
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    content: str,
    started_at: datetime,
    client_id: uuid.UUID | None = None,
) -> None:
    # The request-scoped session is already closed by the time the body streams,
    # so this opens its own short-lived one.
    async with session_factory() as session:
        session.add(
            Message(
                id=message_id,
                conversation_id=conversation_id,
                role=ASSISTANT_ROLE,
                content=content,
                created_at=started_at,
                client_id=client_id,
            )
        )
        try:
            # Flushed before the stamp, so a write that cannot land (a duplicate
            # key, or a conversation deleted mid-stream) fails here and is
            # handled below, rather than surfacing from `touch_activity`.
            await session.flush()
            # The reply is the conversation's most recent activity, so the list
            # still orders by the last thing said.
            await service.touch_activity(session, conversation_id)
            await session.commit()
        except IntegrityError:
            # Either the same logical write already landed (H3), or the
            # conversation was deleted while this reply streamed and the row has
            # nothing left to belong to (ADR-0052). The client has the text
            # either way, so this is not an error part.
            await session.rollback()
            logger.info("Reply for conversation %s was not stored", conversation_id)


async def _record_usage(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: str,
    conversation_id: uuid.UUID,
    usage: TokenUsage,
) -> None:
    """Append one reply's spend to the ledger, whether or not its conversation stands.

    A delete is deliberately not gated (ADR-0052), so the conversation can be gone
    by the time a reply completes — and then the row this write names no longer
    exists, which the foreign key refuses. The tokens were spent either way, and
    the ledger is the record of that: the spend lands against no conversation
    rather than not at all.
    """
    try:
        async with session_factory() as session:
            await record(session, user_id=user_id, conversation_id=conversation_id, usage=usage)
    except IntegrityError:
        async with session_factory() as session:
            await record(session, user_id=user_id, conversation_id=None, usage=usage)
