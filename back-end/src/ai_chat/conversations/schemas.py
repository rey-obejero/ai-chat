import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime


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
