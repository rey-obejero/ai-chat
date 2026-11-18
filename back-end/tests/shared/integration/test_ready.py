"""Liveness is instant; readiness proves the database answers."""

import httpx
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ai_chat.main import create_app
from ai_chat.shared.config import Settings


async def test_ready_reports_ready_when_the_database_answers(client) -> None:
    response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_ready_fails_when_the_database_is_unreachable(tmp_path) -> None:
    app = create_app(Settings(_env_file=None, rate_limit_enabled=False), init_auth=False)
    # A path in a directory that does not exist: SQLite cannot create the file,
    # so the query fails the way an unreachable database does.
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/no-such-directory/missing.db")
    app.state.session_factory = async_sessionmaker(engine, class_=AsyncSession)

    # The 500 handler sends its response and then re-raises; letting that
    # through to the test would hide the response we are asserting on.
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get("/api/v1/ready")

    await engine.dispose()
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
