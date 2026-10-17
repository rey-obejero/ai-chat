import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ai_chat.conversations.models import TITLE_MAX_LENGTH


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    # The conversation's own model choice, or `None` for the deployment default
    # (FR-23). It is the stored choice, not the effective model: a stored id the
    # deployment stopped serving is reported as it is and replaced on the next
    # reply, where the replacement is disclosed (M5).
    model: str | None
    is_pinned: bool
    is_favourite: bool
    is_archived: bool
    created_at: datetime
    last_activity_at: datetime


class ConversationCreate(BaseModel):
    """A new conversation, optionally pinned to a served model (FR-23)."""

    model_config = ConfigDict(extra="forbid")

    model: str | None = None


class ConversationPage(BaseModel):
    """One page of the conversation list (FR-11).

    `next_cursor` is opaque and resumes the list after the last item; `None`
    means this was the last page.
    """

    items: list[ConversationRead]
    next_cursor: str | None


class ConversationUpdate(BaseModel):
    """A partial update: only the fields sent change (FR-11, FR-16, FR-17, FR-23)."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    model: str | None = None
    is_pinned: bool | None = None
    is_favourite: bool | None = None
    is_archived: bool | None = None

    @field_validator("title", "model", "is_pinned", "is_favourite", "is_archived", mode="before")
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
    # A client-generated key for one logical write (ADR-0052, H3). Retrying a
    # send with the same key cannot duplicate the message.
    client_id: uuid.UUID | None = None


class MessageEdit(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    # This attempt's own key, so a retried edit replays the reply it already
    # produced instead of generating a second one (H3). Minting a fresh key per
    # attempt is what makes a later edit of the same turn a new edit rather than
    # that replay.
    client_id: uuid.UUID | None = None
    # The turn being edited: the key its send used, echoed by
    # `MessageRead.client_id`. A live turn has no server uuid yet (the client
    # owns its id), so this is what addresses it when the path cannot.
    target_client_id: uuid.UUID | None = None


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
