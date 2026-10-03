from ai_chat.shared.config import Settings
from ai_chat.shared.rate_limit.limiter import (
    RateLimiter,
    RateLimitPolicy,
    build_rate_limit_policy,
    build_storage,
)


async def test_limiter_allows_up_to_the_limit_then_denies() -> None:
    limiter = RateLimiter(build_storage("async+memory://"), limit="2/minute")

    first = await limiter.check("user:1")
    second = await limiter.check("user:1")
    third = await limiter.check("user:1")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.remaining == 0
    assert 0 <= third.retry_after <= 60


async def test_limit_is_tracked_per_key() -> None:
    limiter = RateLimiter(build_storage("async+memory://"), limit="1/minute")

    assert (await limiter.check("user:1")).allowed is True
    assert (await limiter.check("user:1")).allowed is False
    assert (await limiter.check("user:2")).allowed is True


def test_build_storage_supports_redis_without_connecting() -> None:
    storage = build_storage("async+redis://localhost:6379/0")

    assert type(storage).__name__ == "RedisStorage"


def test_build_rate_limit_policy_reads_settings() -> None:
    settings = Settings(
        _env_file=None,
        rate_limit_rules={"/api/auth": "5/minute"},
    )

    policy = build_rate_limit_policy(settings)

    assert isinstance(policy, RateLimitPolicy)
    assert isinstance(policy.select("/api/auth/signin"), RateLimiter)


def test_the_longest_matching_prefix_wins() -> None:
    # The blanket `/api/auth` limit must not shadow the tighter one on the
    # reset endpoint that sits beneath it.
    policy = RateLimitPolicy(
        build_storage("async+memory://"),
        {"/api/auth": "20/minute", "/api/auth/user/password/reset": "3/minute"},
    )

    assert policy.select("/api/auth/signin") is not policy.select(
        "/api/auth/user/password/reset/token"
    )
    assert policy.select("/api/other") is None
