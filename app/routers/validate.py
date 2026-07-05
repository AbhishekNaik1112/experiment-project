"""Validation endpoint — check an OKF bundle against the spec rules WITHOUT persisting anything."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.bundle import read_dir, read_zip
from app.models import ValidationIssueOut, ValidationReport
from app.rules import validate_bundle

router = APIRouter(tags=["validate"])


@router.post("/validate", response_model=ValidationReport)
async def validate(
    path: str | None = Query(None, description="server-side directory of an OKF bundle"),
    file: UploadFile | None = File(None),
) -> ValidationReport:
    if file is not None:
        bundle_name = "uploaded"
        entries = read_zip(await file.read())
    elif path is not None:
        try:
            bundle_name, entries = read_dir(path)
        except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        raise HTTPException(status_code=400, detail="provide a zip file or a directory path")

    result = validate_bundle([(e.rel_path, e.text) for e in entries])
    has_errors = any(issue.severity == "error" for issue in result.issues)
    return ValidationReport(
        bundle=bundle_name,
        valid=not has_errors,
        concept_count=result.concept_count,
        issues=[ValidationIssueOut(**asdict(issue)) for issue in result.issues],
    )
