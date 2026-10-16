"""Streams an assistant reply and persists it, in the AI SDK wire format."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

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
    session_factory: async_sessionmaker[AsyncSession],
    client_id: uuid.UUID | None = None,
    is_disconnected: Callable[[], Awaitable[bool]] | None = None,
) -> AsyncIterator[str]:
    """Yield stream parts for one reply, persisting it when it completes.

    A failure mid-stream is reported as an ``error`` part rather than an
    exception, because the response status has already been committed by then.

    A client disconnect (Stop, a closed tab, a dropped connection) stops the
    provider stream, keeps whatever was produced, and always clears the
    conversation's generation gate (H4).
    """
    message_id = uuid.uuid4()
    text_id = f"text_{uuid.uuid4().hex}"
    collected: list[str] = []
    usage: TokenUsage | None = None
    # A partial is kept when the reader vanishes mid-reply; it is dropped when
    # the provider or the write failed, because the client hears about that
    # through an `error` part instead.
    keep_partial = True
    chunks = provider.stream_chat(history)

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
                    session_factory, message_id, conversation_id, content, client_id
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
                    session_factory, message_id, conversation_id, collected, client_id
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
    client_id: uuid.UUID | None,
) -> None:
    """Keep the text produced before a disconnect; the tokens are spent anyway."""
    content = "".join(collected)
    if not content:
        return
    try:
        await _persist_assistant_message(
            session_factory, message_id, conversation_id, content, client_id
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
                client_id=client_id,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            # The same logical write already landed; keep the stored one (H3).
            await session.rollback()
            logger.info("Duplicate reply write for conversation %s", conversation_id)


async def _record_usage(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: str,
    conversation_id: uuid.UUID,
    usage: TokenUsage,
) -> None:
    async with session_factory() as session:
        await record(session, user_id=user_id, conversation_id=conversation_id, usage=usage)
