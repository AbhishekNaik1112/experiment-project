"""M14-M15 — semantic + hybrid search plumbing, using a deterministic fake embedder (no torch).

The fake groups synonyms so cosine ordering / RRF fusion are testable without downloading a model.
Genuine model behaviour is covered separately in tests/unit/test_embeddings_real.py.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import Concept, get_session
from app.embeddings import get_embedder
from app.main import create_app

_GROUPS = [
    {"car", "automobile", "vehicle", "speed", "fast", "drive"},
    {"banana", "bread", "recipe", "food", "bake"},
]


class FakeEmbedder:
    def encode(self, texts):
        vectors = []
        for text in texts:
            vec = [0.0] * 384
            tokens = set(text.lower().split())
            for i, group in enumerate(_GROUPS):
                if tokens & group:
                    vec[i] = 1.0
            if not any(vec):
                vec[383] = 1.0
            vectors.append(vec)
        return vectors


@pytest.fixture
def sem_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(embeddings_enabled=True)
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _ingest_two(client, tmp_path, a_body, b_body):
    (tmp_path / "a.md").write_text(f"---\ntype: Doc\n---\n{a_body}", encoding="utf-8")
    (tmp_path / "b.md").write_text(f"---\ntype: Doc\n---\n{b_body}", encoding="utf-8")
    assert client.post("/ingest", params={"path": str(tmp_path)}).status_code == 200


def test_ingest_populates_embedding(sem_client, tmp_path, db_session):
    _ingest_two(sem_client, tmp_path, "car", "banana bread")
    obj = db_session.get(Concept, "a")
    assert obj.embedding is not None and len(obj.embedding) == 384


def test_semantic_finds_without_keyword_overlap(sem_client, tmp_path):
    _ingest_two(sem_client, tmp_path, "the automobile is fast", "banana bread recipe")
    items = sem_client.get("/search", params={"q": "car speed", "mode": "semantic"}).json()["items"]
    assert items and items[0]["id"] == "a"


def test_hybrid_combines_keyword_and_semantic(sem_client, tmp_path):
    _ingest_two(sem_client, tmp_path, "the automobile is fast", "car car car")
    hits = sem_client.get("/search", params={"q": "car", "mode": "hybrid"}).json()["items"]
    ids = {h["id"] for h in hits}
    assert "a" in ids and "b" in ids  # a via semantic, b via keyword


def test_semantic_disabled_returns_400(client):
    assert client.get("/search", params={"q": "x", "mode": "semantic"}).status_code == 400


def test_bad_mode_422(client):
    assert client.get("/search", params={"q": "x", "mode": "nonsense"}).status_code == 422


def test_keyword_mode_still_default(sem_client, tmp_path):
    _ingest_two(sem_client, tmp_path, "bitcoin ledger", "banana bread")
    items = sem_client.get("/search", params={"q": "bitcoin"}).json()["items"]
    assert [i["id"] for i in items] == ["a"]
