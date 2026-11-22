"""The served model list and what a choice is checked against (FR-23)."""

import pytest

from ai_chat.llm import UnknownModelError, model_label, served_models, validate_model
from ai_chat.shared.config import Settings


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_a_deployment_without_a_list_serves_only_the_default() -> None:
    models = served_models(_settings(llm_model="openai/gpt-4o-mini"))

    assert [(model.id, model.label, model.is_default) for model in models] == [
        ("openai/gpt-4o-mini", "openai/gpt-4o-mini", True)
    ]


def test_the_configured_list_is_served_in_order_with_one_default() -> None:
    models = served_models(_settings(llm_model="b/second", llm_models=["a/first", "b/second"]))

    assert [(model.id, model.is_default) for model in models] == [
        ("a/first", False),
        ("b/second", True),
    ]


def test_the_default_is_served_even_when_the_list_omits_it() -> None:
    # Otherwise the list would carry no `is_default` entry and a request with
    # no choice of its own would have nothing to fall back to.
    models = served_models(_settings(llm_model="c/third", llm_models=["a/first"]))

    assert [model.id for model in models] == ["c/third", "a/first"]
    assert models[0].is_default is True


def test_a_repeated_model_is_offered_once() -> None:
    models = served_models(_settings(llm_model="a/first", llm_models=["a/first", "a/first"]))

    assert [model.id for model in models] == ["a/first"]


def test_the_list_may_be_written_comma_separated() -> None:
    models = served_models(_settings(llm_model="a/first", llm_models="a/first, b/second"))

    assert [model.id for model in models] == ["a/first", "b/second"]


def test_a_model_the_deployment_does_not_serve_is_refused() -> None:
    with pytest.raises(UnknownModelError):
        validate_model(_settings(), "someone/elses-model")


def test_a_served_model_is_returned_unchanged() -> None:
    assert validate_model(_settings(llm_model="a/first"), "a/first") == "a/first"


def test_the_label_of_a_model_that_is_not_served_is_its_id() -> None:
    # A caption about a model the deployment dropped still has to name
    # something recognisable.
    assert model_label(_settings(), "gone/model") == "gone/model"
