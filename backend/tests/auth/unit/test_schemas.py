from datetime import UTC, datetime

from ai_chat.auth.models import User
from ai_chat.auth.schemas import UserRead
from ai_chat.llm import ResponseStyle


def test_user_read_validates_from_model() -> None:
    user = User(
        id="user-1",
        email="person@example.com",
        # A stored row always carries all four: the name, the prompt flag and
        # `response_style` are `NOT NULL` with server defaults, and instructions
        # are nullable but present as `None`.
        display_name="Amara Okafor",
        name_prompt_seen=True,
        instructions="Answer in British English.",
        response_style="concise",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    read = UserRead.model_validate(user)

    assert read.id == "user-1"
    assert read.email == "person@example.com"
    assert read.display_name == "Amara Okafor"
    assert read.name_prompt_seen is True
    assert read.instructions == "Answer in British English."
    assert read.response_style is ResponseStyle.CONCISE


def test_user_read_carries_no_instructions_as_none() -> None:
    user = User(
        id="user-1",
        email="person@example.com",
        display_name="Amara Okafor",
        name_prompt_seen=False,
        instructions=None,
        response_style="default",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    read = UserRead.model_validate(user)

    assert read.instructions is None
    assert read.response_style is ResponseStyle.DEFAULT
    # The name is present whether or not the prompt has been answered.
    assert read.display_name == "Amara Okafor"
    assert read.name_prompt_seen is False
