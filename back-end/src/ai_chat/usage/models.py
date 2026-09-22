"""One row per completed reply — a ledger, not a running total (ADR-0024)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from ai_chat.shared.db import Base


class TokenUsage(Base):
    __tablename__ = "token_usage"
    # Enforcement sums a user's rows for the current period; the composite
    # index keeps that a single range scan.
    __table_args__ = (Index("ix_token_usage_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.id", ondelete="CASCADE"))
    # Kept for the audit trail; a conversation can be deleted without losing
    # the spend it already cost.
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
