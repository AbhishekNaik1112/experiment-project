"""M9 — links API: outgoing + backlinks, 404 for missing concept, unresolved flag."""


def _create(client, id, body="x"):
    return client.post("/concepts", json={"id": id, "type": "Doc", "body": body})


def test_links_outgoing_and_backlinks(client):
    _create(client, "b")
    _create(client, "a", body="see [B](b.md)")

    a_links = client.get("/concepts/a/links").json()
    assert [ln["target_id"] for ln in a_links["outgoing"]] == ["b"]
    assert a_links["backlinks"] == []

    b_links = client.get("/concepts/b/links").json()
    assert [ln["target_id"] for ln in b_links["backlinks"]] == ["a"]
    assert b_links["outgoing"] == []


def test_links_concept_missing_404(client):
    assert client.get("/concepts/ghost/links").status_code == 404


def test_links_unresolved_flagged(client):
    _create(client, "a", body="see [X](missing.md)")
    out = client.get("/concepts/a/links").json()["outgoing"]
    assert out[0]["target_id"] == "missing" and out[0]["resolved"] is False
