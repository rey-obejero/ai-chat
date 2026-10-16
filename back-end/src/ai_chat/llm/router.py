"""The models the picker may offer (FR-23)."""

from fastapi import APIRouter, Depends, Request

from ai_chat.auth import get_current_user_id
from ai_chat.llm.catalog import served_models
from ai_chat.llm.schemas import ModelRead
from ai_chat.shared.config import Settings

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelRead])
async def read_models(
    request: Request,
    _user_id: str = Depends(get_current_user_id),
) -> list[ModelRead]:
    """What this deployment serves, exactly one of them the default.

    Authentication is required, because the list is only useful inside the
    application and the choice it feeds is per conversation. The contents are
    configuration: adding a model is an environment change and nothing else.
    """
    settings: Settings = request.app.state.settings
    return [ModelRead.model_validate(model) for model in served_models(settings)]
