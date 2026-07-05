"""M2 — markdown link extraction + resolution of relative hrefs to concept IDs."""

from app.links import RawLink, extract_links, resolve_target


def test_extract_single_link():
    links = extract_links("See [Users](tables/users.md) for detail.")
    assert links == [RawLink(anchor_text="Users", href="tables/users.md")]


def test_extract_multiple_links():
    links = extract_links("[A](a.md) and [B](b.md)")
    assert [ln.href for ln in links] == ["a.md", "b.md"]
    assert [ln.anchor_text for ln in links] == ["A", "B"]


def test_images_are_not_links():
    assert extract_links("![alt](pic.png)") == []


def test_body_without_links_returns_empty():
    assert extract_links("no links here") == []


def test_resolve_relative_against_source_dir():
    assert resolve_target("tables/users", "orders.md") == "tables/orders"
    assert resolve_target("tables/users", "../datasets/bitcoin.md") == "datasets/bitcoin"


def test_resolve_strips_md():
    assert resolve_target("a", "b.md") == "b"


def test_resolve_absolute_bundle_path():
    assert resolve_target("tables/users", "/datasets/x.md") == "datasets/x"


def test_ignore_external_http_links():
    assert resolve_target("a", "https://example.com/x") is None
    assert resolve_target("a", "http://example.com") is None
    assert resolve_target("a", "mailto:foo@bar.com") is None


def test_ignore_anchor_only_links():
    assert resolve_target("a", "#section") is None


def test_resolve_drops_fragment():
    assert resolve_target("tables/users", "orders.md#schema") == "tables/orders"
