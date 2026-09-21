"""Pure-ASGI rate limiting middleware.

Deliberately *not* ``BaseHTTPMiddleware``: that wrapper reconstructs responses
and interferes with streaming, and the next feature is an SSE reply stream
(ADR-0012). This middleware only inspects the request and forwards everything
else untouched.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable, Sequence

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from ai_chat.shared.exceptions import RateLimitedError, problem_body
from ai_chat.shared.rate_limit.limiter import RateLimiter

logger = logging.getLogger(__name__)

IdentityResolver = Callable[[Request], Awaitable[str | None]]


class RateLimitMiddleware:
    """Limit requests to the configured path prefixes, keyed per identity.

    Failures in the limiter (for example an unreachable Redis) fail open by
    default: the provider-side spend cap is the hard backstop, so availability
    wins over strictness here.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        limiter: RateLimiter | None,
        identity: IdentityResolver,
        path_prefixes: Sequence[str],
        fail_open: bool = True,
    ) -> None:
        self._app = app
        self._limiter = limiter
        self._identity = identity
        self._path_prefixes = tuple(path_prefixes)
        self._fail_open = fail_open

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        limiter = self._limiter
        if limiter is None or scope["type"] != "http" or not self._matches(scope.get("path", "")):
            await self._app(scope, receive, send)
            return

        try:
            user_id = await self._identity(Request(scope))
            decision = await limiter.check(_key_for(scope, user_id))
        except Exception:
            if not self._fail_open:
                raise
            logger.warning("Rate limiter unavailable; failing open", exc_info=True)
            await self._app(scope, receive, send)
            return

        if decision.allowed:
            await self._app(scope, receive, send)
            return

        await _send_rate_limited(send, scope, decision.retry_after)

    def _matches(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._path_prefixes)


def _key_for(scope: Scope, user_id: str | None) -> str:
    """Prefer the authenticated user; fall back to the client address."""
    if user_id:
        return f"user:{user_id}"
    client = scope.get("client")
    return f"ip:{client[0] if client else 'unknown'}"


async def _send_rate_limited(send: Send, scope: Scope, retry_after: int) -> None:
    """Build the problem body here: middleware never reaches the handlers."""
    body = problem_body(
        status_code=RateLimitedError.status_code,
        title=RateLimitedError.title,
        detail="Rate limit exceeded. Try again shortly.",
        code=RateLimitedError.code,
        instance=scope.get("path", "/"),
    )
    payload = json.dumps(body).encode()
    headers = [
        (b"content-type", b"application/problem+json"),
        (b"content-length", str(len(payload)).encode()),
        (b"retry-after", str(max(1, retry_after)).encode()),
    ]
    await send(
        {"type": "http.response.start", "status": RateLimitedError.status_code, "headers": headers}
    )
    await send({"type": "http.response.body", "body": payload})
