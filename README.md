# Transcript Analyzer

A full-stack app that analyzes coaching session transcripts using structured LLM output and returns a concise **summary** plus **action items**. FastAPI backend · Next.js frontend · Prometheus + Grafana observability.

---

## Quick Start

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), [Node.js 18+](https://nodejs.org/), a free [Groq API key](https://console.groq.com/)

```bash
# 1. Clone
git clone <repo-url> && cd ml-tech-assessment

# 2. Create .env in the project root
cat > .env << 'EOF'
LLM_PROVIDER=groq
LLM_API_KEY=your-groq-key-here
LLM_MODEL=llama-3.3-70b-versatile
EOF

# 3. Start the backend + Prometheus + Grafana
docker compose up --build -d

# 4. Start the frontend
cd frontend && npm install && npm run dev
```

| Service | URL | Credentials |
|---|---|---|
| Frontend | http://localhost:3000 | — |
| API + Swagger | http://localhost:8000/docs | — |
| Grafana dashboard | http://localhost:3002 | `admin` / `admin` |

Open http://localhost:3000, drag in one of the sample transcripts from [`resources/`](resources/), and hit **Analyze**.

### Viewing the Grafana dashboard

1. Open http://localhost:3002
2. Log in with `admin` / `admin`
3. Click **Dashboards** in the left sidebar → select **Transcript API**

The dashboard has 21 panels across 8 rows covering LLM performance, cost, latency, repository operations, and process health. Panels populate as soon as you run a few analyses — generate some traffic first by submitting a couple of transcripts on the frontend.

> First load may take up to 15 seconds while Prometheus scrapes the initial metrics.

---

## Architecture

Hexagonal (ports & adapters) with clear layer separation:

```
app/
├── ports/          # Interfaces — LLm, AnalysisRepository
├── adapters/       # OpenAI · Gemini · Groq adapters implementing the LLm port
├── repositories/   # In-memory repository implementing AnalysisRepository
├── models/         # Domain entity (TranscriptAnalysis) + LLM DTO
├── services/       # Business logic (TranscriptService)
└── api/            # FastAPI routes + dependency injection wiring
```

The service layer depends only on port interfaces. Adapters are injected at runtime via FastAPI's DI system, making every layer independently unit-testable.

---

## Setup

### Docker Compose

Runs the API, Prometheus, and Grafana in one command. No Python install required.

```bash
docker compose up --build
```

| Service    | URL                        |
|------------|----------------------------|
| API        | http://localhost:8000      |
| Swagger UI | http://localhost:8000/docs |
| Prometheus | http://localhost:9090      |
| Grafana    | http://localhost:3002      |

Grafana default login: `admin` / `admin`.

**Frontend** (run separately — see [Frontend](#frontend) section below):

```bash
cd frontend && npm install && npm run dev
```

| Service  | URL                   |
|----------|-----------------------|
| Frontend | http://localhost:3000 |

### Environment variables

Create a `.env` file in the project root:

```env
# Provider: openai | gemini | groq  (default: groq)
LLM_PROVIDER=groq
LLM_API_KEY=your-api-key-here
LLM_MODEL=llama-3.3-70b-versatile   # optional — this is the groq default
```

**Model defaults per provider:**

| Provider | Default model              | Free tier |
|----------|---------------------------|-----------|
| `groq`   | `llama-3.3-70b-versatile` | Yes       |
| `gemini` | `gemini-2.5-flash`        | No       |
| `openai` | _(must set explicitly)_   | No        |

---

## API Reference

Full interactive docs: **`/docs`** (Swagger UI) · **`/redoc`** (ReDoc)

### Endpoints

| Method   | Path                   | Status | Description                              |
|----------|------------------------|--------|------------------------------------------|
| `GET`    | `/health`              | 200    | Liveness check                           |
| `POST`   | `/transcripts`         | 201    | Analyze a single transcript              |
| `POST`   | `/transcripts/batch`   | 201    | Analyze multiple transcripts concurrently|
| `GET`    | `/transcripts`         | 200    | List all stored analyses (newest first)  |
| `GET`    | `/transcripts/{id}`    | 200    | Retrieve a stored analysis by ID         |
| `DELETE` | `/transcripts/{id}`    | 204    | Delete a stored analysis                 |
| `DELETE` | `/transcripts`         | 200    | Bulk delete by list of IDs               |

### Transcript formats

No `format` field needed — the API auto-detects from content:

| Format       | Example                                              |
|--------------|------------------------------------------------------|
| Plain text   | `Alice: Let's discuss the roadmap.`                  |
| Role label   | `Alice \| Coach: What are your blockers?`            |
| Timestamped  | `[00:05] Alice: Good morning.`                       |
| WebVTT       | `WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nAlice: Hi` |
| SRT          | `1\n00:00:01,000 --> 00:00:04,000\nAlice: Hi`        |
| Raw notes    | `Team agreed to ship v2 by Friday.`                  |

### Example requests

**Single transcript**

```bash
curl -X POST http://localhost:8000/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Alice | Coach: How have you been since our last session?\n\nBob: Much better. I finished the report.\n\nAlice | Coach: What helped?\n\nBob: Breaking it into daily tasks."
  }'
```

Response `201`:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "summary": "Bob made strong progress on his project report by adopting a daily task structure.",
  "action_items": [
    "Continue the daily task habit for upcoming deliverables",
    "Share the completed report with stakeholders by end of week"
  ],
  "created_at": "2026-04-30T20:00:00Z"
}
```

**Batch (concurrent, up to 50 transcripts)**

```bash
curl -X POST http://localhost:8000/transcripts/batch \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Alice | Coach: What is your goal this month?\nBob: Ship the new feature.",
      "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nSarah: We need to improve team communication."
    ]
  }'
