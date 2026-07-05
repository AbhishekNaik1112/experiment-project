"""GitHub push webhook — verify HMAC signature, then re-ingest the repo in the background."""

from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request

from app.config import Settings, get_settings
from app.dependencies import get_repo_syncer
from app.webhook import RepoSyncer, verify_signature

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/github", status_code=202)
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    syncer: RepoSyncer = Depends(get_repo_syncer),
) -> dict[str, str]:
    if not settings.github_webhook_secret:
        raise HTTPException(status_code=503, detail="webhook not configured")

    body = await request.body()
    if not verify_signature(settings.github_webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = json.loads(body or b"{}")
    background.add_task(syncer.sync, payload)
    return {"status": "accepted"}
