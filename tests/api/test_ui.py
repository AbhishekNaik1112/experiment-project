"""M16 — web UI pages render concepts, markdown, links, and search."""


def _create(client, id, **over):
    body = {"id": id, "type": "Doc"}
    body.update(over)
    return client.post("/concepts", json=body)


def test_ui_home_lists_concepts(client):
    _create(client, "a", title="Alpha")
    r = client.get("/ui")
    assert r.status_code == 200 and "Alpha" in r.text


def test_ui_concept_renders_markdown(client):
    _create(client, "a", title="Alpha", body="# Heading")
    r = client.get("/ui/concepts/a")
    assert r.status_code == 200 and "<h1>Heading</h1>" in r.text


def test_ui_concept_shows_outgoing_link(client):
    _create(client, "b")
    _create(client, "a", body="see [B](b.md)")
    r = client.get("/ui/concepts/a")
    assert "/ui/concepts/b" in r.text


def test_ui_search_partial_filters(client):
    _create(client, "a", title="Bitcoin", body="ledger")
    _create(client, "b", title="Banana", body="fruit")
    r = client.get("/ui/search", params={"q": "bitcoin"})
    assert r.status_code == 200 and "Bitcoin" in r.text and "Banana" not in r.text


def test_ui_missing_concept_404(client):
    assert client.get("/ui/concepts/ghost").status_code == 404


def test_ui_graph_page_loads_cytoscape(client):
    r = client.get("/ui/graph")
    assert r.status_code == 200 and "cytoscape" in r.text.lower()


def test_root_redirects_to_ui(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/ui"