```

**Retrieve by ID**

```bash
curl http://localhost:8000/transcripts/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Delete by ID**

```bash
curl -X DELETE http://localhost:8000/transcripts/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

## Observability

The API exposes a `/metrics` endpoint in Prometheus format. Three layers of instrumentation are active out of the box.

### LLM metrics

| Metric                            | Type      | Labels                              | Description                              |
|-----------------------------------|-----------|-------------------------------------|------------------------------------------|
| `llm_requests_total`              | Counter   | `provider`, `model`, `status`       | Total completions (`success` / `error`)  |
| `llm_tokens_total`                | Counter   | `provider`, `model`, `token_type`   | Tokens consumed (`prompt` / `completion`)|
| `llm_cost_usd_total`              | Counter   | `provider`, `model`                 | Estimated cost (USD) from static table   |
| `llm_errors_total`                | Counter   | `provider`, `model`, `error_type`   | Errors by type (see below)               |
| `llm_request_duration_seconds`    | Histogram | `provider`, `model`                 | Completion latency (buckets: 0.5s–60s)  |

`error_type` values: `rate_limit` · `authentication` · `timeout` · `connection` · `bad_request` · `validation` · `unknown`

### Repository metrics

| Metric                        | Type    | Labels               | Description                              |
|-------------------------------|---------|----------------------|------------------------------------------|
| `repository_operations_total` | Counter | `operation`, `result`| Operations: `save/get/list/delete` × `success/miss/error` |
| `repository_size`             | Gauge   | —                    | Number of analyses currently in memory   |
| `batch_size`                  | Histogram | —                  | Transcripts per batch request (buckets: 1–50) |

### HTTP + process metrics

Provided automatically by `prometheus-fastapi-instrumentator` and the default Prometheus process collector:

| Metric                              | Type      | Description                              |
|-------------------------------------|-----------|------------------------------------------|
| `http_request_duration_seconds`     | Histogram | Latency by `method`, `handler`, `status` |
| `http_request_duration_seconds_count` | Counter | Request count (used for rate / error %)  |
| `process_cpu_seconds_total`         | Counter   | Cumulative CPU time                      |
| `process_resident_memory_bytes`     | Gauge     | Resident memory (RSS)                    |
| `process_virtual_memory_bytes`      | Gauge     | Virtual memory                           |
| `process_open_fds` / `process_max_fds` | Gauge  | Open / max file descriptors              |
| `process_start_time_seconds`        | Gauge     | Unix start time (used for uptime)        |

### Grafana dashboard

When running via Docker Compose, Grafana auto-loads a pre-built dashboard called **Transcript API** with 21 panels covering every layer of the system. No manual setup — just open http://localhost:3002 (login `admin` / `admin`) → **Dashboards** → **Transcript API**.

#### Dashboard layout

| Row | Panels | What you read here |
|-----|--------|--------------------|
| **1 — Health stats** | Successful Requests · Total Cost · Stored Analyses · LLM Errors · Uptime | Single-glance health. Errors panel turns red the moment any LLM call fails. Uptime catches crash loops and unexpected restarts. |
| **2 — LLM performance** | Request Rate (by status) · Latency p50/p95/p99 | Are calls succeeding? Are they fast? Diverging p50 vs p99 = long-tail stalls (usually the LLM provider). |
| **3 — Cost & errors** | Token Consumption Rate · Errors by Type | Why is cost going up — more prompts, longer outputs, or model change? Error breakdown by `rate_limit / authentication / timeout / …` tells you who to call. |
| **4 — HTTP latency** | Request Latency p95 by endpoint (full width) | End-to-end API latency including LLM time. Compare `/transcripts` vs `/transcripts/batch`. |
| **5 — Business metrics** | Cost ($/hr) · Batch Size Distribution · Repository Operations | Spend acceleration in real time. Batch p95 vs avg shows whether occasional huge batches are skewing load. Repo ops catches `get — miss` spikes (404s). |
| **6 — Process resources** | CPU · Memory (RSS + Virtual) · File Descriptors | Container-level health. FDs trending toward `max` = leak. |
| **7 — HTTP traffic** | Request Rate by endpoint · 4xx / 5xx Error Rate | Traffic patterns and HTTP-level failures. |
| **8 — SLI / efficiency** | Cost per Analysis · Tokens per Request · Error Rate (%) | The numbers you actually alert on. Error rate as a ratio (not absolute count) is the proper SLI. |

#### Custom queries

Need something not on the dashboard? Use **Explore** → select **Prometheus**:

```promql
# LLM p95 latency per provider/model
histogram_quantile(0.95, sum by (le, provider, model) (rate(llm_request_duration_seconds_bucket[5m])))

