import uuid
from datetime import datetime
from typing import Annotated
import pydantic
import fastapi
from app.api.dependencies import get_service
from app.services.transcript import TranscriptService

router = fastapi.APIRouter(tags=["transcripts"])

ServiceDep = Annotated[TranscriptService, fastapi.Depends(get_service)]


class AnalyzeRequest(pydantic.BaseModel):
    transcript: str = pydantic.Field(
        description="Plain-text transcript in any conversational format (speaker labels, timestamps, raw notes).",
        min_length=1,
        max_length=50_000,
    )

    @pydantic.field_validator("transcript")
    @classmethod
    def transcript_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("transcript must not be blank or whitespace-only")
        return v

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transcript": (
                        "Alice | Coach: How have you been since our last session?\n\n"
                        "Bob: Much better. I finished the project report.\n\n"
                        "Alice | Coach: What helped you push through?\n\n"
                        "Bob: Breaking it into daily tasks."
                    )
                }
            ]
        }
    )


class AnalyzeResponse(pydantic.BaseModel):
    id: uuid.UUID = pydantic.Field(description="Unique identifier for this analysis.")
    summary: str = pydantic.Field(description="Concise summary of the key discussion points.")
    action_items: list[str] = pydantic.Field(description="Ordered list of recommended next actions.")
    created_at: datetime = pydantic.Field(description="UTC timestamp when the analysis was created.")


class BatchAnalyzeRequest(pydantic.BaseModel):
    transcripts: list[Annotated[str, pydantic.Field(min_length=1, max_length=50_000)]] = pydantic.Field(
        description="List of plain-text transcripts to analyze concurrently. Each item must be non-empty.",
        min_length=1,
        max_length=50,
    )

    @pydantic.field_validator("transcripts")
    @classmethod
    def transcripts_not_blank(cls, v: list[str]) -> list[str]:
        if any(not t.strip() for t in v):
            raise ValueError("each transcript must be non-empty and not whitespace-only")
        return v

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transcripts": [
                        "Alice | Coach: What is your main goal this month?\n\nBob: Ship the new feature.",
                        "[00:00] Sarah: We need to improve team communication.\n[00:30] Manager: Agreed. Weekly syncs?",
                    ]
                }
            ]
        }
    )


@router.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Returns `ok` when the service is running. Used by deployment platforms to verify liveness.",
)
def health_check():
    return {"status": "ok"}


@router.get(
    "/transcripts",
    response_model=list[AnalyzeResponse],
    summary="List all analyses",
    description="Returns all stored transcript analyses ordered by creation time, most recent first.",
)
def list_transcripts(service: ServiceDep):
    return service.list_all()


@router.post(
    "/transcripts/batch",
    response_model=list[AnalyzeResponse],
    status_code=201,
    summary="Batch analyze transcripts",
    description=(
        "Accepts a list of transcripts and analyzes them **concurrently** using asyncio. "
        "All analyses run in parallel (up to 5 simultaneous OpenAI calls via a semaphore) "
        "and results are returned in the same order as the input list."
    ),
    responses={
        201: {"description": "All transcripts analyzed successfully."},
        422: {"description": "Empty list or any transcript is blank."},
    },
)
async def analyze_transcripts_batch(request: BatchAnalyzeRequest, service: ServiceDep):
    analyses = await service.analyze_batch(request.transcripts)
    return analyses


@router.post(
    "/transcripts",
    response_model=AnalyzeResponse,
    status_code=201,
    summary="Analyze a single transcript",
    description=(
        "Sends the transcript to OpenAI with a business-coaching system prompt "
        "and returns a structured analysis containing a **summary** and **action items**. "
        "The result is persisted in memory and retrievable by the returned `id`."
    ),
    responses={
        201: {"description": "Transcript analyzed and stored successfully."},
        422: {"description": "Transcript is empty or whitespace-only."},
    },
)
def analyze_transcript(request: AnalyzeRequest, service: ServiceDep):
    return service.analyze(request.transcript)


@router.get(
    "/transcripts/{id}",
    response_model=AnalyzeResponse,
    summary="Get analysis by ID",
    description="Retrieves a previously stored transcript analysis by its unique identifier.",
    responses={
        200: {"description": "Analysis found and returned."},
        404: {"description": "No analysis found for the given ID."},
    },
)
def get_transcript(id: uuid.UUID, service: ServiceDep):
    analysis = service.get_by_id(id)
    if analysis is None:
        raise fastapi.HTTPException(status_code=404, detail="Transcript not found")
    return analysis


@router.delete(
    "/transcripts/{id}",
    status_code=204,
    summary="Delete analysis by ID",
    description="Permanently removes a stored transcript analysis. Returns 204 on success, 404 if not found.",
    responses={
        204: {"description": "Analysis deleted successfully."},
        404: {"description": "No analysis found for the given ID."},
    },
)
def delete_transcript(id: uuid.UUID, service: ServiceDep):
    if not service.delete(id):
        raise fastapi.HTTPException(status_code=404, detail="Transcript not found")
