"""Search endpoint — keyword (ts_rank_cd), semantic (pgvector cosine), or hybrid (RRF)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.dependencies import get_search_repo
from app.embeddings import Embedder, get_embedder
from app.models import Page, SearchHitOut
from app.repository import SqlSearchRepository

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page[SearchHitOut])
def search(
    q: str = Query(min_length=1),
    mode: Literal["keyword", "semantic", "hybrid"] = "keyword",
    type: str | None = Query(None),
    tags: list[str] = Query(default=[]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: SqlSearchRepository = Depends(get_search_repo),
    embedder: Embedder = Depends(get_embedder),
    settings: Settings = Depends(get_settings),
) -> Page[SearchHitOut]:
    tag_filter = tags or None

    if mode == "keyword":
        hits, total = repo.search(q, type=type, tags=tag_filter, limit=limit, offset=offset)
    else:
        if not settings.embeddings_enabled:
            raise HTTPException(status_code=400, detail="semantic search is disabled")
        query_vec = embedder.encode([q])[0]
        if mode == "semantic":
            hits, total = repo.semantic(
                query_vec, type=type, tags=tag_filter, limit=limit, offset=offset
            )
        else:  # hybrid
            hits, total = repo.hybrid(
                q, query_vec, type=type, tags=tag_filter, limit=limit, offset=offset
            )

    return Page(
        items=[SearchHitOut.model_validate(h) for h in hits],
        total=total,
        limit=limit,
        offset=offset,
    )
