"""Streams an assistant reply and persists it, in the AI SDK wire format."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_chat.conversations.models import Message
from ai_chat.llm import ChatMessage, ChatProvider, LLMProviderError, Role
from ai_chat.shared import streaming as sse

logger = logging.getLogger(__name__)

ASSISTANT_ROLE = "assistant"


def build_history(messages: Sequence[Message]) -> list[ChatMessage]:
    return [ChatMessage(role=Role(message.role), content=message.content) for message in messages]


async def stream_reply(
    *,
    provider: ChatProvider,
    conversation_id: uuid.UUID,
    history: Sequence[ChatMessage],
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[str]:
    """Yield stream parts for one reply, persisting it when it completes.

    A failure mid-stream is reported as an ``error`` part rather than an
    exception, because the response status has already been committed by then.
    """
    message_id = uuid.uuid4()
    text_id = f"text_{uuid.uuid4().hex}"
    collected: list[str] = []

    yield sse.start(str(message_id))
    yield sse.text_start(text_id)

    try:
        async for chunk in provider.stream_chat(history):
            if chunk.content:
                collected.append(chunk.content)
                yield sse.text_delta(text_id, chunk.content)
    except LLMProviderError:
        logger.warning("Provider failed for conversation %s", conversation_id, exc_info=True)
        yield sse.error("The language model provider failed.")
        yield sse.DONE
        return
    except Exception:
        logger.exception("Unexpected streaming failure for conversation %s", conversation_id)
        yield sse.error("The reply could not be completed.")
        yield sse.DONE
        return

    yield sse.text_end(text_id)

    content = "".join(collected)
    if content:
        try:
            await _persist_assistant_message(session_factory, message_id, conversation_id, content)
        except Exception:
            logger.exception("Failed to persist the reply for conversation %s", conversation_id)
            yield sse.error("The reply could not be saved.")
            yield sse.DONE
            return

    yield sse.finish()
    yield sse.DONE


async def _persist_assistant_message(
    session_factory: async_sessionmaker[AsyncSession],
    message_id: uuid.UUID,
    conversation_id: uuid.UUID,
    content: str,
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
            )
        )
        await session.commit()
