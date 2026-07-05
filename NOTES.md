# NOTES — in-flight progress

## Status: Phase A (core MVP) COMPLETE ✅ — 82 tests green, drive-verified

### Done (M0–M10)
- M0 harness: docker-compose pg+pgvector (host **port 5433** — host has its own PG on 5432),
  SQLAlchemy models, pytest transaction-rollback fixture.
- M1 parser, M2 links (pure). M3 concept repo, M4 edge repo, M5 tsvector search repo.
- M6 CRUD API, M7 list/filter, M8 search, M9 links, M10 ingest (real crypto_bitcoin fixture).
- Verified by driving the running app: ingest→list→search→links→render all work.

### Environment gotchas (important for next session)
- **Postgres runs in Docker on host port 5433**, not 5432 (a host-installed PG occupies 5432).
  URLs: `postgresql+psycopg://okf:okf@localhost:5433/okf` (dev) and `.../okf_test` (tests).
- Docker Desktop must be running before tests. `docker compose up -d` then wait healthy.
- Dev DB `okf` schema was applied manually via `init_db`. No Alembic migrations authored yet
  (planned; needed for Neon deploy in Phase F).
- Cosmetic warning: starlette TestClient nudges "install httpx2" — ignore.

### Next up
- **Phase B** — OKF validator: `rules.py` + `POST /validate` (type-required, dup-id, dangling links),
  returns report without persisting.
- Then C (auth+webhook), D (semantic search — add `sentence-transformers`, hnsw index, hybrid rank),
  E (web UI+graph), F (deploy: author Alembic migrations, provision Neon via MCP, Render).

### Commands
```
docker compose up -d
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload
```
