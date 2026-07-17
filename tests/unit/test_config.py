"""Phase F — DATABASE_URL driver normalization (managed providers hand out bare postgresql://)."""

from app.config import Settings


def test_config_normalizes_bare_postgres_url():
    s = Settings(database_url="postgresql://u:p@host/db?sslmode=require")
    assert s.database_url == "postgresql+psycopg://u:p@host/db?sslmode=require"


def test_config_keeps_psycopg_url():
    s = Settings(database_url="postgresql+psycopg://u:p@host/db")
    assert s.database_url == "postgresql+psycopg://u:p@host/db"


def test_auto_init_db_defaults_false():
    assert Settings().auto_init_db is False
