import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ai_chat.conversations.models import TITLE_MAX_LENGTH


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    is_pinned: bool
    is_favourite: bool
    is_archived: bool
    created_at: datetime
    last_activity_at: datetime


class ConversationPage(BaseModel):
    """One page of the conversation list (FR-11).

    `next_cursor` is opaque and resumes the list after the last item; `None`
    means this was the last page.
    """

    items: list[ConversationRead]
    next_cursor: str | None


class ConversationUpdate(BaseModel):
    """A partial update: only the fields sent change (FR-11, FR-16, FR-17)."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    is_pinned: bool | None = None
    is_favourite: bool | None = None
    is_archived: bool | None = None

    @field_validator("title", "is_pinned", "is_favourite", "is_archived", mode="before")
    @classmethod
    def _reject_null(cls, value: object, info: ValidationInfo) -> object:
        # A field is absent or it carries a value. An explicit `null` is a
        # client bug, not a partial update, so it is rejected rather than
        # silently treated as "leave it alone".
        if value is None:
            raise ValueError(f"{info.field_name} may not be null; omit it instead.")
        return value

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title must not be blank")
        if len(cleaned) > TITLE_MAX_LENGTH:
            raise ValueError(f"title must be at most {TITLE_MAX_LENGTH} characters")
        return cleaned


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    # A client-generated key for one logical write (ADR-0050, H3). Retrying a
    # send with the same key cannot duplicate the message.
    client_id: uuid.UUID | None = None


class MessageEdit(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    # The key of the turn being edited — the one its send used, echoed by
    # `MessageRead.client_id`. A live turn has no server uuid yet (the client
    # owns its id), so the key is what addresses it; it doubles as the write's
    # idempotency key, because a retried edit carries the same turn.
    client_id: uuid.UUID | None = None


class MessageRegenerate(BaseModel):
    client_id: uuid.UUID | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    # So a restored turn is addressable by the same key a live one is.
    client_id: uuid.UUID | None
