import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ai_chat.shared.db import Base

USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
# A transcript-level notice rather than a turn: today it is the model-switch
# caption (FR-23), which the interface renders as a centred caption and the
# provider receives as a system message.
SYSTEM_ROLE = "system"

# The column's width and the rename rule's limit are the same number.
TITLE_MAX_LENGTH = 255


class Conversation(Base):
    __tablename__ = "conversations"
    # One index carries the list's sort key — pinned first, then most recently
    # active — and a trigram index makes the `ILIKE '%term%'` search over the
    # title a search rather than a scan (migration 0005).
    __table_args__ = (
        Index("ix_conversations_user_last_activity", "user_id", text("last_activity_at DESC")),
        Index(
            "ix_conversations_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), default="New conversation")
    # The model this conversation's replies go to (FR-23). Nullable: without a
    # choice the deployment's default applies, which is the picker's "Auto".
    # The value is checked against the served list at request time, never here
    # — the list is configuration and can change under a stored row (M5).
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # The three presentation states (FR-17). Each changes only how the list
    # shows a row, so each is a plain flag rather than a date or a status enum.
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    is_favourite: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    # Denormalized time of the last message, stamped by `touch_activity`. The
    # list orders by it: `created_at` cannot answer "what did I answer last",
    # which is what resuming a conversation must do (FR-11).
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    # Set while a stream holds this conversation's one-generation gate; cleared
    # in the stream's `finally`. A set-but-stale value expires after
    # `stream_grace_seconds` so a crashed worker cannot wedge the conversation.
    generating_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Message(Base):
    __tablename__ = "messages"
    # Structural idempotency (ADR-0052): a retried write carries the same
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
        # Search is a substring match over the transcript too, and it is the
        # larger table; the trigram index keeps it from becoming a full scan.
        Index(
            "ix_messages_content_trgm",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_trgm_ops"},
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
