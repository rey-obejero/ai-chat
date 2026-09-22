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
    # The token quota is off too — its tests opt in through quota_app.
    return _build_app(
        session_factory,
        Settings(_env_file=None, rate_limit_enabled=False, token_quota_enabled=False),
    )


@pytest_asyncio.fixture
async def quota_app(session_factory):
    """An app with the token quota on and a deliberately tiny budget."""
    return _build_app(
        session_factory,
        Settings(
            _env_file=None,
            rate_limit_enabled=False,
            token_quota_enabled=True,
            token_quota_tokens=1000,
        ),
    )


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
