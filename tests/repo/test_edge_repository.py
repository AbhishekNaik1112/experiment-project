"""M4 — edge repository: replace-for-source (idempotent), outgoing, backlinks, cascade, flags."""

import pytest

from app.repository import (
    ConceptInput,
    EdgeInput,
    SqlConceptRepository,
    SqlEdgeRepository,
)


@pytest.fixture
def concepts(db_session):
    return SqlConceptRepository(db_session)


@pytest.fixture
def edges(db_session):
    return SqlEdgeRepository(db_session)


def _seed(concepts, *ids):
    for cid in ids:
        concepts.upsert(ConceptInput(id=cid, type="Doc"))


def test_replace_for_source_inserts(concepts, edges):
    _seed(concepts, "a", "b")
    edges.replace_for_source("a", [EdgeInput(target_id="b")])
    assert [e.target_id for e in edges.outgoing("a")] == ["b"]


def test_replace_for_source_idempotent(concepts, edges):
    _seed(concepts, "a", "b")
    edges.replace_for_source("a", [EdgeInput(target_id="b")])
    edges.replace_for_source("a", [EdgeInput(target_id="b")])
    assert len(edges.outgoing("a")) == 1


def test_outgoing_returns_targets(concepts, edges):
    _seed(concepts, "a", "b", "c")
    edges.replace_for_source("a", [EdgeInput(target_id="b"), EdgeInput(target_id="c")])
    assert [e.target_id for e in edges.outgoing("a")] == ["b", "c"]


def test_backlinks_returns_sources(concepts, edges):
    _seed(concepts, "a", "b", "target")
    edges.replace_for_source("a", [EdgeInput(target_id="target")])
    edges.replace_for_source("b", [EdgeInput(target_id="target")])
    assert [e.source_id for e in edges.backlinks("target")] == ["a", "b"]


def test_delete_concept_cascades_edges(concepts, edges):
    _seed(concepts, "a", "b")
    edges.replace_for_source("a", [EdgeInput(target_id="b")])
    concepts.delete("a")
    assert edges.outgoing("a") == []


def test_unresolved_edge_flagged(concepts, edges):
    _seed(concepts, "a")
    edges.replace_for_source("a", [EdgeInput(target_id="ghost", resolved=False)])
    out = edges.outgoing("a")
    assert len(out) == 1 and out[0].resolved is False
