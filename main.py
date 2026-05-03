import fastapi
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api import routes
from app.api.rate_limit import limiter

app = fastapi.FastAPI(
    title="Transcript Analyzer API",
    version="1.0.0",
    root_path="/api",
    description="""
Analyzes plain-text coaching session transcripts using **OpenAI structured output**
and returns a concise **summary** of key discussion points plus a list of **action items**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/transcripts` | Analyze a single transcript |
| `POST` | `/transcripts/batch` | Analyze multiple transcripts concurrently |
| `GET` | `/transcripts/{id}` | Retrieve a stored analysis by ID |
""",
    contact={"name": "Enzo Faliveni", "email": "enzofali.ef@gmail.com"},
    openapi_tags=[
        {
            "name": "transcripts",
            "description": "Analyze coaching transcripts and retrieve stored results.",
        }
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
