from ai_chat.auth import get_current_user_id
from ai_chat.auth.models import User
from ai_chat.chat.models import Conversation


async def test_conversations_are_isolated_per_user(app, client, session_factory) -> None:
    async def current_user() -> str:
        return "user-1"

    app.dependency_overrides[get_current_user_id] = current_user

    async with session_factory() as session:
        session.add_all(
            [
                User(id="user-1", email="one@example.com"),
                User(id="user-2", email="two@example.com"),
                Conversation(user_id="user-1", title="Mine"),
                Conversation(user_id="user-2", title="Theirs"),
            ]
        )
        await session.commit()

    response = await client.get("/api/v1/conversations")

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["Mine"]
