import openai
import pydantic
from prometheus_client import Counter, Gauge, Histogram

# USD per 1M tokens: {model: {input, output}}
# Groq dev-tier models are free; set to 0.0 so cost counter stays at 0 rather than raising.
_PRICE_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
}

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens consumed",
    ["provider", "model", "token_type"],  # token_type: prompt | completion
)

llm_cost_usd_total = Counter(
    "llm_cost_usd_total",
    "Estimated LLM cost in USD",
    ["provider", "model"],
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM completion requests",
    ["provider", "model", "status"],  # status: success | error
)

llm_errors_total = Counter(
    "llm_errors_total",
    "LLM completion errors by type",
    ["provider", "model", "error_type"],
)

repository_operations_total = Counter(
    "repository_operations_total",
    "Total repository operations",
    ["operation", "result"],  # operation: save|get|list|delete  result: success|miss|error
)

repository_size = Gauge(
    "repository_size",
    "Number of analyses currently stored in the repository",
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM completion latency in seconds",
    ["provider", "model"],
    buckets=[0.5, 1, 2, 5, 10, 20, 30, 60],
)

batch_size = Histogram(
    "batch_size",
    "Number of transcripts per batch request",
    buckets=[1, 2, 5, 10, 20, 50],
)


def record_llm_error(provider: str, model: str, exc: Exception) -> None:
    if isinstance(exc, openai.RateLimitError):
        error_type = "rate_limit"
    elif isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
        error_type = "authentication"
    elif isinstance(exc, openai.APITimeoutError):
        error_type = "timeout"
    elif isinstance(exc, openai.APIConnectionError):
        error_type = "connection"
    elif isinstance(exc, openai.BadRequestError):
        error_type = "bad_request"
    elif isinstance(exc, pydantic.ValidationError):
        error_type = "validation"
    else:
        error_type = "unknown"
    llm_requests_total.labels(provider=provider, model=model, status="error").inc()
    llm_errors_total.labels(provider=provider, model=model, error_type=error_type).inc()


def record_llm_usage(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    prices = _PRICE_PER_1M_TOKENS.get(model, {"input": 0.0, "output": 0.0})
    cost = (prompt_tokens * prices["input"] + completion_tokens * prices["output"]) / 1_000_000

    llm_tokens_total.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
    llm_tokens_total.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)
    llm_cost_usd_total.labels(provider=provider, model=model).inc(cost)
