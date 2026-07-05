"""Database engine, ORM table definitions, and the request-scoped session dependency.

One place owns the physical schema. The same SQLAlchemy metadata drives both create_all (tests)
and Alembic autogeneration (deploy), so there is a single source of truth for the schema.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.config import get_settings

EMBED_DIM = 384  # all-MiniLM-L6-v2 (Phase D)


class Base(DeclarativeBase):
    pass


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(Text, primary_key=True)  # bundle path, sans .md
    bundle: Mapped[str] = mapped_column(Text, nullable=False, server_default="default")
    type: Mapped[str] = mapped_column(Text, nullable=False)  # OKF's only required field
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    resource: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    frontmatter: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', "
            "coalesce(title,'') || ' ' || coalesce(description,'') || ' ' || coalesce(body,''))",
            persisted=True,
        ),
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM))  # Phase D
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_concepts_type", "type"),
        Index("idx_concepts_bundle", "bundle"),
        Index("idx_concepts_tags", "tags", postgresql_using="gin"),
        Index("idx_concepts_fts", "search_vector", postgresql_using="gin"),
    )


class Edge(Base):
    __tablename__ = "edges"

    source_id: Mapped[str] = mapped_column(
        Text, ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    target_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rel_type: Mapped[str] = mapped_column(Text, primary_key=True, server_default="link")
    anchor_text: Mapped[str | None] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    __table_args__ = (Index("idx_edges_target", "target_id"),)


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or get_settings().database_url, future=True)


def init_db(engine: Engine) -> None:
    """Ensure the pgvector extension exists, then materialize all tables."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = make_engine()
    return _engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency: yields a request-scoped session. Overridden in tests."""
    with Session(get_engine()) as session:
        yield session
