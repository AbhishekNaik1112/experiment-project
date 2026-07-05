"""Application services — orchestrate repositories into a unit of work.

ConceptService owns the write path: persist a concept, re-derive its outgoing edges from the
markdown body, then commit atomically. Reused by the CRUD router and (later) the ingest pipeline.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import Concept
from app.links import resolved_links
from app.repository import (
    ConceptInput,
    EdgeInput,
    SqlConceptRepository,
    SqlEdgeRepository,
)


class ConceptService:
    def __init__(
        self,
        concepts: SqlConceptRepository,
        edges: SqlEdgeRepository,
        session: Session,
    ) -> None:
        self.concepts = concepts
        self.edges = edges
        self.session = session

    def get(self, concept_id: str) -> Concept | None:
        return self.concepts.get(concept_id)

    def list(self, **kwargs) -> tuple[list[Concept], int]:
        return self.concepts.list(**kwargs)

    def create(self, data: ConceptInput) -> Concept:
        obj = self.concepts.create(data)
        self._sync_edges(obj.id, obj.body)
        self.session.commit()
        return obj

    def update(self, concept_id: str, data: ConceptInput) -> Concept:
        obj = self.concepts.update(concept_id, data)
        self._sync_edges(concept_id, obj.body)
        self.session.commit()
        return obj

    def delete(self, concept_id: str) -> None:
        self.concepts.delete(concept_id)
        self.session.commit()

    def _sync_edges(self, source_id: str, body: str) -> None:
        edges = [
            EdgeInput(
                target_id=target,
                anchor_text=anchor,
                resolved=self.concepts.get(target) is not None,
            )
            for target, anchor in resolved_links(source_id, body)
        ]
        self.edges.replace_for_source(source_id, edges)
