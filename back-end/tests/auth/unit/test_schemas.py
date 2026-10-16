from datetime import UTC, datetime

from ai_chat.auth.models import User
from ai_chat.auth.schemas import UserRead
from ai_chat.llm import ResponseStyle


def test_user_read_validates_from_model() -> None:
    user = User(
        id="user-1",
        email="person@example.com",
        # A stored row always carries both: `response_style` is `NOT NULL` with
        # a server default, and instructions are nullable but present as `None`.
        instructions="Answer in British English.",
        response_style="concise",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    read = UserRead.model_validate(user)

    assert read.id == "user-1"
    assert read.email == "person@example.com"
    assert read.instructions == "Answer in British English."
    assert read.response_style is ResponseStyle.CONCISE


def test_user_read_carries_no_instructions_as_none() -> None:
    user = User(
        id="user-1",
        email="person@example.com",
        instructions=None,
        response_style="default",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    read = UserRead.model_validate(user)

    assert read.instructions is None
    assert read.response_style is ResponseStyle.DEFAULT
