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
