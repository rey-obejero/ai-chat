"""The reduced allowance, and the nudge its refusal carries (FR-4, ADR-0039).

The quota dependency refuses the request before the conversation handler runs,
so a conversation that does not exist is enough to see the refusal — and the
problem body is the one the client reads the nudge from.
"""

import uuid

from ai_chat.auth import get_current_user_id, get_email_verified
from ai_chat.llm import ChatChunk, TokenUsage, get_chat_provider
from ai_chat.usage import service


class _StubProvider:
    """The provider the route asks for; the quota refuses before it is used."""

    async def stream_chat(self, _messages, *, model=None):
        yield ChatChunk(content="never sent")


def _current_user(app, user_id: str = "user-1") -> None:
    async def override() -> str:
        return user_id

    app.dependency_overrides[get_current_user_id] = override


def _email_verified(app, *, verified: bool) -> None:
    async def override() -> bool:
        return verified

    app.dependency_overrides[get_email_verified] = override


def _stub_provider(app) -> None:
    app.dependency_overrides[get_chat_provider] = _StubProvider


async def _spend(session_factory, tokens: int) -> None:
    async with session_factory() as session:
        await service.record(
            session, user_id="user-1", conversation_id=None, usage=TokenUsage(total_tokens=tokens)
        )


async def _reply(client):
    return await client.post(
        f"/api/v1/conversations/{uuid.uuid4()}/messages",
        json={"content": "Hello"},
    )


async def test_an_unverified_account_is_blocked_at_half_the_quota(
    quota_app, quota_client, session_factory
) -> None:
    _current_user(quota_app)
    _email_verified(quota_app, verified=False)
    _stub_provider(quota_app)
    await _spend(session_factory, 500)

    response = await _reply(quota_client)

    assert response.status_code == 429
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "QUOTA_EXCEEDED"
    # What turns the plain quota copy into "verify your email" (ADR-0039).
    assert body["verification_required"] is True
    assert body["retry_after"] >= 0


async def test_a_verified_account_is_not_blocked_at_the_same_spend(
    quota_app, quota_client, session_factory
) -> None:
    _current_user(quota_app)
    _email_verified(quota_app, verified=True)
    _stub_provider(quota_app)
    await _spend(session_factory, 500)

    response = await _reply(quota_client)

    # Past the quota and on to the conversation, which is not there.
    assert response.status_code == 404


async def test_a_verified_account_at_the_full_quota_gets_no_verification_nudge(
    quota_app, quota_client, session_factory
) -> None:
    _current_user(quota_app)
    _email_verified(quota_app, verified=True)
    _stub_provider(quota_app)
    await _spend(session_factory, 1000)

    response = await _reply(quota_client)

    assert response.status_code == 429
    body = response.json()
    assert body["code"] == "QUOTA_EXCEEDED"
    assert "verification_required" not in body
