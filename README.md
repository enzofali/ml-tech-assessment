# Transcript Analyzer API

A FastAPI service that analyzes coaching session transcripts using **OpenAI structured output** and returns a concise **summary** plus a list of **action items**.

## Architecture

Hexagonal (ports & adapters) with clear layer separation:

```
app/
├── ports/          # Interfaces — LLm, AnalysisRepository
├── adapters/       # OpenAI adapter implementing the LLm port
├── repositories/   # In-memory repository implementing AnalysisRepository
├── models/         # Domain entity (TranscriptAnalysis) + LLM DTO
├── services/       # Business logic (TranscriptService)
└── api/            # FastAPI routes + dependency injection wiring
```

The service layer depends only on port interfaces. Adapters are injected at runtime via FastAPI's DI system, making every layer independently unit-testable.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/transcripts` | Analyze a single transcript |
| `POST` | `/transcripts/batch` | Analyze multiple transcripts concurrently |
| `GET` | `/transcripts/{id}` | Retrieve a stored analysis by ID |

Full interactive docs: **`/docs`** (Swagger UI) · **`/redoc`** (ReDoc)

## Transcript Format

No standard format is required. The API accepts free-form plain text and the LLM normalises all common conventions automatically:

| Format | Example |
|--------|---------|
| Simple label | `Alice: Let's discuss the roadmap.` |
| Role label (AceUp) | `Alice \| Coach: What are your blockers?` |
| Timestamped | `[00:05] Alice: Good morning.` |
| Raw meeting notes | `Team agreed to ship v2 by Friday.` |

## Setup

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/docs/#installation)
- An OpenAI API key

### Install dependencies

```bash
poetry install
```

### Environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-2024-08-06   # optional — this is the default
```

### Run the server

```bash
poetry run uvicorn main:app --reload
```

API available at `http://localhost:8000` · Swagger UI at `http://localhost:8000/docs`

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

> `tests/adapters/` requires a live OpenAI key and is excluded from the default run.

## Example Requests

### Single transcript

```bash
curl -X POST http://localhost:8000/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Alice | Coach: How have you been since our last session?\n\nBob: Much better. I finished the report.\n\nAlice | Coach: What helped?\n\nBob: Breaking it into daily tasks."
  }'
```

**Response (201)**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "summary": "Bob made strong progress on his project report by adopting a daily task structure.",
  "action_items": [
    "Continue the daily task habit for upcoming deliverables",
    "Share the completed report with stakeholders by end of week"
  ]
}
```

### Batch (concurrent)

```bash
curl -X POST http://localhost:8000/transcripts/batch \
  -H "Content-Type: application/json" \
  -d '{
    "transcripts": [
      "Alice | Coach: What is your goal this month?\nBob: Ship the new feature.",
      "[00:00] Sarah: We need to improve team communication.\n[00:30] Manager: Agreed. Weekly syncs?"
    ]
  }'
```

### Retrieve by ID

```bash
curl http://localhost:8000/transcripts/3fa85f64-5717-4562-b3fc-2c963f66afa6
```
