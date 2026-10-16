"""The limiter must sit *outside* SuperTokens to see an auth request (issue 0012).

SuperTokens answers `/api/auth/*` itself and returns without calling the wrapped
app, so a limiter beneath it never runs. Starlette treats the last-added
middleware as outermost; this file pins that ordering down, because the mistake
is invisible until it is under load.
"""

import httpx
from limits import parse

from ai_chat.main import create_app
from ai_chat.shared.config import Settings
from ai_chat.shared.rate_limit import RateLimitMiddleware


def _per_minute(rule: str) -> int:
    """The rule's amount; every default rule is stated per minute."""
    return parse(rule).amount


class _SentinelMiddleware:
    """Stands in for the SuperTokens middleware, which needs a running core."""

    def __init__(self, app, *args, **kwargs) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        await self.app(scope, receive, send)


def _patch_supertokens(monkeypatch) -> None:
    import ai_chat.auth.adapter_supertokens as supertokens_adapter

    monkeypatch.setattr(supertokens_adapter, "init_supertokens", lambda settings: None)
    monkeypatch.setattr(supertokens_adapter, "supertokens_middleware", lambda: _SentinelMiddleware)


def test_the_limiter_is_added_after_supertokens(monkeypatch) -> None:
    _patch_supertokens(monkeypatch)

    app = create_app(Settings(_env_file=None, rate_limit_enabled=True), init_auth=True)

    classes = [middleware.cls for middleware in app.user_middleware]
    # Index 0 is outermost; it must be the limiter, not SuperTokens.
    assert classes[0] is RateLimitMiddleware
    assert classes.index(RateLimitMiddleware) < classes.index(_SentinelMiddleware)


def test_default_rules_cover_auth_and_the_mail_endpoints() -> None:
    rules = Settings(_env_file=None).rate_limit_rules

    assert "/api/auth" in rules
    assert "/api/auth/user/password/reset" in rules
    assert "/api/auth/user/email/verify/token" in rules
    # Both endpoints that send a message are throttled harder than sign-in, so
    # neither a reset request nor a verification resend can ride the blanket
    # auth prefix; the longest matching prefix is the only rule that counts.
    assert _per_minute(rules["/api/auth/user/password/reset"]) < _per_minute(rules["/api/auth"])
    assert _per_minute(rules["/api/auth/user/email/verify/token"]) < _per_minute(rules["/api/auth"])


async def test_an_auth_endpoint_returns_429_with_retry_after() -> None:
    settings = Settings(
        _env_file=None,
        rate_limit_enabled=True,
        rate_limit_rules={"/api/auth": "1/minute"},
    )
    app = create_app(settings, init_auth=False)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/api/auth/signin")
        second = await client.post("/api/auth/signin")

    # The first request is counted, then reaches the router (no auth route is
    # mounted with init_auth=False); the second is refused before routing.
    assert first.status_code != 429
    assert second.status_code == 429
    assert second.headers["content-type"] == "application/problem+json"
    assert int(second.headers["retry-after"]) >= 1
