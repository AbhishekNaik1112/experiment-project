"""Application settings, loaded from environment / .env (single source of config)."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://okf:okf@localhost:5433/okf"
    api_key: str | None = None
    github_webhook_secret: str | None = None

    embeddings_enabled: bool = False
    embedding_model: str = "all-MiniLM-L6-v2"

    auto_init_db: bool = False  # create schema on startup (used in cloud where there's no manual step)

    default_page_size: int = 50
    max_page_size: int = 200

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, v: str) -> str:
        # Managed providers (e.g. Neon) hand out a bare `postgresql://` URL; SQLAlchemy needs the driver.
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://") :]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
