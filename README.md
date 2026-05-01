# Transcript Analyzer API

A FastAPI service that analyzes coaching session transcripts using structured LLM output and returns a concise **summary** plus **action items**. Supports OpenAI, Gemini, and Groq as interchangeable backends.

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
| Grafana    | http://localhost:3000      |

Grafana default login: `admin` / `admin`.

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

- `http_request_duration_seconds` — latency histogram by method, path, status code
- `process_cpu_seconds_total`, `process_resident_memory_bytes`, `process_open_fds`

### Grafana dashboard

When running via Docker Compose, Grafana is pre-configured with Prometheus as the default data source.

1. Open http://localhost:3000 → log in with `admin` / `admin`
2. Go to **Explore** → select **Prometheus**
3. Start querying — useful starters:

```promql
# LLM p95 latency per provider/model
histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m]))

# Token rate per model
rate(llm_tokens_total[5m])

# Error breakdown
llm_errors_total

# Request latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Repository size over time
repository_size
```

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
