"""Application settings, loaded from environment / .env (single source of config)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://okf:okf@localhost:5433/okf"
    api_key: str | None = None
    github_webhook_secret: str | None = None

    embeddings_enabled: bool = False
    embedding_model: str = "all-MiniLM-L6-v2"

    default_page_size: int = 50
    max_page_size: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
