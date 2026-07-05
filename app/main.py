"""FastAPI application factory. Registers routers and maps domain errors to HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import ConflictError, NotFoundError
from app.routers import concepts, search


def create_app() -> FastAPI:
    app = FastAPI(title="OKF Knowledge Catalog API", version="0.1.0")

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

    return app


app = create_app()
