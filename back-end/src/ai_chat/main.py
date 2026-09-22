from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from ai_chat.auth import resolve_user_id
from ai_chat.auth import router as auth_router
from ai_chat.conversations import router as conversations_router
from ai_chat.shared.config import Settings, get_settings
from ai_chat.shared.exceptions import register_exception_handlers
from ai_chat.shared.rate_limit import RateLimitMiddleware, build_rate_limiter
from ai_chat.usage import router as usage_router


def create_app(settings: Settings | None = None, *, init_auth: bool = True) -> FastAPI:
    settings = settings or get_settings()
    limiter = build_rate_limiter(settings) if settings.rate_limit_enabled else None

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            if limiter is not None:
                await limiter.aclose()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    # Dependencies read the settings the app was built with, not the global
    # cached ones, so tests can build an app with a different configuration.
    app.state.settings = settings

    # Added before the SuperTokens middleware so the latter stays outermost and
    # runs first. The limiter resolves identity itself, because middleware runs
    # before route dependencies (ADR-0020).
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        identity=resolve_user_id,
        path_prefixes=settings.rate_limit_path_prefixes,
        fail_open=settings.rate_limit_fail_open,
    )

    if init_auth:
        from ai_chat.auth.adapter_supertokens import (
            init_supertokens,
            supertokens_middleware,
        )

        init_supertokens(settings)
        app.add_middleware(supertokens_middleware())

    register_exception_handlers(app)

    api = APIRouter(prefix="/api/v1")

    @api.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(auth_router)
    api.include_router(conversations_router)
    api.include_router(usage_router)
    app.include_router(api)

    return app


app = create_app()
