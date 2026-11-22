"""The models this deployment serves, and the rules that read that list (FR-23)."""

from __future__ import annotations

from dataclasses import dataclass

from ai_chat.llm.exceptions import UnknownModelError
from ai_chat.shared.config import Settings


@dataclass(frozen=True, slots=True)
class ServedModel:
    """One entry of the picker: the id a provider is called with, and its label."""

    id: str
    label: str
    is_default: bool


def served_models(settings: Settings) -> list[ServedModel]:
    """The picker's list, in settings order, with exactly one default.

    Configuration, not code: the list is `LLM_MODELS`, and `LLM_MODEL` is
    always in it (the settings enforce that), which is what makes the default
    resolvable and exactly one entry the default.
    """
    return [
        ServedModel(id=model, label=model, is_default=model == settings.llm_model)
        for model in settings.llm_models
    ]


def default_model(settings: Settings) -> str:
    """The model a request without a choice of its own goes to."""
    return settings.llm_model


def is_served(settings: Settings, model: str) -> bool:
    return model in settings.llm_models


def validate_model(settings: Settings, model: str) -> str:
    """The model as given, when this deployment serves it.

    The served list is configuration that can change under a stored choice
    (M5), so nothing is sent to a provider until it is checked against the
    list the deployment serves right now.
    """
    if not is_served(settings, model):
        raise UnknownModelError(detail="That model is not served by this deployment.")
    return model


def model_label(settings: Settings, model: str) -> str:
    """What to call a model in the interface; the id itself when it is unknown."""
    for served in served_models(settings):
        if served.id == model:
            return served.label
    return model
