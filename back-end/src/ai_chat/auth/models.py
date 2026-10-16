from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ai_chat.llm import ResponseStyle
from ai_chat.shared.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
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
