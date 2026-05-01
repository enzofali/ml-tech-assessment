# Integration Test Results

Tested manually against a live server (Groq provider, `llama-3.3-70b-versatile`) on 2026-04-30.

## Happy path

| Endpoint | Scenario | HTTP |
|---|---|---|
| GET /health | Liveness check | 200 |
| GET /transcripts | Empty store returns `[]` | 200 |
| POST /transcripts | Plain text → summary + action_items | 201 |
| POST /transcripts | WebVTT (timestamps stripped by parser) | 201 |
| POST /transcripts | SRT (sequence numbers + timestamps stripped) | 201 |
| GET /transcripts | Lists 3 stored analyses, newest first | 200 |
| GET /transcripts/{id} | Fetch by valid UUID | 200 |
| DELETE /transcripts/{id} | Delete existing → no body | 204 |
| GET /transcripts/{id} | Previously deleted ID | 404 |
| DELETE /transcripts/{id} | Non-existent ID | 404 |
| POST /transcripts/batch | 3 mixed formats (plain/VTT/SRT) concurrently | 201 |

## Validation guards

| Scenario | HTTP | Error type |
|---|---|---|
| Empty string `""` | 422 | `string_too_short` |
| Whitespace-only `"   "` | 422 | `value_error` (custom validator) |
| Missing `transcript` field | 422 | `missing` |
| Batch empty list `[]` | 422 | `too_short` |
| Batch with blank item in list | 422 | `value_error` (custom validator) |
| Malformed UUID in path | 422 | `uuid_parsing` |

## LLM error handling

| Scenario | HTTP | `detail` |
|---|---|---|
| Bad API key (`AuthenticationError`) | 500 | `LLM authentication failed — check your API key configuration` |

LLM errors are caught in each adapter as `openai.OpenAIError` or `pydantic.ValidationError` and re-raised as `LLMError` (defined in `app/ports/llm.py`). Routes return `HTTPException(status_code=e.status_code, detail=str(e))`.

Expected status codes per error type:

| Error | HTTP |
|---|---|
| `RateLimitError` | 429 |
| `AuthenticationError` / `PermissionDeniedError` | 500 |
| `APIConnectionError` / `APITimeoutError` | 502 |
| `BadRequestError` / `ValidationError` / other | 502 |
