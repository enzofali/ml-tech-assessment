# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-04-27

### Added

**Core API (Point 1)**
- `POST /transcripts` — analyze a single transcript via OpenAI structured output, persist result in memory, return `{id, summary, action_items}`
- `GET /transcripts/{id}` — retrieve a stored analysis by UUID; returns 404 when not found
- Input validation: 422 on empty or whitespace-only transcripts

**Batch endpoint (Point 2)**
- `POST /transcripts/batch` — accepts a list of transcripts and analyzes them concurrently via `asyncio.gather`
- `asyncio.Semaphore(5)` throttles concurrent OpenAI calls to avoid rate-limit errors

**Architecture**
- Hexagonal (ports & adapters): `LLm` and `AnalysisRepository` ports, OpenAI adapter, in-memory + SQLite repository implementations
- `TranscriptAnalysisDTO` decouples the LLM response shape from the domain entity

**OpenAI integration**
- `OpenAIAdapter.run_completion` — synchronous structured output via `beta.chat.completions.parse`
- `OpenAIAdapter.run_completion_async` — async variant using `AsyncOpenAI` client

**Documentation**
- Swagger UI at `/docs` with per-endpoint summaries, descriptions, and request/response examples
- ReDoc at `/redoc`
- Multi-format transcript guide in API description and README

**Tests**
- Unit tests: `TranscriptService` (sync, async single, batch, prompt formatting, repository delegation)
- Unit tests: in-memory and SQLite repository implementations
- E2E tests: full HTTP stack via `starlette.testclient.TestClient` with mocked LLM — covers all endpoints, validation paths, and multi-format transcripts
