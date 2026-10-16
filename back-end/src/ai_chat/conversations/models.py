import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from ai_chat.shared.db import Base

USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="New conversation")
    # Set while a stream holds this conversation's one-generation gate; cleared
    # in the stream's `finally`. A set-but-stale value expires after
    # `stream_grace_seconds` so a crashed worker cannot wedge the conversation.
    generating_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Message(Base):
    __tablename__ = "messages"
    # Structural idempotency (ADR-0050): a retried write carries the same
    # client-generated key and hits this constraint instead of duplicating a row.
    # The key names one logical turn, so it is scoped by role: an edit keys its
    # reply with the key of the user turn it rewrites, which is what makes a
    # retried edit recognisable without a second key.
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "role",
            "client_id",
            name="uq_messages_conversation_role_client_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    # A Python-side default as well as the server default: Postgres timestamps
    # are microsecond-precise but SQLite's are not, and ordering a conversation
    # depends on insert order being recoverable in both.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
