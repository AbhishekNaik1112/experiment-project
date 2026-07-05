"""CRUD endpoints for concepts. Path IDs contain slashes, so every route uses {concept_id:path}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_concept_service
from app.errors import NotFoundError
from app.models import ConceptCreate, ConceptOut, ConceptUpdate
from app.render import render_markdown
from app.repository import ConceptInput
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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConceptOut)
def create_concept(
    payload: ConceptCreate,
    response: Response,
    svc: ConceptService = Depends(get_concept_service),
) -> ConceptOut:
    obj = svc.create(_to_input(payload.id, payload.bundle, payload))
    response.headers["Location"] = f"/concepts/{obj.id}"
    return _to_out(obj)


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


@router.put("/{concept_id:path}", response_model=ConceptOut)
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


@router.delete("/{concept_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(
    concept_id: str,
    svc: ConceptService = Depends(get_concept_service),
) -> Response:
    svc.delete(concept_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
