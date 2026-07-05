"""M1 — frontmatter parser: type-required, id derivation, structural-file detection,
tag normalization, unknown-key capture."""

import datetime as dt

import pytest

from app.parser import (
    MissingTypeError,
    derive_id,
    is_structural_file,
    parse_concept,
)


def test_parse_minimal_type_only():
    text = "---\ntype: BigQuery Table\n---\nBody here."
    c = parse_concept("tables/users.md", text, bundle="crypto_bitcoin")
    assert c.type == "BigQuery Table"
    assert c.id == "tables/users"
    assert c.bundle == "crypto_bitcoin"
    assert c.body.strip() == "Body here."
    assert c.tags == []
    assert c.title is None
    assert c.extra == {}


def test_parse_full_frontmatter_fields():
    text = (
        "---\n"
        "type: BigQuery Table\n"
        "title: Users\n"
        "description: The users table\n"
        "resource: https://example.com/users\n"
        "tags:\n  - Analytics\n  - Web\n"
        "timestamp: 2026-06-29T00:00:00Z\n"
        "---\n"
        "# Users\n"
    )
    c = parse_concept("users.md", text, bundle="b")
    assert c.title == "Users"
    assert c.description == "The users table"
    assert c.resource == "https://example.com/users"
    assert c.tags == ["analytics", "web"]
    assert c.timestamp == dt.datetime(2026, 6, 29, tzinfo=dt.timezone.utc)


def test_missing_type_raises():
    with pytest.raises(MissingTypeError):
        parse_concept("x.md", "---\ntitle: No type\n---\nbody", bundle="b")


def test_empty_type_raises():
    with pytest.raises(MissingTypeError):
        parse_concept("x.md", "---\ntype: '   '\n---\nbody", bundle="b")


def test_derive_id_strips_md_and_dirs():
    assert derive_id("tables/users.md") == "tables/users"
    assert derive_id("note.md") == "note"


def test_derive_id_normalizes_backslashes():
    assert derive_id("tables\\users.md") == "tables/users"
    assert derive_id("./a/b.md") == "a/b"
    assert derive_id("/a/b.md") == "a/b"


def test_index_md_is_structural():
    assert is_structural_file("index.md")
    assert is_structural_file("datasets/index.md")


def test_log_md_is_structural():
    assert is_structural_file("log.md")
    assert not is_structural_file("tables/users.md")


def test_unknown_keys_go_to_extra():
    text = "---\ntype: T\ncustom_field: 42\nowner: alice\n---\nb"
    c = parse_concept("x.md", text, bundle="b")
    assert c.extra == {"custom_field": 42, "owner": "alice"}


def test_tags_scalar_and_csv_normalized_to_list():
    assert parse_concept("a.md", "---\ntype: T\ntags: solo\n---\n", "b").tags == ["solo"]
    # CSV, mixed case, duplicate -> lowercased, de-duplicated, order preserved
    assert parse_concept("b.md", "---\ntype: T\ntags: a, B, a\n---\n", "b").tags == ["a", "b"]
