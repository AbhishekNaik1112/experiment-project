"""Ingest pipeline — parse an OKF bundle (directory or zip) and upsert concepts + edges.

Transport-agnostic on purpose: the same service backs POST /ingest today and the Git webhook later.
Two passes so cross-links resolve correctly: upsert every concept first, then derive edges (a link
target is 'resolved' only once its concept exists).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.bundle import BundleEntry, read_dir, read_zip
from app.embeddings import Embedder
from app.links import resolved_links
from app.models import IngestError, IngestResult
from app.parser import MissingTypeError, is_structural_file, parse_concept
from app.repository import (
    ConceptInput,
    EdgeInput,
    SqlConceptRepository,
    SqlEdgeRepository,
)


class IngestService:
    def __init__(
        self,
        concepts: SqlConceptRepository,
        edges: SqlEdgeRepository,
        session: Session,
        embedder: Embedder | None = None,
    ) -> None:
        self.concepts = concepts
        self.edges = edges
        self.session = session
        self.embedder = embedder

    def ingest_dir(self, dir_path: str, bundle: str | None = None) -> IngestResult:
        # NOTE: reads an arbitrary server-side path (local/self-host tool). Guard behind auth
        # before exposing publicly (Phase C).
        name, entries = read_dir(dir_path)
        return self._ingest(entries, bundle or name)

    def ingest_zip(self, data: bytes, bundle: str = "default") -> IngestResult:
        return self._ingest(read_zip(data), bundle)

    def _ingest(self, entries: list[BundleEntry], bundle: str) -> IngestResult:
        created = updated = skipped = 0
        errors: list[IngestError] = []
        bodies: dict[str, str] = {}
        embed_sources: dict[str, str] = {}

        for entry in entries:
            if is_structural_file(entry.rel_path):
                skipped += 1
                continue
            try:
                parsed = parse_concept(entry.rel_path, entry.text, bundle)
            except MissingTypeError as exc:
                errors.append(IngestError(path=entry.rel_path, reason=str(exc)))
                continue
            existed = self.concepts.get(parsed.id) is not None
            self.concepts.upsert(ConceptInput.from_parsed(parsed))
            updated += existed
            created += not existed
            bodies[parsed.id] = parsed.body
            embed_sources[parsed.id] = " ".join(
                x for x in (parsed.title, parsed.description, parsed.body) if x
            )

        for concept_id, body in bodies.items():
            edges = [
                EdgeInput(
                    target_id=target,
                    anchor_text=anchor,
                    resolved=self.concepts.get(target) is not None,
                )
                for target, anchor in resolved_links(concept_id, body)
            ]
            self.edges.replace_for_source(concept_id, edges)

        if self.embedder is not None and embed_sources:
            ids = list(embed_sources)
            vectors = self.embedder.encode([embed_sources[i] for i in ids])
            for concept_id, vector in zip(ids, vectors):
                self.concepts.set_embedding(concept_id, list(vector))

        self.session.commit()
        return IngestResult(
            bundle=bundle,
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )
