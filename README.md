# Knowledge Atlas

*A Knowledge Catalog API for OKF (Open Knowledge Format) bundles — REST + web UI over a Markdown knowledge graph.*

A backend service that ingests **OKF (Open Knowledge Format)** bundles — directories of Markdown files
with YAML frontmatter — into PostgreSQL and exposes them through a REST API and a small web UI: CRUD,
tag/type filtering, full-text and semantic search, a validator, a GitHub auto-sync webhook, and an
interactive cross-link graph.

Built **test-first (TDD)** on an entirely **free / open-source stack**. 116 tests, no paid services.

> OKF is Google's open, vendor-neutral format for knowledge-as-files. Each concept is one Markdown file
> with a small YAML header (`type` is the only required field); concepts cross-link with normal Markdown
> links, forming a graph. Spec: <https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md> (Apache-2.0).

---

## Features

- **Ingest** an OKF bundle from a directory or a `.zip` — parses frontmatter, derives concept IDs from
  paths, skips `index.md`/`log.md`, extracts cross-links into a graph, and is idempotent on re-ingest.
- **CRUD** over concepts with slash-containing IDs (e.g. `tables/users`).
- **Filter** by `type` and `tags` (AND semantics via Postgres arrays), paginated.
- **Full-text search** (`tsvector` + `ts_rank_cd`), with an optional **semantic** mode (local
  `sentence-transformers` embeddings + `pgvector` cosine) and a **hybrid** mode (reciprocal-rank fusion).
- **Link graph** — outgoing links, backlinks, and a whole-catalog `/graph` JSON.
- **Validator** — lint a bundle for missing `type`, duplicate IDs, and dangling links (no persistence).
- **GitHub webhook** — HMAC-SHA256-verified push → background re-ingest.
- **API-key auth** on write endpoints (opt-in).
- **Web UI** — browse, live search, rendered Markdown, and a Cytoscape link graph.

## Architecture

Layered and test-driven: pure functions (`parser`, `links`, `rules`) → repositories (SQL behind a thin
surface) → services (`ConceptService`, `IngestService`) → HTTP routers. One request = one session /
unit of work. See `NOTES.md` for the build log.

```
app/
  main.py            app factory + error handlers        parser.py    frontmatter → ParsedConcept
  db.py              SQLAlchemy models + engine           links.py     markdown link extraction/resolution
  config.py          pydantic-settings                    rules.py     bundle validation
  models.py          Pydantic API DTOs                    bundle.py    dir/zip reader
  repository.py      concept / edge / search repos        ingest.py    IngestService (parse→persist→embed)
  services.py        ConceptService (write + edge sync)   embeddings.py sentence-transformers (lazy)
  security.py        API-key dependency                   webhook.py   HMAC verify + RepoSyncer
  render.py          markdown → HTML
  routers/           concepts, search, ingest, validate, webhooks, graph, ui
  templates/         Jinja + htmx pages
tests/               unit / repo / api  (+ real crypto_bitcoin fixture)
```

---

## Requirements

- Python 3.11+
- Docker (runs the local Postgres + `pgvector` container)

## Quickstart

```bash
# 1. Start Postgres (pgvector) — mapped to host port 5433 to avoid a host Postgres on 5432
docker compose up -d

# 2. Virtualenv + install
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows
# .venv/bin/python -m pip install -e ".[dev]"        # macOS/Linux

# 3. Create the schema on the dev database
.venv/Scripts/python -c "from app.db import make_engine, init_db; init_db(make_engine())"

# 4. Run
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Then load some data and open the UI:

```bash
# ingest the bundled sample (real trimmed Bitcoin OKF bundle)
curl -X POST "http://127.0.0.1:8000/ingest?path=tests/fixtures/bundles/crypto_bitcoin"
```

- Web UI:   http://127.0.0.1:8000/ui
- Graph:    http://127.0.0.1:8000/ui/graph
- Swagger:  http://127.0.0.1:8000/docs

## Environment variables

All optional; sensible local defaults. Copy `.env.example` to `.env` to override.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://okf:okf@localhost:5433/okf` | Postgres connection |
| `API_KEY` | *(unset → auth off)* | When set, writes require `X-API-Key` |
| `GITHUB_WEBHOOK_SECRET` | *(unset → webhook 503)* | HMAC secret for `/webhooks/github` |
| `EMBEDDINGS_ENABLED` | `false` | Compute embeddings on ingest + enable semantic/hybrid search |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model (384-dim) |

