from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, false, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ai_chat.llm import ResponseStyle
from ai_chat.shared.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # What the account is called (FR-7, ADR-0045). Never null and never blank
    # for an account the service created: the derivation fills it. The server
    # default is what lets `NOT NULL` be added to a table that already has rows.
    display_name: Mapped[str] = mapped_column(
        String(50), default="", server_default=text("''"), nullable=False
    )
    # Whether the first-run name prompt has been answered (FR-7). Separate from
    # the name, so the prompt can be asked once while the derived name already
    # satisfies "never nameless".
    name_prompt_seen: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    # Standing instructions the assistant is given on every reply (FR-24).
    # Nullable: having none is a state, not an empty string.
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # How replies sound (FR-25). A Python-side default as well as the server
    # default, so a freshly inserted row reads back without a second round trip.
    response_style: Mapped[str] = mapped_column(
        String(16),
        default=ResponseStyle.DEFAULT.value,
        server_default=ResponseStyle.DEFAULT.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
