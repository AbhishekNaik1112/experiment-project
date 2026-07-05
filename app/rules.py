"""OKF bundle validation — pure, no persistence. Fills a gap: no official OKF validator exists.

Rules:
- missing_type (error): a concept file lacks the required `type`.
- duplicate_id (error): two files derive the same concept id.
- dangling_link (warning): a bundle-local link points at a concept not present in the bundle.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.links import resolved_links
from app.parser import (
    MissingTypeError,
    ParsedConcept,
    derive_id,
    is_structural_file,
    parse_concept,
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    concept_id: str | None
    rule: str
    severity: str  # "error" | "warning"
    message: str


@dataclass
class BundleValidation:
    issues: list[ValidationIssue]
    concept_count: int


def validate_bundle(entries: Iterable[tuple[str, str]]) -> BundleValidation:
    issues: list[ValidationIssue] = []
    parsed: list[tuple[str, ParsedConcept]] = []
    id_paths: dict[str, list[str]] = {}

    for rel_path, text in entries:
        if is_structural_file(rel_path):
            continue
        concept_id = derive_id(rel_path)
        id_paths.setdefault(concept_id, []).append(rel_path)
        try:
            concept = parse_concept(rel_path, text, bundle="")
        except MissingTypeError as exc:
            issues.append(
                ValidationIssue(rel_path, concept_id, "missing_type", "error", str(exc))
            )
            continue
        parsed.append((rel_path, concept))

    for concept_id, paths in id_paths.items():
        if len(paths) > 1:
            for path in paths:
                issues.append(
                    ValidationIssue(
                        path,
                        concept_id,
                        "duplicate_id",
                        "error",
                        f"concept id {concept_id!r} produced by {len(paths)} files",
                    )
                )

    known = {concept.id for _, concept in parsed}
    for rel_path, concept in parsed:
        for target, _anchor in resolved_links(concept.id, concept.body):
            if target not in known:
                issues.append(
                    ValidationIssue(
                        rel_path,
                        concept.id,
                        "dangling_link",
                        "warning",
                        f"link target {target!r} not found in bundle",
                    )
                )

    return BundleValidation(issues=issues, concept_count=len(parsed))
