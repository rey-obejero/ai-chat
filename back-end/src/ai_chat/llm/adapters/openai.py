"""Chat provider over any OpenAI-compatible API (OpenRouter by default)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from ai_chat.llm.exceptions import LLMProviderError
from ai_chat.llm.schemas import ChatChunk, ChatMessage


class OpenAIChatProvider:
    """``ChatProvider`` backed by the OpenAI SDK.

    The client is injected rather than built here so tests can supply a fake
    without an HTTP layer; SuperTokens-style vendor isolation is preserved by
    the ``ChatProvider`` port.
    """

    def __init__(
        self,
        client: AsyncOpenAI,
        *,
        model: str,
        max_output_tokens: int | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._max_output_tokens = max_output_tokens

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
    ) -> AsyncIterator[ChatChunk]:
        payload: dict[str, Any] = {
            "model": model or self._model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": True,
        }
        if self._max_output_tokens is not None:
            payload["max_tokens"] = self._max_output_tokens

        try:
            stream = await self._client.chat.completions.create(**payload)
            async for event in stream:
                chunk = _to_chunk(event)
                if chunk is not None:
                    yield chunk
        except OpenAIError as exc:
            raise LLMProviderError(detail="The language model provider failed.") from exc


def _to_chunk(event: Any) -> ChatChunk | None:
    """Translate one SDK stream event; return None for events with no payload."""
    choices = getattr(event, "choices", None)
    if not choices:
        return None
    choice = choices[0]
    delta = getattr(choice, "delta", None)
    content = getattr(delta, "content", None) or ""
    finish_reason = getattr(choice, "finish_reason", None)
    if not content and finish_reason is None:
        return None
    return ChatChunk(content=content, finish_reason=finish_reason)
