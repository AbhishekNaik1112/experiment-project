"""M13 — GitHub webhook: HMAC-SHA256 verification + background re-ingest."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db import get_session
from app.dependencies import get_repo_syncer
from app.main import create_app
from app.webhook import verify_signature

SECRET = "whsecret"


def _sig(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


class _SpySyncer:
    def __init__(self):
        self.calls: list[dict] = []

    def sync(self, payload: dict) -> None:
        self.calls.append(payload)


@pytest.fixture
def webhook_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(github_webhook_secret=SECRET)
    spy = _SpySyncer()
    app.dependency_overrides[get_repo_syncer] = lambda: spy
    with TestClient(app) as c:
        yield c, spy
    app.dependency_overrides.clear()


def test_verify_signature_valid():
    body = b'{"a":1}'
    assert verify_signature(SECRET, body, _sig(body))


def test_verify_signature_invalid():
    assert not verify_signature(SECRET, b"{}", "sha256=deadbeef")


def test_verify_signature_missing():
    assert not verify_signature(SECRET, b"{}", None)


def test_webhook_valid_signature_accepts_and_syncs(webhook_client):
    client, spy = webhook_client
    body = json.dumps({"repository": {"clone_url": "https://x/y.git", "name": "y"}}).encode()
    r = client.post("/webhooks/github", content=body, headers={"X-Hub-Signature-256": _sig(body)})
    assert r.status_code == 202
    assert len(spy.calls) == 1
    assert spy.calls[0]["repository"]["name"] == "y"


def test_webhook_bad_signature_401(webhook_client):
    client, spy = webhook_client
    r = client.post(
        "/webhooks/github", content=b"{}", headers={"X-Hub-Signature-256": "sha256=deadbeef"}
    )
    assert r.status_code == 401 and spy.calls == []


def test_webhook_missing_signature_401(webhook_client):
    client, spy = webhook_client
    r = client.post("/webhooks/github", content=b"{}")
    assert r.status_code == 401 and spy.calls == []