# Cost per hour at current rate
rate(llm_cost_usd_total[5m]) * 3600

# Repository miss rate (404s)
rate(repository_operations_total{result="miss"}[5m])

# Average tokens per request
rate(llm_tokens_total[5m]) / rate(llm_requests_total{status="success"}[5m])
```

#### Tuning the dashboard

The dashboard JSON lives at [grafana/dashboards/transcript-api.json](grafana/dashboards/transcript-api.json) and reloads every 30s. Edit it on disk or click **Edit** in Grafana then **Save JSON to file** — the file is the source of truth.

---

## Deployment

### Cloudflare Tunnel

**1. Install cloudflared**

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
```

**2. Start the stack**

```bash
docker compose up -d
```

**3. Open a tunnel for each service** (separate terminals)

```bash
cloudflared tunnel --url http://localhost:8000   # API + Swagger
cloudflared tunnel --url http://localhost:3000   # Frontend
cloudflared tunnel --url http://localhost:3002   # Grafana dashboard
```

Each command prints a public `https://*.trycloudflare.com` URL. Share both with the reviewer:

| Service | URL |
|---------|-----|
| API + Swagger | `https://xxxx.trycloudflare.com/docs` |
| Frontend | `https://zzzz.trycloudflare.com` |
| Grafana | `https://yyyy.trycloudflare.com` (login: `admin` / `admin`) |

> The tunnel stays alive as long as the terminal is open. Your machine is the server.

---

## Running Tests

```bash
# All tests (unit + E2E)
poetry run pytest

# Verbose output
poetry run pytest -v

# Only E2E (full HTTP stack, mocked LLM)
poetry run pytest tests/api/

# Only unit tests
poetry run pytest tests/services/ tests/repositories/
```

