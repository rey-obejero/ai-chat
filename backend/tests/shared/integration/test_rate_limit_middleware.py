import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from ai_chat.shared.rate_limit import RateLimitMiddleware
from ai_chat.shared.rate_limit.limiter import RateLimitPolicy, build_storage

_PATH = "/api/v1/conversations"
_HEALTH = "/api/v1/health"
_SIGN_IN = "/api/auth/signin"
_RESET = "/api/auth/user/password/reset/token"


async def _ok(_request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def _inner_app() -> Starlette:
    return Starlette(
        routes=[
            Route(_PATH, _ok),
            Route(_HEALTH, _ok),
            Route(_SIGN_IN, _ok, methods=["POST"]),
            Route(_RESET, _ok, methods=["POST"]),
        ]
    )


def _client(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _policy(rules: dict[str, str]) -> RateLimitPolicy:
    return RateLimitPolicy(build_storage("async+memory://"), rules)


async def test_requests_over_the_limit_return_problem_json() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(_inner_app(), policy=_policy({_PATH: "2/minute"}), identity=identity)

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

    app = RateLimitMiddleware(_inner_app(), policy=_policy({_PATH: "1/minute"}), identity=identity)

    async with _client(app) as client:
        responses = [await client.get(_HEALTH) for _ in range(3)]

    assert [response.status_code for response in responses] == [200, 200, 200]


async def test_each_identity_gets_its_own_bucket() -> None:
    current = {"id": "user-1"}

    async def identity(_request):
        return current["id"]

    app = RateLimitMiddleware(_inner_app(), policy=_policy({_PATH: "1/minute"}), identity=identity)

    async with _client(app) as client:
        assert (await client.get(_PATH)).status_code == 200
        assert (await client.get(_PATH)).status_code == 429
        current["id"] = "user-2"
        assert (await client.get(_PATH)).status_code == 200


async def test_anonymous_callers_fall_back_to_ip() -> None:
    async def identity(_request):
        return None

    app = RateLimitMiddleware(_inner_app(), policy=_policy({_PATH: "1/minute"}), identity=identity)

    async with _client(app) as client:
        assert (await client.get(_PATH)).status_code == 200
        assert (await client.get(_PATH)).status_code == 429


async def test_the_tighter_prefix_beneath_a_blanket_one_is_applied() -> None:
    # `/api/auth` is the blanket prefix; the reset endpoint beneath it carries a
    # tighter limit and must win, so the third reset request is rejected while
    # sign-in is still allowed.
    async def identity(_request):
        return None

    app = RateLimitMiddleware(
        _inner_app(),
        policy=_policy({"/api/auth": "20/minute", "/api/auth/user/password/reset": "2/minute"}),
        identity=identity,
    )

    async with _client(app) as client:
        assert (await client.post(_SIGN_IN)).status_code == 200
        assert (await client.post(_RESET)).status_code == 200
        assert (await client.post(_RESET)).status_code == 200
        reset = await client.post(_RESET)

    assert reset.status_code == 429
    assert reset.headers["content-type"] == "application/problem+json"
    assert int(reset.headers["retry-after"]) >= 1


class _BrokenLimiter:
    async def check(self, _key: str):
        raise RuntimeError("storage unavailable")


class _BrokenPolicy:
    def select(self, _path: str) -> _BrokenLimiter:
        return _BrokenLimiter()


async def test_limiter_failure_fails_open() -> None:
    async def identity(_request):
        return "user-1"

    app = RateLimitMiddleware(
        _inner_app(),
        policy=_BrokenPolicy(),  # type: ignore[arg-type]
        identity=identity,
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
        policy=_BrokenPolicy(),  # type: ignore[arg-type]
        identity=identity,
        fail_open=False,
    )

    with pytest.raises(RuntimeError):
        async with _client(app) as client:
            await client.get(_PATH)
