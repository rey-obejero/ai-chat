from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """One turn in a conversation, as the provider sees it."""

    role: Role
    content: str


class TokenUsage(BaseModel):
    """Provider-reported token counts for one completion (ADR-0024)."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChunk(BaseModel):
    """A streamed fragment of an assistant reply.

    An empty ``content`` with a ``finish_reason`` is a terminal event. ``usage``
    rides the provider's final chunk and is absent until then.
    """

    content: str = ""
    finish_reason: str | None = None
    usage: TokenUsage | None = None
