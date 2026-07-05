"""M3 — concept repository: CRUD, upsert, type/tag filtering (AND), pagination, totals."""

import pytest

from app.errors import ConflictError, NotFoundError
from app.repository import ConceptInput, SqlConceptRepository


@pytest.fixture
def repo(db_session):
    return SqlConceptRepository(db_session)


def _mk(id="a", type="Doc", tags=None, title=None, bundle="default", body=""):
    return ConceptInput(
        id=id, type=type, tags=tags or [], title=title, bundle=bundle, body=body
    )


def test_upsert_inserts_new(repo):
    repo.upsert(_mk(id="a", type="Doc"))
    got = repo.get("a")
    assert got is not None and got.type == "Doc"


def test_upsert_updates_existing(repo):
    repo.upsert(_mk(id="a", title="v1"))
    repo.upsert(_mk(id="a", title="v2"))
    assert repo.get("a").title == "v2"


def test_get_missing_returns_none(repo):
    assert repo.get("nope") is None


def test_create_new(repo):
    assert repo.create(_mk(id="a")).id == "a"


def test_create_conflict_raises(repo):
    repo.create(_mk(id="a"))
    with pytest.raises(ConflictError):
        repo.create(_mk(id="a"))


def test_update_existing(repo):
    repo.create(_mk(id="a", title="old"))
    repo.update("a", _mk(id="a", title="new"))
    assert repo.get("a").title == "new"


def test_update_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.update("ghost", _mk(id="ghost"))


def test_delete_removes_concept(repo):
    repo.create(_mk(id="a"))
    repo.delete("a")
    assert repo.get("a") is None


def test_delete_missing_raises(repo):
    with pytest.raises(NotFoundError):
        repo.delete("ghost")


def test_list_filter_by_type(repo):
    repo.upsert(_mk(id="a", type="Table"))
    repo.upsert(_mk(id="b", type="Dataset"))
    items, total = repo.list(type="Table")
    assert [c.id for c in items] == ["a"] and total == 1


def test_list_filter_by_tags_AND(repo):
    repo.upsert(_mk(id="a", tags=["x", "y"]))
    repo.upsert(_mk(id="b", tags=["x"]))
    items, total = repo.list(tags=["x", "y"])
    assert [c.id for c in items] == ["a"] and total == 1


def test_list_pagination(repo):
    for i in range(5):
        repo.upsert(_mk(id=f"c{i}"))
    items, total = repo.list(limit=2, offset=2)
    assert [c.id for c in items] == ["c2", "c3"] and total == 5


def test_list_returns_total(repo):
    for i in range(3):
        repo.upsert(_mk(id=f"c{i}"))
    items, total = repo.list(limit=1)
    assert total == 3 and len(items) == 1


def test_list_no_filter_returns_all(repo):
    repo.upsert(_mk(id="a"))
    repo.upsert(_mk(id="b"))
    _, total = repo.list()
    assert total == 2
