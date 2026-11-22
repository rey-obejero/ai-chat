from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> AsyncEngine:
    """One engine per application, built at startup and disposed at shutdown.

    The pool numbers are stated defaults, not derived from a capacity
    measurement. The statement timeout is PostgreSQL-only: the SQLite engine
    the tests use rejects unknown server settings.
    """
    connect_args: dict[str, object] = {}
    if database_url.startswith("postgresql"):
        connect_args["server_settings"] = {"statement_timeout": "30000"}
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        connect_args=connect_args,
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """A session factory for work that outlives the request-scoped session.

    Streaming replies persist their assistant message after the response body
    has started, by which point ``get_session``'s session is already closed.
    Injectable so tests can point it at their own engine.
    """
    return request.app.state.session_factory