> `tests/adapters/` requires a live API key and is excluded from the default run.

---

## Frontend

The frontend was **vibe-coded** — rapidly scaffolded to make the product interactive and easy to demo, rather than built as production-grade UI. The goal was a clean interface that lets a reviewer explore every API capability without touching `curl`.

### Stack

- **Next.js 15** (App Router) with **TypeScript** and **Tailwind CSS**
- **lucide-react** for icons — no other UI library

### Architecture

The app follows the Next.js App Router model, mixing Server and Client Components based on responsibility:

```
frontend/
├── app/
│   ├── page.tsx                  # Analyze page — Client Component (form, state, drag & drop)
│   ├── history/page.tsx          # History page — Client Component (multi-select, bulk delete)
│   └── transcripts/[id]/page.tsx # Detail page  — Server Component (fetch + render analysis)
├── components/
│   └── DeleteButton.tsx          # Client Component (confirm dialog, DELETE call, redirect)
└── lib/
    └── api.ts                    # Typed API client (all 4 operations, driven by NEXT_PUBLIC_API_URL)
```

Server Components fetch directly on the server — no loading spinners, no client-side state. Client Components are used where the browser needs interactivity: the analyze form, the history page (multi-select + bulk delete), and the delete button.

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Analyze | `/` | Paste or drag-and-drop a transcript file (`.txt`, `.vtt`, `.srt`), submit for analysis, see results inline |
| History | `/history` | List of all stored analyses with summary preview, date, and action item count |
| Detail | `/transcripts/:id` | Full analysis view with delete button |

### Configuration

The only config needed is the API URL:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Sample files

The `resources/` directory contains four mock transcripts in every supported format, ready to drag onto the analyze page:

| File | Format | Scenario |
|------|--------|----------|
| `career_coaching_plain.txt` | Plain `Speaker: text` | Promotion conversation |
| `product_team_standup.srt` | SRT | Sprint retro |
| `leadership_coaching.vtt` | WebVTT | Manager overwhelm + delegation |
| `onboarding_coaching.txt` | Timestamped `[HH:MM:SS]` | New hire first month |

---

## Next Steps

The current deployment is a **monolith** — API, Prometheus, and Grafana run together via Docker Compose on a single host. This is intentional as a starting point. The natural evolution is to decouple into a production-grade architecture:

### Target architecture

```
Internet
    │
    ▼
Nginx Ingress (LoadBalancer)
    ├── /api          → API Deployment (N replicas)
    ├── /             → Frontend Deployment
    └── grafana.x.com → Grafana (via kube-prometheus-stack)

K8s Cluster
    ├── api-deployment         FastAPI × N replicas
    ├── frontend-deployment    React / Next.js
    ├── postgres StatefulSet   PersistentVolumeClaim (decoupled store)
    ├── prometheus             Scrapes API + K8s node metrics
    └── grafana                Pre-loaded dashboard, viewer access for reviewers
```

### Migration path

1. **Persistent store** — swap `InMemoryAnalysisRepository` for a `PostgresAnalysisRepository` (the port interface stays unchanged). Add a Postgres `StatefulSet` + `PersistentVolumeClaim` to the cluster.

2. **Frontend** — build a dedicated UI (separate deployment), served independently behind the same Ingress.

3. **Kubernetes manifests** — write `Deployment`, `Service`, `Ingress`, and `PVC` manifests (or use Helm). Recommended cluster: GKE Autopilot (free tier) or DigitalOcean DOKS (~$12/mo).

4. **Monitoring** — install [`kube-prometheus-stack`](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack) via Helm. This auto-wires Prometheus + Grafana + AlertManager and adds K8s node/pod metrics on top of the existing app metrics. Expose Grafana via Ingress at `grafana.your-domain.com`.
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install monitoring prometheus-community/kube-prometheus-stack \
     --namespace monitoring --create-namespace
   ```
   Alternatively, use **Grafana Cloud** (free tier, 10k series) with `remote_write` from in-cluster Prometheus — user gets a public URL with a read-only Viewer account.

