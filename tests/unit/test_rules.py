"""M11 (Phase B) — OKF validation rules: missing type, duplicate id, dangling links."""

from app.rules import validate_bundle


def test_valid_bundle_no_issues():
    r = validate_bundle(
        [
            ("a.md", "---\ntype: Doc\n---\nsee [b](b.md)"),
            ("b.md", "---\ntype: Doc\n---\nok"),
        ]
    )
    assert r.issues == []
    assert r.concept_count == 2


def test_missing_type_is_error():
    r = validate_bundle([("bad.md", "---\ntitle: no type\n---\nx")])
    assert len(r.issues) == 1
    issue = r.issues[0]
    assert issue.rule == "missing_type" and issue.severity == "error" and issue.path == "bad.md"
    assert r.concept_count == 0


def test_dangling_link_is_warning():
    r = validate_bundle([("a.md", "---\ntype: Doc\n---\nsee [ghost](ghost.md)")])
    assert len(r.issues) == 1
    issue = r.issues[0]
    assert issue.rule == "dangling_link" and issue.severity == "warning"
    assert issue.concept_id == "a"


def test_structural_files_skipped():
    r = validate_bundle(
        [
            ("index.md", "no frontmatter, just links to [a](a.md)"),
            ("a.md", "---\ntype: Doc\n---\nx"),
        ]
    )
    assert r.issues == []
    assert r.concept_count == 1


def test_duplicate_id_is_error():
    # 'a.md' and './a.md' both derive concept id 'a'
    r = validate_bundle(
        [
            ("a.md", "---\ntype: Doc\n---\n"),
            ("./a.md", "---\ntype: Doc\n---\n"),
        ]
    )
    assert any(i.rule == "duplicate_id" and i.severity == "error" for i in r.issues)
