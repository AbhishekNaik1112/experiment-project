"""M8 — search API: ranked hits, filters, snippet, empty-query validation."""


def _create(client, id, **over):
    body = {"id": id, "type": "Doc"}
    body.update(over)
    return client.post("/concepts", json=body)


def test_search_ranked_hits(client):
    _create(client, "low", body="bitcoin")
    _create(client, "high", title="Bitcoin", body="bitcoin bitcoin bitcoin ledger")
    items = client.get("/search", params={"q": "bitcoin"}).json()["items"]
    assert items[0]["id"] == "high"


def test_search_empty_q_422(client):
    assert client.get("/search", params={"q": ""}).status_code == 422
    assert client.get("/search").status_code == 422


def test_search_filter_type(client):
    _create(client, "a", type="Table", body="bitcoin")
    _create(client, "b", type="Dataset", body="bitcoin")
    data = client.get("/search", params={"q": "bitcoin", "type": "Table"}).json()
    assert [i["id"] for i in data["items"]] == ["a"] and data["total"] == 1


def test_search_filter_tag(client):
    _create(client, "a", body="bitcoin", tags=["crypto"])
    _create(client, "b", body="bitcoin", tags=["web"])
    data = client.get("/search?q=bitcoin&tags=crypto").json()
    assert [i["id"] for i in data["items"]] == ["a"] and data["total"] == 1


def test_search_snippet_present(client):
    _create(client, "a", body="the bitcoin ledger records transactions")
    hit = client.get("/search", params={"q": "bitcoin"}).json()["items"][0]
    assert hit["snippet"] is not None
