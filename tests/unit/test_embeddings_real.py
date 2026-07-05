"""Real sentence-transformers model test — opt-in (downloads ~90MB model on first run).

Run with:  OKF_REAL_EMBED=1 pytest tests/unit/test_embeddings_real.py
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("OKF_REAL_EMBED") != "1",
    reason="set OKF_REAL_EMBED=1 to run the real model test",
)


def test_real_embedder_dim():
    pytest.importorskip("sentence_transformers")
    from app.embeddings import SentenceTransformerEmbedder

    vecs = SentenceTransformerEmbedder().encode(["hello world", "another sentence"])
    assert len(vecs) == 2 and len(vecs[0]) == 384


def test_real_embedder_semantic_similarity():
    pytest.importorskip("sentence_transformers")
    import numpy as np

    from app.embeddings import SentenceTransformerEmbedder

    car, automobile, banana = SentenceTransformerEmbedder().encode(
        ["car", "automobile", "banana bread"]
    )

    def cos(a, b):
        a, b = np.array(a), np.array(b)
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

    assert cos(car, automobile) > cos(car, banana)
