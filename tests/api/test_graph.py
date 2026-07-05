"""M17 — /graph JSON: nodes = concepts, edges = resolved cross-links only."""


def _create(client, id, body="x"):
    return client.post("/concepts", json={"id": id, "type": "Doc", "body": body})


def test_graph_nodes_and_edges(client):
    _create(client, "b")
    _create(client, "a", body="see [B](b.md)")
    g = client.get("/graph").json()
    assert {n["id"] for n in g["nodes"]} == {"a", "b"}
    pairs = {(e["source"], e["target"]) for e in g["edges"]}
    assert ("a", "b") in pairs


def test_graph_excludes_dangling(client):
    _create(client, "a", body="see [X](missing.md)")
    g = client.get("/graph").json()
    node_ids = {n["id"] for n in g["nodes"]}
    assert all(e["target"] in node_ids for e in g["edges"])
    assert g["edges"] == []
