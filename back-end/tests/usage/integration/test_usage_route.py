from ai_chat.auth import get_current_user_id
from ai_chat.llm import TokenUsage
from ai_chat.usage import service


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


async def test_usage_route_reports_spend_with_the_quota_disabled(
    app, client, session_factory
) -> None:
    _current_user(app)
    async with session_factory() as session:
        await service.record(
            session, user_id="user-1", conversation_id=None, usage=TokenUsage(total_tokens=1234)
        )

    response = await client.get("/api/v1/usage")

    assert response.status_code == 200
    body = response.json()
    assert body["used"] == 1234
    assert body["limit"] is None
    assert body["remaining"] is None
    assert body["period_start"]
    assert body["resets_at"]


async def test_usage_route_reports_the_remaining_budget(
    quota_app, quota_client, session_factory
) -> None:
    _current_user(quota_app)
    async with session_factory() as session:
        await service.record(
            session, user_id="user-1", conversation_id=None, usage=TokenUsage(total_tokens=400)
        )

    response = await quota_client.get("/api/v1/usage")

    assert response.status_code == 200
    body = response.json()
    assert body["used"] == 400
    assert body["limit"] == 1000
    assert body["remaining"] == 600
