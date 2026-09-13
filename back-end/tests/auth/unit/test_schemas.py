from datetime import UTC, datetime

from ai_chat.auth.models import User
from ai_chat.auth.schemas import UserRead


def test_user_read_validates_from_model() -> None:
    user = User(
        id="user-1",
        email="person@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    read = UserRead.model_validate(user)

    assert read.id == "user-1"
    assert read.email == "person@example.com"
