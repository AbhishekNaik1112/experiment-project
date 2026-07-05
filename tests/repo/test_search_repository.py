"""M5 — search repository: Postgres tsvector full-text, ts_rank_cd ordering, filters, sync."""

import pytest

from app.repository import ConceptInput, SqlConceptRepository, SqlSearchRepository


@pytest.fixture
def concepts(db_session):
    return SqlConceptRepository(db_session)


@pytest.fixture
def search(db_session):
    return SqlSearchRepository(db_session)


def _c(concepts, id, type="Doc", title=None, description=None, body="", tags=None):
    concepts.upsert(
        ConceptInput(
            id=id, type=type, title=title, description=description, body=body, tags=tags or []
        )
    )


def test_fts_finds_by_title(concepts, search):
    _c(concepts, "a", title="Bitcoin Ledger")
    hits, total = search.search("bitcoin")
    assert [h.id for h in hits] == ["a"] and total == 1


def test_fts_finds_by_body(concepts, search):
    _c(concepts, "a", body="the ethereum blockchain")
    hits, _ = search.search("ethereum")
    assert [h.id for h in hits] == ["a"]


def test_ts_rank_orders_by_relevance(concepts, search):
    _c(concepts, "low", body="bitcoin")
    _c(concepts, "high", title="Bitcoin", body="bitcoin bitcoin bitcoin ledger")
    hits, _ = search.search("bitcoin")
    assert hits[0].id == "high"


def test_fts_filter_by_type(concepts, search):
    _c(concepts, "a", type="Table", body="bitcoin")
    _c(concepts, "b", type="Dataset", body="bitcoin")
    hits, total = search.search("bitcoin", type="Table")
    assert [h.id for h in hits] == ["a"] and total == 1


def test_fts_filter_by_tag(concepts, search):
    _c(concepts, "a", body="bitcoin", tags=["crypto"])
    _c(concepts, "b", body="bitcoin", tags=["web"])
    hits, total = search.search("bitcoin", tags=["crypto"])
    assert [h.id for h in hits] == ["a"] and total == 1


def test_fts_synced_on_update(concepts, search):
    _c(concepts, "a", body="original text")
    concepts.upsert(ConceptInput(id="a", type="Doc", body="updated dogecoin"))
    assert [h.id for h in search.search("dogecoin")[0]] == ["a"]
    assert search.search("original")[0] == []


def test_fts_synced_on_delete(concepts, search):
    _c(concepts, "a", body="bitcoin")
    concepts.delete("a")
    assert search.search("bitcoin")[0] == []


def test_search_snippet_present(concepts, search):
    _c(concepts, "a", body="the bitcoin ledger records transactions")
    hits, _ = search.search("bitcoin")
    assert hits[0].snippet is not None
