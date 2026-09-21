from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Chat"
    api_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://aichat:aichat@localhost:5433/aichat"

    supertokens_connection_uri: str = "http://localhost:3567"
    supertokens_api_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""

    # LLM provider — OpenRouter by default (ADR-0018). The key is env-only
    # (ADR-0009) and no default means a missing key fails loudly at request time.
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "openai/gpt-4o-mini"
    llm_embedding_model: str = "openai/text-embedding-3-small"
    llm_max_output_tokens: int = 1024
    llm_request_timeout: float = 60.0

    # Rate limiting (ADR-0020). Memory storage in development; switch to
    # "async+redis://…" once the API runs more than one process.
    rate_limit_enabled: bool = True
    rate_limit_storage_uri: str = "async+memory://"
    rate_limit_chat: str = "20/minute"
    rate_limit_path_prefixes: list[str] = ["/api/v1/conversations"]
    rate_limit_fail_open: bool = True

    @property
    def supertokens_api_key_or_none(self) -> str | None:
        return self.supertokens_api_key or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
