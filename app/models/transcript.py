import uuid
import pydantic


class TranscriptAnalysisDTO(pydantic.BaseModel):
    """LLM-layer DTO — shape of the structured output returned by OpenAI."""
    summary: str
    action_items: list[str]


class TranscriptAnalysis(pydantic.BaseModel):
    """Domain entity stored in memory and returned by the API."""
    id: uuid.UUID
    summary: str
    action_items: list[str]
