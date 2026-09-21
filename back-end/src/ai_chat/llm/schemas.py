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


class ChatChunk(BaseModel):
    """A streamed fragment of an assistant reply.

    An empty ``content`` with a ``finish_reason`` is a terminal event.
    """

    content: str = ""
    finish_reason: str | None = None
