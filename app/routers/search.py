"""Full-text search endpoint (BM-like ts_rank_cd ordering)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_search_repo
from app.models import Page, SearchHitOut
from app.repository import SqlSearchRepository

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page[SearchHitOut])
def search(
    q: str = Query(min_length=1),
    type: str | None = Query(None),
    tags: list[str] = Query(default=[]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: SqlSearchRepository = Depends(get_search_repo),
) -> Page[SearchHitOut]:
    hits, total = repo.search(q, type=type, tags=tags or None, limit=limit, offset=offset)
    return Page(
        items=[SearchHitOut.model_validate(h) for h in hits],
        total=total,
        limit=limit,
        offset=offset,
    )
