import uuid
from datetime import datetime, timezone
import pydantic


class TranscriptAnalysisDTO(pydantic.BaseModel):
    """LLM-layer DTO — shape of the structured output returned by OpenAI."""
    summary: str
    action_items: list[str]


class TranscriptAnalysis(pydantic.BaseModel):
    """Domain entity stored in memory and returned by the API."""
    id: uuid.UUID = pydantic.Field(description="Unique identifier for this analysis.")
    summary: str = pydantic.Field(description="Concise summary of the key discussion points.")
    action_items: list[str] = pydantic.Field(description="Ordered list of recommended next actions.")
    created_at: datetime = pydantic.Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the analysis was created.",
    )
