"""M7 — list/filter API: pagination, type + tags(AND) filters, page shape, validation."""


def _create(client, id, **over):
    body = {"id": id, "type": "Doc"}
    body.update(over)
    return client.post("/concepts", json=body)


def test_list_default_pagination(client):
    for i in range(3):
        _create(client, f"c{i}")
    data = client.get("/concepts").json()
    assert data["total"] == 3
    assert data["limit"] == 50 and data["offset"] == 0
    assert len(data["items"]) == 3


def test_list_filter_type(client):
    _create(client, "a", type="Table")
    _create(client, "b", type="Dataset")
    data = client.get("/concepts", params={"type": "Table"}).json()
    assert [i["id"] for i in data["items"]] == ["a"] and data["total"] == 1


def test_list_filter_tags_AND(client):
    _create(client, "a", tags=["x", "y"])
    _create(client, "b", tags=["x"])
    r = client.get("/concepts?tags=x&tags=y")
    data = r.json()
    assert [i["id"] for i in data["items"]] == ["a"] and data["total"] == 1


def test_list_page_shape(client):
    for i in range(5):
        _create(client, f"c{i}")
    data = client.get("/concepts", params={"limit": 2, "offset": 2}).json()
    assert set(data) == {"items", "total", "limit", "offset"}
    assert [i["id"] for i in data["items"]] == ["c2", "c3"]
    assert data["total"] == 5


def test_list_bad_pagination_422(client):
    assert client.get("/concepts", params={"limit": 0}).status_code == 422
    assert client.get("/concepts", params={"limit": 999}).status_code == 422
    assert client.get("/concepts", params={"offset": -1}).status_code == 422
