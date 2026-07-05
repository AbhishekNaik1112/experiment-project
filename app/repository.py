"""Data-access layer. Routers and services depend on these repositories, never on SQL directly,
so a different backend (e.g. Postgres->another store) can be swapped behind the same surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import Concept
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
