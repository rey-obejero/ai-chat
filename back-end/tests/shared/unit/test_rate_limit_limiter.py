from ai_chat.shared.config import Settings
from ai_chat.shared.rate_limit.limiter import RateLimiter, build_rate_limiter, build_storage


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


def test_build_rate_limiter_reads_settings() -> None:
    settings = Settings(_env_file=None, rate_limit_chat="5/minute")

    limiter = build_rate_limiter(settings)

    assert isinstance(limiter, RateLimiter)
