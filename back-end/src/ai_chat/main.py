import secrets
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _metadata_version

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_chat.auth import resolve_user_id
from ai_chat.auth import router as auth_router
from ai_chat.conversations import router as conversations_router
from ai_chat.llm import router as models_router
from ai_chat.media import router as media_router
from ai_chat.shared.config import Settings, get_settings
from ai_chat.shared.db import build_engine, get_session
from ai_chat.shared.exceptions import register_exception_handlers
from ai_chat.shared.logging import configure_logging, request_id_var, set_request_id
from ai_chat.shared.rate_limit import RateLimitMiddleware, build_rate_limit_policy
from ai_chat.usage import router as usage_router


def _package_version() -> str:
    """The installed distribution's version, or a placeholder in a source tree."""
    try:
        return _metadata_version("ai-chat")
    except PackageNotFoundError:
        return "0.0.0"


APP_VERSION = _package_version()


class RequestIdMiddleware:
    """Give every request an identifier and echo it back in the response."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound = dict(scope["headers"]).get(b"x-request-id", b"")
        request_id = inbound.decode("ascii", "replace") or secrets.token_hex(8)
        token = set_request_id(request_id)

        async def send_with_id(message):
            if message["type"] == "http.response.start":
                headers = [*message.get("headers", []), (b"x-request-id", request_id.encode())]
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)


class SecurityHeadersMiddleware:
    """Protective headers on every response, whichever deployment serves it."""

    HEADERS = (
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
    )

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = [*message.get("headers", []), *self.HEADERS]
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


def create_app(settings: Settings | None = None, *, init_auth: bool = True) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)
    policy = build_rate_limit_policy(settings) if settings.rate_limit_enabled else None

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # Built before the try so a failed construction never reaches the
        # disposal path with nothing to dispose.
        engine = build_engine(settings.database_url)
        _app.state.engine = engine
        _app.state.session_factory = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        try:
            yield
        finally:
            if policy is not None:
                await policy.aclose()
            await engine.dispose()
            # Only built lazily on the first proxied image, if ever.
            media_client = getattr(_app.state, "media_client", None)
            if media_client is not None:
                await media_client.aclose()

    app = FastAPI(title=settings.app_name, version=APP_VERSION, lifespan=lifespan)
    # Dependencies read the settings the app was built with, not the global
    # cached ones, so tests can build an app with a different configuration.
    app.state.settings = settings

    if init_auth:
        from ai_chat.auth.adapter_supertokens import (
            init_supertokens,
            supertokens_middleware,
        )

        init_supertokens(settings)
        app.add_middleware(supertokens_middleware())

    # Added *after* the SuperTokens middleware so it is outermost and runs
    # first. SuperTokens answers `/api/auth/*` itself and never calls the
    # wrapped app, so a limiter beneath it would never see an auth request.
    # The limiter resolves identity itself, because middleware runs before
    # route dependencies (ADR-0020).
    app.add_middleware(
        RateLimitMiddleware,
        policy=policy,
        identity=resolve_user_id,
        fail_open=settings.rate_limit_fail_open,
    )

    # Starlette treats the last-added middleware as outermost. The request-id
    # layer goes last so the identifier exists in logging context before any
    # other layer logs; the protective headers sit just inside it, so even the
    # limiter's refusals carry them.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    api = APIRouter(prefix="/api/v1")

    @api.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/ready", tags=["health"])
    async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
        # Liveness stays instant; readiness proves the database answers. The
        # auth service is excluded on purpose: its SDK polls it, and test apps
        # and the mock-LLM lane run without it.
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}

    api.include_router(auth_router)
    api.include_router(conversations_router)
    api.include_router(models_router)
    api.include_router(usage_router)
    if settings.media_proxy_enabled:
        api.include_router(media_router)
    app.include_router(api)

    return app


app = create_app()
