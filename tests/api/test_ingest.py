"""M10 — ingest end-to-end against a trimmed REAL crypto_bitcoin OKF bundle."""

import io
import zipfile
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "bundles" / "crypto_bitcoin"


def test_ingest_dir_path(client):
    r = client.post("/ingest", params={"path": str(FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert body["bundle"] == "crypto_bitcoin"
    assert body["created"] == 3  # dataset + 2 tables
    assert body["skipped"] == 3  # 3 index.md files
    assert body["errors"] == []


def test_ingest_skips_index_and_log(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    assert client.get("/concepts/index").status_code == 404
    assert client.get("/concepts/datasets/index").status_code == 404
    assert client.get("/concepts").json()["total"] == 3


def test_ingest_populates_edges(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    links = client.get("/concepts/datasets/crypto_bitcoin/links").json()
    resolved = {ln["target_id"]: ln["resolved"] for ln in links["outgoing"]}
    assert resolved["tables/blocks"] is True
    assert resolved["tables/transactions"] is True
    # inputs/outputs are linked but not in the trimmed fixture -> dangling
    assert resolved["tables/inputs"] is False
    assert resolved["tables/outputs"] is False


def test_ingest_is_idempotent_on_reingest(client):
    client.post("/ingest", params={"path": str(FIXTURE)})
    second = client.post("/ingest", params={"path": str(FIXTURE)}).json()
    assert second["created"] == 0 and second["updated"] == 3
    assert client.get("/concepts").json()["total"] == 3


def test_ingest_zip(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in FIXTURE.rglob("*.md"):
            zf.write(p, p.relative_to(FIXTURE).as_posix())
    r = client.post(
        "/ingest",
        params={"bundle": "crypto_bitcoin"},
        files={"file": ("bundle.zip", buf.getvalue(), "application/zip")},
    )
    assert r.status_code == 200 and r.json()["created"] == 3


def test_ingest_type_errors_nonfatal(client, tmp_path):
    (tmp_path / "good.md").write_text("---\ntype: Doc\n---\nok", encoding="utf-8")
    (tmp_path / "bad.md").write_text("---\ntitle: no type\n---\nnope", encoding="utf-8")
    body = client.post("/ingest", params={"path": str(tmp_path)}).json()
    assert body["created"] == 1
    assert [e["path"] for e in body["errors"]] == ["bad.md"]
