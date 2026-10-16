from ai_chat.auth import get_current_user_id, get_email_verified
from ai_chat.llm import TokenUsage
from ai_chat.usage import service


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


def _email_verified(app, *, verified: bool) -> None:
    async def override() -> bool:
        return verified

    app.dependency_overrides[get_email_verified] = override


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
    _email_verified(quota_app, verified=True)
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


async def test_usage_route_reports_the_reduced_allowance_when_unverified(
    quota_app, quota_client, session_factory
) -> None:
    # The figure the next reply is checked against, not the one the account
    # cannot reach yet (FR-4) — otherwise the budget shown is a lie.
    _current_user(quota_app)
    _email_verified(quota_app, verified=False)
    async with session_factory() as session:
        await service.record(
            session, user_id="user-1", conversation_id=None, usage=TokenUsage(total_tokens=400)
        )

    response = await quota_client.get("/api/v1/usage")

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 500
    assert body["remaining"] == 100
