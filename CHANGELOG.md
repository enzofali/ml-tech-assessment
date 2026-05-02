# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.0] — 2026-05-02

### Added

**Postgres repository adapter**
- `PostgresAnalysisRepository` — full `AnalysisRepository` implementation backed by a `psycopg2` connection pool (min 1, max 10)
- `DATABASE_URL` env var selects the adapter at runtime; omitting it falls back to in-memory with no code changes
- Schema: `transcript_analysis(id UUID PK, summary TEXT, action_items JSONB, created_at TIMESTAMPTZ)` — auto-created on first boot
- `DELETE WHERE id = ANY(%s::uuid[])` for batch deletes — single round-trip regardless of list size

**Service decoupling**
- Frontend now runs as a dedicated container (multi-stage Next.js standalone Dockerfile)
- nginx reverse proxy on port 80 routes all traffic: `/api/` → FastAPI, `/grafana/` → Grafana, `/` → Next.js

**docker-compose**
- Added `postgres` service (Postgres 16 Alpine) with healthcheck; `api` waits for healthy signal before starting
- Added `frontend` service built with `NEXT_PUBLIC_API_URL=http://localhost/api` baked in
- Added `nginx` service mounting `nginx/nginx.conf`; only nginx exposes a host port (80)
- Grafana configured with `GF_SERVER_SERVE_FROM_SUB_PATH=true` for correct sub-path asset resolution
- Named volume `postgres_data` persists analyses across restarts; survives `docker compose down` (requires `-v` to wipe)

**Tests**
- Added 4 `delete_many` test cases to the shared repository fixture: partial delete, missing IDs, empty list, all missing
- Fixed `SQLiteInMemoryAnalysisRepository` — missing `delete_many` made it uninstantiable as an ABC; implemented using `DELETE WHERE id IN (?,…)` with dynamic placeholders
- Added 13 Postgres integration tests in `tests/adapters/test_postgres_repository.py`; auto-skip when DB is unreachable; excluded from default `pytest` run

### Changed

- `app/api/dependencies.py` — `get_repository()` now switches on `DATABASE_URL`; return type widened to `AnalysisRepository` port
- `app/configurations.py` — added optional `DATABASE_URL: str | None = None`
- `frontend/next.config.ts` — added `output: "standalone"` required for the standalone Docker build
- `docker-compose.yml` — postgres port `5432` exposed to host to allow integration tests to run against the live container
- README — updated Quick Start (single port, no Node prerequisite), URL table, env vars, Cloudflare tunnel (one tunnel not three), removed stale "Next Steps" migration items that are now shipped

---

## [0.0.1] — 2026-05-02

### Added

**Core API**
- `POST /transcripts` — analyze a single transcript via structured LLM output, persist result in memory, return `{id, summary, action_items, created_at}`
- `POST /transcripts/batch` — analyze up to 50 transcripts concurrently via `asyncio.gather` with a `Semaphore(5)` throttle
- `GET /transcripts` — list all stored analyses ordered by creation time, newest first
- `GET /transcripts/{id}` — retrieve a stored analysis by UUID; returns 404 when not found
- `DELETE /transcripts/{id}` — delete a single analysis; returns 204
- `DELETE /transcripts` — bulk delete by list of IDs; skips missing IDs silently, returns `{ deleted: N }`
- Input validation: 422 on empty, whitespace-only, or malformed VTT/SRT transcripts

**Multi-format transcript parsing**
- Auto-detection of format from content — no `format` field required
- Supported formats: plain text, `Speaker: text`, `Speaker | Role: text`, `[HH:MM:SS]` timestamps, WebVTT (Zoom / Teams / Meet exports), SRT
- Strict validation rejects structurally invalid VTT/SRT files with a 422 and a clear error message

**Text normalization**
- Strips timestamps, cue headers, and sequence numbers before sending to the LLM
- Conservative strategy preserves speaker labels and dialogue; aggressive strategy collapses whitespace further
- Reduces token usage on formatted transcripts by up to 40%

**Multi-provider LLM support**
- Interchangeable backends via the `LLm` port: Groq (default, free tier), OpenAI, Gemini
- Configured entirely via environment variables — no code changes needed to switch providers
- Per-provider cost table for accurate USD spend tracking

**Architecture**
- Hexagonal (ports & adapters): `LLm` and `AnalysisRepository` ports with runtime injection via FastAPI DI
- `TranscriptAnalysisDTO` decouples the LLM response shape from the domain entity
- In-memory repository with full CRUD; swappable for a Postgres implementation without touching the service layer

**Observability**
- Prometheus `/metrics` endpoint with 3 instrumentation layers: LLM metrics, repository metrics, HTTP + process metrics
- 21-panel Grafana dashboard (auto-provisioned) covering LLM performance, cost, latency, repository operations, and process health
- Metrics: `llm_requests_total`, `llm_tokens_total`, `llm_cost_usd_total`, `llm_errors_total`, `llm_request_duration_seconds`, `repository_operations_total`, `repository_size`, `batch_size`

**Frontend**
- Next.js 15 (App Router) with TypeScript and Tailwind CSS
- Analyze page: paste or drag-and-drop transcript files (`.txt`, `.vtt`, `.srt`), submit for analysis, see results inline
- History page: list of all analyses with summary preview, date, action item count, multi-select checkboxes, and bulk delete
- Detail page: full analysis view with single-item delete

**Local deployment**
- `docker compose up --build` starts the API, Prometheus, and Grafana in one command
- Grafana dashboard auto-loads on first boot — no manual setup
- Sample transcripts in `resources/` covering all supported formats and scenarios

**Tests**
- Unit tests: `TranscriptService`, in-memory repository, transcript parser, text normalizer
- E2E tests: full HTTP stack via `TestClient` with mocked LLM — covers all endpoints, validation paths, and multi-format inputs
- Adapter integration tests (require live API key, excluded from default run)