---

## API reference

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/ingest?path=<dir>` or multipart `file=<zip>` | Parse bundle → upsert concepts + edges. Idempotent. *(write: API key)* |
| `GET` | `/concepts?type=&tags=&limit=&offset=` | List/filter; repeat `tags` for AND |
| `POST` | `/concepts` | Create *(write: API key)* |
| `GET` | `/concepts/{id}?render=true` | Fetch; `render=true` adds HTML |
| `PUT` / `DELETE` | `/concepts/{id}` | Update / delete *(write: API key)* |
| `GET` | `/concepts/{id}/links` | Outgoing links + backlinks |
| `GET` | `/search?q=&mode=&type=&tags=` | `mode=keyword` (default) / `semantic` / `hybrid` |
| `POST` | `/validate?path=` or zip | Lint a bundle; returns issues, **does not persist** |
| `POST` | `/webhooks/github` | Verify `X-Hub-Signature-256`, background re-ingest |
| `GET` | `/graph` | `{nodes, edges}` for the whole catalog |
| `GET` | `/health` | Liveness |

Concept IDs are the file path within the bundle minus `.md` (e.g. `tables/users`), so every `{id}` route
uses a path converter — slashes work.

## Web UI

Server-rendered (Jinja + htmx), under `/ui`:

- `/ui` — browse all concepts with a live (debounced) search box
- `/ui/concepts/{id}` — rendered Markdown, metadata, tags, outgoing links + backlinks
- `/ui/graph` — interactive Cytoscape.js graph of the cross-links

## Search modes

- **keyword** (default) — Postgres `tsvector`, BM-like `ts_rank_cd` ordering, `ts_headline` snippets.
- **semantic** / **hybrid** — require `pip install -e ".[semantic]"` and `EMBEDDINGS_ENABLED=true`.
  Embeddings (`all-MiniLM-L6-v2`, run locally, free) are stored in a `pgvector` column with an hnsw
  cosine index; **hybrid** fuses keyword and vector rankings via reciprocal-rank fusion.

---

## Testing

```bash
docker compose up -d                      # tests use the okf_test database
.venv/Scripts/python -m pytest            # 116 tests
```

Each test runs inside a transaction that rolls back (fast, isolated) against real Postgres. The ingest
suite exercises a trimmed **real** `crypto_bitcoin` OKF bundle. The heavy real-model embedding test is
opt-in:

```bash
pip install -e ".[semantic]"
OKF_REAL_EMBED=1 .venv/Scripts/python -m pytest tests/unit/test_embeddings_real.py
```

---

## Notes & caveats

- **Postgres is on host port 5433** (not 5432) so it doesn't clash with a locally-installed Postgres.
- **SQLite is intentionally not used** — Postgres gives `tsvector`, `pgvector`, and cloud durability.
- **Schema is created via `init_db`** today; Alembic migrations are planned for deployment.
- **`/ingest?path=` reads a server-side directory** — meant for local/self-host use. Set `API_KEY`
  before exposing it publicly.
- **Embeddings are heavy** (torch): keep `EMBEDDINGS_ENABLED=false` on small/free hosts. Keyword search,
  validator, UI, and webhook all work without it.

## Roadmap

Phase A core MVP ✅ · B validator ✅ · C auth + webhook ✅ · D semantic/hybrid search ✅ · E web UI + graph ✅
· **F deploy (Render + Neon) — not yet done.**

License of the referenced OKF spec/samples: Apache-2.0.
