# NOTES — in-flight progress

## Status: Phases A–E done + Phase F artifacts ready ✅ — 119 tests green (+2 opt-in real-model)

### Phase F (deploy) — artifacts done; Render step is user-interactive
- **Neon** project `wild-salad-94185066` (db `neondb`) provisioned; schema/pgvector/hnsw verified + seeded
  with crypto_bitcoin (3 concepts). Connection string is a secret (not in repo).
- **Dockerfile** (slim, no torch) + **.dockerignore** + **render.yaml** Blueprint pushed.
- `config.py` normalizes bare `postgresql://`→`postgresql+psycopg://`; `main.py` lifespan runs `init_db`
  on boot when `AUTO_INIT_DB=true`. Templates shipped via package-data.
- **Docker image built + run against Neon, verified**: ingest(zip)=3, search ranked, /ui 200.
- LEFT (user, dashboard): Render → New → Blueprint → connect `knowledge-atlas` repo → set `DATABASE_URL`
  (Neon) + `GITHUB_WEBHOOK_SECRET` → deploy. Then optionally wire the GitHub push webhook.
- Note: `.venv` editable pointer went stale after the folder rename — run from the project root (cwd on
  path) or `pip install -e .` to refresh; tests/uvicorn work from the root regardless.

### Phase E (web UI + graph) — done
- `GET /graph` JSON (nodes=concepts, edges=resolved links only); dangling edges dropped.
- Jinja + htmx UI: `/ui` (browse + live search box), `/ui/concepts/{id}` (rendered MD + links/backlinks),
  `/ui/graph` (Cytoscape.js via CDN reading `/graph`). Templates in `app/templates/`.
- Drive-verified: /graph 3 nodes/4 edges on crypto_bitcoin, slash-id concept page renders.

### Phase D (semantic / hybrid search) — done
- `app/embeddings.py`: `SentenceTransformerEmbedder` (all-MiniLM-L6-v2, 384d) — **lazy** torch import.
- `embedding vector(384)` col + hnsw cosine index; populated on ingest when `EMBEDDINGS_ENABLED=true`.
- Search `?mode=keyword|semantic|hybrid`; hybrid = RRF of ts_rank + cosine. Disabled -> 400; bad mode -> 422.
- Plumbing tested with a deterministic FakeEmbedder (no torch). Real model verified via
  `OKF_REAL_EMBED=1 pytest tests/unit/test_embeddings_real.py`.
- Optional install: `pip install -e ".[semantic]"`.

### Phase C (auth + webhook) — done
- `app/security.py`: `require_api_key` on writes (POST/PUT/DELETE /concepts, POST /ingest).
  Auth disabled when `API_KEY` unset (local dev); else `X-API-Key` header, constant-time compare.
- `app/webhook.py`: `verify_signature` (HMAC-SHA256) + `RepoSyncer` (shallow clone + ingest).
- `POST /webhooks/github`: verify `X-Hub-Signature-256`, ack 202, background re-ingest. Bad/missing sig -> 401.

### Phase B (OKF validator) — done
- `app/bundle.py`: shared dir/zip reader (ingest + validate both use it).
- `app/rules.py`: `validate_bundle` — missing_type (error), duplicate_id (error), dangling_link (warning).
- `POST /validate` (path or zip), no persistence; returns report (valid flag + issues + concept_count).

## Phase A (core MVP) COMPLETE ✅ — drive-verified

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

### Next up — Phase F (deploy, free)
- Author **Alembic** migrations (baseline from current models incl. hnsw + generated tsvector column —
  autogenerate may need manual tweaks for the Computed tsvector + hnsw index ops).
- `Dockerfile` (COPY app/ so templates ship). Provision **Neon** project/branch via Neon MCP, enable
  `vector`, run migrations. **Render** free web service, env `DATABASE_URL`→Neon, `API_KEY`,
  `GITHUB_WEBHOOK_SECRET`, `EMBEDDINGS_ENABLED`. Point GitHub webhook at Render URL. Smoke test.
- NOTE: torch on Render free (512MB RAM) may be too heavy — consider EMBEDDINGS_ENABLED=false in cloud,
  or a smaller/remote embedding path. Keyword+validator+UI work fine without it.

### Commands
```
docker compose up -d
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload
```
