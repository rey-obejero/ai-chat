from fastapi import APIRouter, FastAPI

from ai_chat.auth import router as auth_router
from ai_chat.chat import router as chat_router
from ai_chat.shared.config import Settings, get_settings
from ai_chat.shared.exceptions import register_exception_handlers


def create_app(settings: Settings | None = None, *, init_auth: bool = True) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

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
    api.include_router(chat_router)
    app.include_router(api)

    return app


app = create_app()
