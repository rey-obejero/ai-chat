from collections.abc import AsyncIterator, Sequence
from typing import Protocol, runtime_checkable

from ai_chat.llm.schemas import ChatChunk, ChatMessage


@runtime_checkable
class ChatProvider(Protocol):
    """The only surface the app needs from an LLM vendor.

    Keeps the vendor behind a thin boundary so it can be swapped in one place,
    the same way ``auth.port`` isolates SuperTokens.
    """

    def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
    ) -> AsyncIterator[ChatChunk]:
        """Yield assistant output as the provider produces it."""
        ...
