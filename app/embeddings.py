"""Text embeddings for semantic search.

`sentence-transformers` (and torch) is imported lazily inside `encode`, so importing this module is
cheap and the rest of the app/tests never pull torch unless embeddings are actually used.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

EMBED_DIM = 384  # all-MiniLM-L6-v2


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None  # loaded on first use

    def encode(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # heavy; deferred

            self._model = SentenceTransformer(self.model_name)
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]


@lru_cache
def _default_embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder()


def get_embedder() -> Embedder:
    """FastAPI dependency. Cheap to construct (model loads lazily); overridable in tests."""
    return _default_embedder()
