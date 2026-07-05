"""API-key auth for write endpoints.

If no `api_key` is configured, auth is disabled (open) — convenient for local/self-host. Once a key
is set, mutating requests must send it in the `X-API-Key` header (constant-time compared).
"""

from __future__ import annotations

import hmac

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings


def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.api_key is None:
        return
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="missing API key")
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="invalid API key")
