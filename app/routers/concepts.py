"""CRUD endpoints for concepts. Path IDs contain slashes, so every route uses {concept_id:path}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_concept_repo, get_concept_service, get_edge_repo
from app.errors import NotFoundError
from app.models import (
    ConceptCreate,
    ConceptListItem,
    ConceptOut,
    ConceptUpdate,
    LinkOut,
    LinksResponse,
    Page,
)
from app.render import render_markdown
from app.repository import ConceptInput, SqlConceptRepository, SqlEdgeRepository
from app.security import require_api_key
from app.services import ConceptService

router = APIRouter(prefix="/concepts", tags=["concepts"])


def _to_out(obj, *, render: bool = False) -> ConceptOut:
    out = ConceptOut.model_validate(obj)
    if render:
        out.html = render_markdown(obj.body)
    return out


def _to_input(concept_id: str, bundle: str, payload: ConceptCreate | ConceptUpdate) -> ConceptInput:
    return ConceptInput(
        id=concept_id,
        type=payload.type,
        bundle=bundle,
        title=payload.title,
        description=payload.description,
        resource=payload.resource,
        timestamp=payload.timestamp,
        tags=payload.tags,
        body=payload.body,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ConceptOut,
    dependencies=[Depends(require_api_key)],
)
def create_concept(
    payload: ConceptCreate,
    response: Response,
    svc: ConceptService = Depends(get_concept_service),
) -> ConceptOut:
    obj = svc.create(_to_input(payload.id, payload.bundle, payload))
    response.headers["Location"] = f"/concepts/{obj.id}"
    return _to_out(obj)


@router.get("", response_model=Page[ConceptListItem])
def list_concepts(
    type: str | None = Query(None),
    tags: list[str] = Query(default=[]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    svc: ConceptService = Depends(get_concept_service),
) -> Page[ConceptListItem]:
    items, total = svc.list(type=type, tags=tags or None, limit=limit, offset=offset)
    return Page(
        items=[ConceptListItem.model_validate(o) for o in items],
        total=total,
        limit=limit,
        offset=offset,
    )


# Declared before GET /{concept_id:path} so `.../links` is not swallowed by the path converter.
@router.get("/{concept_id:path}/links", response_model=LinksResponse)
def get_links(
    concept_id: str,
    concepts_repo: SqlConceptRepository = Depends(get_concept_repo),
    edges_repo: SqlEdgeRepository = Depends(get_edge_repo),
) -> LinksResponse:
    if concepts_repo.get(concept_id) is None:
        raise NotFoundError(f"concept {concept_id!r} not found")
    outgoing = [
        LinkOut(target_id=e.target_id, anchor_text=e.anchor_text, resolved=e.resolved)
        for e in edges_repo.outgoing(concept_id)
    ]
    backlinks = [
        LinkOut(target_id=e.source_id, anchor_text=e.anchor_text, resolved=e.resolved)
        for e in edges_repo.backlinks(concept_id)
    ]
    return LinksResponse(id=concept_id, outgoing=outgoing, backlinks=backlinks)


@router.get("/{concept_id:path}", response_model=ConceptOut)
def get_concept(
    concept_id: str,
    render: bool = Query(False),
    svc: ConceptService = Depends(get_concept_service),
) -> ConceptOut:
    obj = svc.get(concept_id)
    if obj is None:
        raise NotFoundError(f"concept {concept_id!r} not found")
    return _to_out(obj, render=render)


@router.put(
    "/{concept_id:path}",
    response_model=ConceptOut,
    dependencies=[Depends(require_api_key)],
)
def update_concept(
    concept_id: str,
    payload: ConceptUpdate,
    svc: ConceptService = Depends(get_concept_service),
) -> ConceptOut:
    existing = svc.get(concept_id)
    if existing is None:
        raise NotFoundError(f"concept {concept_id!r} not found")
    obj = svc.update(concept_id, _to_input(concept_id, existing.bundle, payload))
    return _to_out(obj)


@router.delete(
    "/{concept_id:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_concept(
    concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> Response:
    svc.delete(concept_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
