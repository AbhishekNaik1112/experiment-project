"""Pydantic v2 API DTOs — the wire contract, decoupled from ORM rows."""

from __future__ import annotations

import datetime as dt
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.parser import normalize_tags

T = TypeVar("T")


class ConceptBase(BaseModel):
    type: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    resource: str | None = None
    tags: list[str] = []
    timestamp: dt.datetime | None = None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v: list[str]) -> list[str]:
        return normalize_tags(v)


class ConceptCreate(ConceptBase):
    id: str = Field(min_length=1)
    bundle: str = "default"
    body: str = ""


class ConceptUpdate(ConceptBase):
    body: str = ""


class ConceptOut(ConceptBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bundle: str
    body: str
    html: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class ConceptListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bundle: str
    type: str
    title: str | None
    description: str | None
    tags: list[str]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class SearchHitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str | None
    description: str | None
    score: float
    snippet: str | None


class LinkOut(BaseModel):
    target_id: str
    anchor_text: str | None
    resolved: bool


class LinksResponse(BaseModel):
    id: str
    outgoing: list[LinkOut]
    backlinks: list[LinkOut]


class ValidationIssueOut(BaseModel):
    path: str
    concept_id: str | None
    rule: str
    severity: str
    message: str


class ValidationReport(BaseModel):
    bundle: str
    valid: bool
    concept_count: int
    issues: list[ValidationIssueOut]


class IngestError(BaseModel):
    path: str
    reason: str


class IngestResult(BaseModel):
    bundle: str
    created: int
    updated: int
    skipped: int
    errors: list[IngestError] = []
