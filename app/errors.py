"""Domain exceptions. Routers map these to HTTP status codes in one place (see main.py)."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected, mappable domain errors."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""


class ConflictError(DomainError):
    """An entity already exists (e.g. creating a concept with a taken ID)."""
