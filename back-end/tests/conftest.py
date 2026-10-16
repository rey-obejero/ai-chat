import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from ai_chat.main import create_app
from ai_chat.shared.config import Settings
from ai_chat.shared.db import Base, get_session, get_session_factory

# No test reaches another service. The breach check is off for every app built
# here; a test that exercises screening passes its own settings or a fake client.
_OFFLINE: dict[str, object] = {
    "rate_limit_enabled": False,
    "password_breach_check_enabled": False,
}


@pytest.fixture(autouse=True)
def _no_auth_service(monkeypatch):
    """Keep the verification read off the network.

    These tests build the app with `init_auth=False`, so there is no core to ask.
    The real read would spend the SDK's whole 30-second HTTP timeout before
    failing, and it fails either way — so it is replaced by a lookup that fails
    at once, which is the conservative answer the app must reach without the
    wait. Tests that need a *verified* account override `get_email_verified`.
    """
    import ai_chat.auth.adapter_supertokens as adapter
    from ai_chat.auth.verification import VerificationStateCache

    async def unreachable(_user_id: str) -> bool:
        raise RuntimeError("no auth service in the test process")

    monkeypatch.setattr(adapter, "_verification_state", VerificationStateCache(unreachable))


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


def _build_app(session_factory, settings):
    application = create_app(settings, init_auth=False)

    async def override_session():
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_session] = override_session
    application.dependency_overrides[get_session_factory] = lambda: session_factory
    return application


@pytest_asyncio.fixture
async def app(session_factory):
    # Rate limiting is exercised by its own tests against the middleware
    # directly; the shared app fixture keeps it off so auth is not involved.
    # The token quota is off too — its tests opt in through quota_app. `_OFFLINE`
    # covers what no test may reach: the breach service.
    return _build_app(
        session_factory,
        Settings(_env_file=None, **_OFFLINE, token_quota_enabled=False),
    )


@pytest_asyncio.fixture
async def quota_app(session_factory):
    """An app with the token quota on and a deliberately tiny budget."""
    return _build_app(
        session_factory,
        Settings(
            _env_file=None,
            **_OFFLINE,
            token_quota_enabled=True,
            token_quota_tokens=1000,
        ),
    )


# The picker's list is configuration (FR-23), so the only way to prove a second
# model is offered is to configure a deployment that serves one. Everything
# else about this app is the ordinary test app.
@pytest_asyncio.fixture
async def two_model_app(session_factory):
    """An app serving `openai/gpt-4o-mini` and `anthropic/claude-haiku`."""
    return _build_app(
        session_factory,
        Settings(
            _env_file=None,
            **_OFFLINE,
            token_quota_enabled=False,
            llm_model="openai/gpt-4o-mini",
            llm_models=["openai/gpt-4o-mini", "anthropic/claude-haiku"],
        ),
    )


@pytest_asyncio.fixture
async def two_model_client(two_model_app):
    transport = ASGITransport(app=two_model_app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def quota_client(quota_app):
    transport = ASGITransport(app=quota_app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
