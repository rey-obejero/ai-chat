import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from ai_chat.shared.rate_limit import RateLimitMiddleware
from ai_chat.shared.rate_limit.limiter import RateLimiter, build_storage

_PATH = "/api/v1/conversations"
_HEALTH = "/api/v1/health"


async def _ok(_request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def _inner_app() -> Starlette:
    return Starlette(routes=[Route(_PATH, _ok), Route(_HEALTH, _ok)])


def _client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _limiter(limit: str) -> RateLimiter:
    return RateLimiter(build_storage("async+memory://"), limit=limit)


async def test_requests_over_the_limit_return_problem_json() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(
        _inner_app(), limiter=_limiter("2/minute"), identity=identity, path_prefixes=(_PATH,)
    )

    async with _client(app) as client:
        first = await client.get(_PATH)
        second = await client.get(_PATH)
        third = await client.get(_PATH)

    assert (first.status_code, second.status_code) == (200, 200)
    assert third.status_code == 429
    assert third.headers["content-type"] == "application/problem+json"
    assert int(third.headers["retry-after"]) >= 1
    body = third.json()
    assert body["code"] == "RATE_LIMITED"
    assert body["status"] == 429
    assert body["instance"] == _PATH


async def test_unscoped_paths_pass_through() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(
        _inner_app(), limiter=_limiter("1/minute"), identity=identity, path_prefixes=(_PATH,)
    )

    async with _client(app) as client:
        responses = [await client.get(_HEALTH) for _ in range(3)]

    assert [response.status_code for response in responses] == [200, 200, 200]


async def test_each_identity_gets_its_own_bucket() -> None:
    current = {"id": "user-1"}

    async def identity(_request):
        return current["id"]

    app = RateLimitMiddleware(
        _inner_app(), limiter=_limiter("1/minute"), identity=identity, path_prefixes=(_PATH,)
    )

    async with _client(app) as client:
        assert (await client.get(_PATH)).status_code == 200
        assert (await client.get(_PATH)).status_code == 429
        current["id"] = "user-2"
        assert (await client.get(_PATH)).status_code == 200


async def test_anonymous_callers_fall_back_to_ip() -> None:
    async def identity(_request):
        return None

    app = RateLimitMiddleware(
        _inner_app(), limiter=_limiter("1/minute"), identity=identity, path_prefixes=(_PATH,)
    )

    async with _client(app) as client:
        assert (await client.get(_PATH)).status_code == 200
        assert (await client.get(_PATH)).status_code == 429


class _BrokenLimiter:
    async def check(self, _key: str):
        raise RuntimeError("storage unavailable")


async def test_limiter_failure_fails_open() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(
        _inner_app(),
        limiter=_BrokenLimiter(),  # type: ignore[arg-type]
        identity=identity,
        path_prefixes=(_PATH,),
        fail_open=True,
    )

    async with _client(app) as client:
        response = await client.get(_PATH)

    assert response.status_code == 200


async def test_limiter_failure_raises_when_not_failing_open() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(
        _inner_app(),
        limiter=_BrokenLimiter(),  # type: ignore[arg-type]
        identity=identity,
        path_prefixes=(_PATH,),
        fail_open=False,
    )

    with pytest.raises(RuntimeError):
        async with _client(app) as client:
            await client.get(_PATH)
