"""FastAPI application factory. Registers routers and maps domain errors to HTTP responses."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import get_settings
from app.errors import ConflictError, NotFoundError
from app.routers import concepts, graph, ingest, search, ui, validate, webhooks


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Cloud has no manual migration step; create the schema on boot (idempotent) when asked.
    if get_settings().auto_init_db:
        from app.db import init_db, make_engine

        init_db(make_engine())
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="OKF Knowledge Catalog API", version="0.1.0", lifespan=_lifespan)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ui")

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc), "code": "not_found"})

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc), "code": "conflict"})

    app.include_router(concepts.router)
    app.include_router(search.router)
    app.include_router(ingest.router)
    app.include_router(validate.router)
    app.include_router(webhooks.router)
    app.include_router(graph.router)
    app.include_router(ui.router)

    return app


app = create_app()
