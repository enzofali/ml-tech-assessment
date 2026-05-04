# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.2.0] — 2026-05-04

### Added

**Kubernetes deployment**
- Added plain Kubernetes manifests for namespace, API, frontend, Postgres, Prometheus, Grafana, ingress, secrets, PVCs, services, and API HPA
- Added Docker Desktop / minikube-friendly ingress setup with `/api`, `/`, and `/grafana` routes
- Added `k8s/secrets.example.yaml` so real LLM and database credentials stay out of source control

**Operations**
- Added a `Makefile` for local image builds, Docker Compose lifecycle, Kubernetes deploy/teardown/status, ingress forwarding, and minikube helpers
- Added Grafana dashboard ConfigMap generation from the checked-in dashboard JSON
- Added Kubernetes status and port-forward commands for local reviewer verification

### Fixed

- Adjusted Kubernetes manifests so the Docker Desktop deployment can run end-to-end locally
- Preserved Grafana sub-path routing under `/grafana`

## [0.1.0] — 2026-05-03

### Added

**Decoupled services**
- Added a Postgres repository adapter behind the existing `AnalysisRepository` port
- Added `DATABASE_URL` configuration; the API falls back to in-memory storage when unset
- Added a dedicated frontend container so the Next.js UI can run independently from the API
- Added nginx routing for frontend, API, and Grafana behind a single local entry point

**Persistence**
- Added Postgres service and persistent volume to Docker Compose
- Added repository coverage for the Postgres-backed implementation

### Changed

- Updated Docker Compose from the `0.0.1` monolith-oriented setup to a decoupled stack with Postgres, API, frontend, nginx, Prometheus, and Grafana
- Updated frontend configuration to consume the API through the routed public URL

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
