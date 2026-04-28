import uuid
from typing import Annotated
import pydantic
import fastapi
from app.api.dependencies import get_service
from app.services.transcript import TranscriptService

router = fastapi.APIRouter()

type ServiceDep = Annotated[TranscriptService, fastapi.Depends(get_service)]


class AnalyzeRequest(pydantic.BaseModel):
    transcript: str


class AnalyzeResponse(pydantic.BaseModel):
    id: uuid.UUID
    summary: str
    action_items: list[str]


class BatchAnalyzeRequest(pydantic.BaseModel):
    transcripts: list[str]


@router.post("/transcripts/batch", response_model=list[AnalyzeResponse], status_code=201)
async def analyze_transcripts_batch(request: BatchAnalyzeRequest, service: ServiceDep):
    if not request.transcripts:
        raise fastapi.HTTPException(status_code=422, detail="Transcripts list cannot be empty")
    if any(not t.strip() for t in request.transcripts):
        raise fastapi.HTTPException(status_code=422, detail="Each transcript must be non-empty")
    analyses = await service.analyze_batch(request.transcripts)
    return [AnalyzeResponse(id=a.id, summary=a.summary, action_items=a.action_items) for a in analyses]


@router.post("/transcripts", response_model=AnalyzeResponse, status_code=201)
def analyze_transcript(request: AnalyzeRequest, service: ServiceDep):
    if not request.transcript.strip():
        raise fastapi.HTTPException(status_code=422, detail="Transcript cannot be empty")
    analysis = service.analyze(request.transcript)
    return AnalyzeResponse(id=analysis.id, summary=analysis.summary, action_items=analysis.action_items)


@router.get("/transcripts/{id}", response_model=AnalyzeResponse)
def get_transcript(id: uuid.UUID, service: ServiceDep):
    analysis = service.get_by_id(id)
    if analysis is None:
        raise fastapi.HTTPException(status_code=404, detail="Transcript not found")
    return AnalyzeResponse(id=analysis.id, summary=analysis.summary, action_items=analysis.action_items)
