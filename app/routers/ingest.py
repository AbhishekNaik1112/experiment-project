"""Ingest endpoint — accepts a directory path (query) or an uploaded .zip bundle (multipart)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.dependencies import get_ingest_service
from app.ingest import IngestService
from app.models import IngestResult
from app.security import require_api_key

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResult, dependencies=[Depends(require_api_key)])
async def ingest(
    path: str | None = Query(None, description="server-side directory of an OKF bundle"),
    bundle: str | None = Query(None),
    file: UploadFile | None = File(None),
    svc: IngestService = Depends(get_ingest_service),
) -> IngestResult:
    if file is not None:
        return svc.ingest_zip(await file.read(), bundle=bundle or "default")
    if path is not None:
        try:
            return svc.ingest_dir(path, bundle=bundle)
        except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(status_code=400, detail="provide a zip file or a directory path")
