"""GitHub webhook signature verification + repo sync.

Security: GitHub signs each delivery with HMAC-SHA256 over the raw body in `X-Hub-Signature-256`.
Verify against the shared secret with a constant-time compare BEFORE trusting any payload field.
"""

from __future__ import annotations

import hashlib
import hmac
import subprocess
import tempfile

from sqlalchemy.orm import Session

from app.db import make_engine
from app.ingest import IngestService
from app.repository import SqlConceptRepository, SqlEdgeRepository


def verify_signature(secret: str, body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


class RepoSyncer:
    """Clone the pushed repo (shallow) and ingest it. Runs in a background task, own DB session."""

    def sync(self, payload: dict) -> None:
        repo = payload.get("repository", {})
        clone_url = repo.get("clone_url")
        if not clone_url:
            return
        name = repo.get("name", "default")
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, tmp],
                check=True,
                capture_output=True,
            )
            with Session(make_engine()) as session:
                service = IngestService(
                    SqlConceptRepository(session), SqlEdgeRepository(session), session
                )
                service.ingest_dir(tmp, bundle=name)
