"""Composition root: wire concrete repositories/services into request handlers.

FastAPI caches `get_session` per request, so every repo/service below shares one session
(one transaction / unit of work per request)."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.ingest import IngestService
from app.repository import SqlConceptRepository, SqlEdgeRepository, SqlSearchRepository
from app.services import ConceptService
from app.webhook import RepoSyncer


def get_concept_repo(session: Session = Depends(get_session)) -> SqlConceptRepository:
    return SqlConceptRepository(session)


def get_edge_repo(session: Session = Depends(get_session)) -> SqlEdgeRepository:
    return SqlEdgeRepository(session)


def get_search_repo(session: Session = Depends(get_session)) -> SqlSearchRepository:
    return SqlSearchRepository(session)


def get_concept_service(
    session: Session = Depends(get_session),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
) -> ConceptService:
    return ConceptService(concepts, edges, session)


def get_ingest_service(
    session: Session = Depends(get_session),
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
) -> IngestService:
    return IngestService(concepts, edges, session)


def get_repo_syncer() -> RepoSyncer:
    return RepoSyncer()
