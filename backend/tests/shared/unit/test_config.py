"""Settings as a deployment writes them, including the model list (FR-23)."""

import pytest
from pydantic import ValidationError

from ai_chat.shared.config import Settings

DEFAULT = "openai/gpt-4o-mini"


def _from_env(monkeypatch, models: str | None = None) -> Settings:
    """Build settings with the model list coming from the environment.

    ``_env_file=None`` keeps the developer's own `backend/.env` out of it: the
    environment is what a container and the e2e stack use.
    """
    monkeypatch.setenv("LLM_MODEL", DEFAULT)
    if models is None:
        monkeypatch.delenv("LLM_MODELS", raising=False)
    else:
        monkeypatch.setenv("LLM_MODELS", models)
    return Settings(_env_file=None)


def test_no_value_serves_only_the_default(monkeypatch) -> None:
    assert _from_env(monkeypatch).llm_models == [DEFAULT]


def test_an_empty_value_serves_only_the_default(monkeypatch) -> None:
    assert _from_env(monkeypatch, "").llm_models == [DEFAULT]


def test_a_comma_separated_value_is_split(monkeypatch) -> None:
    settings = _from_env(monkeypatch, "e2e/mock,e2e/mock-alt")

    assert settings.llm_models == [DEFAULT, "e2e/mock", "e2e/mock-alt"]


def test_a_comma_separated_value_ignores_spaces_and_blanks(monkeypatch) -> None:
    settings = _from_env(monkeypatch, " e2e/mock , , e2e/mock-alt ,")

    assert settings.llm_models == [DEFAULT, "e2e/mock", "e2e/mock-alt"]


def test_a_json_array_is_accepted(monkeypatch) -> None:
    settings = _from_env(monkeypatch, '["e2e/mock", "e2e/mock-alt"]')

    assert settings.llm_models == [DEFAULT, "e2e/mock", "e2e/mock-alt"]


def test_a_json_array_keeps_order_and_collapses_repeats(monkeypatch) -> None:
    settings = _from_env(monkeypatch, f'["e2e/mock-alt", "e2e/mock-alt", "{DEFAULT}"]')

    assert settings.llm_models == ["e2e/mock-alt", DEFAULT]


def test_a_list_given_in_code_is_used_as_it_is(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", DEFAULT)
    monkeypatch.delenv("LLM_MODELS", raising=False)

    settings = Settings(_env_file=None, llm_models=["e2e/mock", "e2e/mock-alt"])

    assert settings.llm_models == [DEFAULT, "e2e/mock", "e2e/mock-alt"]


def test_the_dotenv_file_may_hold_the_comma_separated_form(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LLM_MODEL", DEFAULT)
    monkeypatch.delenv("LLM_MODELS", raising=False)
    env_file = tmp_path / "env"
    env_file.write_text("LLM_MODELS=e2e/mock,e2e/mock-alt\n")

    settings = Settings(_env_file=env_file)

    assert settings.llm_models == [DEFAULT, "e2e/mock", "e2e/mock-alt"]


def test_an_unterminated_json_array_is_refused(monkeypatch) -> None:
    with pytest.raises(ValidationError) as raised:
        _from_env(monkeypatch, '["e2e/mock"')

    # The rejection names the field and both accepted forms.
    assert "LLM_MODELS" in str(raised.value)
    assert "comma-separated" in str(raised.value)


def test_a_json_object_is_refused(monkeypatch) -> None:
    # The field is a list, so an object is a typo rather than one odd id.
    with pytest.raises(ValidationError):
        _from_env(monkeypatch, '{"e2e/mock": "e2e/mock-alt"}')


def _origins(monkeypatch, **overrides) -> Settings:
    """Build settings with the browser origins taken from the environment."""
    monkeypatch.setenv("LLM_MODEL", DEFAULT)
    for name in ("API_BASE_URL", "FRONTEND_URL"):
        monkeypatch.delenv(name, raising=False)
    return Settings(_env_file=None, **overrides)


def test_an_absolute_url_is_accepted(monkeypatch) -> None:
    settings = _origins(
        monkeypatch,
        api_base_url="https://chat.example.com",
        frontend_url="https://chat.example.com",
    )

    assert settings.api_base_url == "https://chat.example.com"
    assert settings.frontend_url == "https://chat.example.com"


def test_a_bare_host_is_refused(monkeypatch) -> None:
    with pytest.raises(ValidationError) as raised:
        _origins(monkeypatch, api_base_url="chat.example.com")

    # The rejection names the variable, the form, and what was given.
    message = str(raised.value)
    assert "API_BASE_URL must be an absolute URL such as https://chat.example.com" in message
    assert "chat.example.com" in message


def test_a_bare_host_is_refused_for_the_frontend_url(monkeypatch) -> None:
    with pytest.raises(ValidationError) as raised:
        _origins(monkeypatch, frontend_url="chat.example.com")

    assert "FRONTEND_URL must be an absolute URL" in str(raised.value)


def test_mismatched_origins_are_refused(monkeypatch) -> None:
    with pytest.raises(ValidationError) as raised:
        _origins(
            monkeypatch,
            api_base_url="https://chat.example.com",
            frontend_url="https://app.example.com",
        )

    message = str(raised.value)
    assert "API_BASE_URL and FRONTEND_URL must match" in message
    assert "https://chat.example.com" in message
    assert "https://app.example.com" in message
