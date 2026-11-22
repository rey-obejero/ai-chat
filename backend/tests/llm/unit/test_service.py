import pytest

from ai_chat.llm.adapters.openai import OpenAIChatProvider
from ai_chat.llm.exceptions import LLMNotConfiguredError
from ai_chat.llm.port import ChatProvider
from ai_chat.llm.service import build_chat_provider
from ai_chat.shared.config import Settings


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_build_chat_provider_requires_key() -> None:
    with pytest.raises(LLMNotConfiguredError):
        build_chat_provider(_settings(llm_api_key=""))


def test_build_chat_provider_satisfies_the_port() -> None:
    provider = build_chat_provider(_settings(llm_api_key="test-key"))

    assert isinstance(provider, OpenAIChatProvider)
    assert isinstance(provider, ChatProvider)
