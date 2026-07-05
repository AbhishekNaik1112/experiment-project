# OKF Knowledge Catalog API

A REST service that ingests **OKF (Open Knowledge Format)** bundles — Markdown files with YAML
frontmatter — parses them into PostgreSQL, and exposes CRUD, filtering, full-text search, and a
cross-link graph over the concepts.

Built test-first (TDD). Free stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL (`tsvector` full-text,
`pgvector`-ready for semantic search).

## Requirements
- Python 3.11+
- Docker (for the local Postgres+pgvector container)

## Setup

```bash
# 1. Start Postgres (pgvector) on host port 5433
docker compose up -d

# 2. Create a virtualenv and install
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
# .venv/bin/python -m pip install -e ".[dev]"      # macOS/Linux

# 3. Apply the schema to the dev database
.venv/Scripts/python -c "from app.db import make_engine, init_db; init_db(make_engine())"

# 4. Run
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive Swagger UI.

## Tests

```bash
docker compose up -d          # tests run against the okf_test database
.venv/Scripts/python -m pytest
```

The suite uses a session-scoped engine with a per-test transaction rollback (fast, isolated), and
ingests a trimmed real `crypto_bitcoin` bundle as an end-to-end fixture.

## API (Phase A)

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/ingest?path=<dir>` or zip upload | Parse a bundle, upsert concepts + edges |
| `GET` | `/concepts?type=&tags=&limit=&offset=` | List/filter concepts (tags = AND) |
| `POST` | `/concepts` | Create a concept |
| `GET` | `/concepts/{id}?render=true` | Fetch one (optional Markdown→HTML) |
| `PUT` / `DELETE` | `/concepts/{id}` | Update / delete |
| `GET` | `/concepts/{id}/links` | Outgoing links + backlinks |
| `GET` | `/search?q=&type=&tags=` | Full-text search (ts_rank_cd ordered) |

Also: `POST /validate` (lint a bundle, no persist), `POST /webhooks/github` (HMAC-verified auto-ingest),
`GET /graph` (nodes + edges JSON). Search supports `?mode=keyword|semantic|hybrid` (semantic needs the
`[semantic]` extra + `EMBEDDINGS_ENABLED=true`).

Concept IDs are the file path within the bundle minus `.md` (e.g. `tables/users`), so routes use a
path converter — slashes in IDs work.

## Web UI

A server-rendered UI (Jinja + htmx) lives under `/ui`:
- `/ui` — browse concepts with a live search box
- `/ui/concepts/{id}` — rendered Markdown + outgoing links / backlinks
- `/ui/graph` — interactive Cytoscape.js graph of the cross-links

## Roadmap
Phase A (core MVP) ✅ · B: OKF validator · C: API-key auth + GitHub webhook · D: semantic/hybrid
search (pgvector) · E: web UI + graph · F: deploy (Render + Neon).

## Notes
- OKF spec: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md> (Apache-2.0).
- `/ingest?path=` reads a server-side directory — intended for local/self-host use; gate behind auth
  before exposing publicly (Phase C).
