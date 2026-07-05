"""Data-access layer. Routers and services depend on these repositories, never on SQL directly,
so a different backend (e.g. Postgres->another store) can be swapped behind the same surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import Concept, Edge
from app.errors import ConflictError, NotFoundError
from app.parser import ParsedConcept


@dataclass
class ConceptInput:
    """Everything needed to persist one concept (maps 1:1 to the concepts table)."""

    id: str
    type: str
    bundle: str = "default"
    title: str | None = None
    description: str | None = None
    resource: str | None = None
    timestamp: datetime | None = None
    tags: list[str] = field(default_factory=list)
    body: str = ""
    frontmatter: dict = field(default_factory=dict)

    @classmethod
    def from_parsed(cls, parsed: ParsedConcept) -> "ConceptInput":
        return cls(
            id=parsed.id,
            type=parsed.type,
            bundle=parsed.bundle,
            title=parsed.title,
            description=parsed.description,
            resource=parsed.resource,
            timestamp=parsed.timestamp,
            tags=list(parsed.tags),
            body=parsed.body,
            frontmatter=dict(parsed.extra),
        )


class SqlConceptRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def get(self, concept_id: str) -> Concept | None:
        return self.s.get(Concept, concept_id)

    def upsert(self, data: ConceptInput) -> Concept:
        obj = self.s.get(Concept, data.id)
        if obj is None:
            obj = Concept(id=data.id)
            self.s.add(obj)
        self._apply(obj, data)
        self.s.flush()
        return obj

    def create(self, data: ConceptInput) -> Concept:
        if self.s.get(Concept, data.id) is not None:
            raise ConflictError(f"concept {data.id!r} already exists")
        obj = Concept(id=data.id)
        self.s.add(obj)
        self._apply(obj, data)
        self.s.flush()
        return obj

    def update(self, concept_id: str, data: ConceptInput) -> Concept:
        obj = self.s.get(Concept, concept_id)
        if obj is None:
            raise NotFoundError(f"concept {concept_id!r} not found")
        self._apply(obj, data)
        self.s.flush()
        return obj

    def delete(self, concept_id: str) -> None:
        obj = self.s.get(Concept, concept_id)
        if obj is None:
            raise NotFoundError(f"concept {concept_id!r} not found")
        self.s.delete(obj)
        self.s.flush()

    def list(
        self,
        *,
        type: str | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Concept], int]:
        conditions = []
        if type:
            conditions.append(Concept.type == type)
        if tags:
            conditions.append(Concept.tags.contains(tags))  # array @> => AND semantics

        count_stmt = select(func.count()).select_from(Concept)
        list_stmt = select(Concept)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            list_stmt = list_stmt.where(*conditions)

        total = self.s.execute(count_stmt).scalar_one()
        list_stmt = list_stmt.order_by(Concept.id).limit(limit).offset(offset)
        items = list(self.s.execute(list_stmt).scalars())
        return items, total

    @staticmethod
    def _apply(obj: Concept, d: ConceptInput) -> None:
        obj.type = d.type
        obj.bundle = d.bundle
        obj.title = d.title
        obj.description = d.description
        obj.resource = d.resource
        obj.timestamp = d.timestamp
        obj.tags = list(d.tags)
        obj.body = d.body
        obj.frontmatter = dict(d.frontmatter)


@dataclass
class EdgeInput:
    target_id: str
    anchor_text: str | None = None
    rel_type: str = "link"
    resolved: bool = True


class SqlEdgeRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def replace_for_source(self, source_id: str, edges: list[EdgeInput]) -> None:
        """Replace all edges originating from source_id (idempotent full rewrite)."""
        self.s.execute(delete(Edge).where(Edge.source_id == source_id))
        seen: set[tuple[str, str]] = set()
        for e in edges:
            key = (e.target_id, e.rel_type)
            if key in seen:
                continue
            seen.add(key)
            self.s.add(
                Edge(
                    source_id=source_id,
                    target_id=e.target_id,
                    rel_type=e.rel_type,
                    anchor_text=e.anchor_text,
                    resolved=e.resolved,
                )
            )
        self.s.flush()

    def outgoing(self, source_id: str) -> list[Edge]:
        stmt = select(Edge).where(Edge.source_id == source_id).order_by(Edge.target_id)
        return list(self.s.execute(stmt).scalars())

    def backlinks(self, target_id: str) -> list[Edge]:
        stmt = select(Edge).where(Edge.target_id == target_id).order_by(Edge.source_id)
        return list(self.s.execute(stmt).scalars())
