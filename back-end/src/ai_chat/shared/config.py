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

    @property
    def supertokens_api_key_or_none(self) -> str | None:
        return self.supertokens_api_key or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
