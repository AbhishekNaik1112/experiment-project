"""M11 (Phase B) — validate API: reports issues without persisting."""

from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "bundles" / "crypto_bitcoin"


def test_validate_real_bundle_reports_dangling(client):
    body = client.post("/validate", params={"path": str(FIXTURE)}).json()
    assert body["bundle"] == "crypto_bitcoin"
    assert body["concept_count"] == 3
    assert body["valid"] is True  # no missing-type errors
    dangling = [i for i in body["issues"] if i["rule"] == "dangling_link"]
    messages = " ".join(i["message"] for i in dangling)
    assert "inputs" in messages and "outputs" in messages


def test_validate_missing_type_invalid(client, tmp_path):
    (tmp_path / "good.md").write_text("---\ntype: Doc\n---\nx", encoding="utf-8")
    (tmp_path / "bad.md").write_text("---\ntitle: no type\n---\ny", encoding="utf-8")
    body = client.post("/validate", params={"path": str(tmp_path)}).json()
    assert body["valid"] is False
    assert any(i["rule"] == "missing_type" for i in body["issues"])


def test_validate_no_input_400(client):
    assert client.post("/validate").status_code == 400


def test_validate_does_not_persist(client, tmp_path):
    (tmp_path / "a.md").write_text("---\ntype: Doc\n---\nx", encoding="utf-8")
    client.post("/validate", params={"path": str(tmp_path)})
    assert client.get("/concepts").json()["total"] == 0
