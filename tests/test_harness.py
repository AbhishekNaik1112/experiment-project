"""M0 — prove the harness: app boots, schema applies, pgvector is available."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_schema_applies(db_session: Session):
    for table in ("concepts", "edges"):
        got = db_session.execute(text("SELECT to_regclass(:t)"), {"t": table}).scalar()
        assert got == table


def test_pgvector_available(db_session: Session):
    ext = db_session.execute(
        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    ).scalar()
    assert ext == "vector"

    # The vector type round-trips.
    val = db_session.execute(text("SELECT '[1,2,3]'::vector")).scalar()
    assert val is not None
