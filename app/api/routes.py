import uuid
import pydantic
import fastapi

router = fastapi.APIRouter()


class AnalyzeRequest(pydantic.BaseModel):
    transcript: str


class AnalyzeResponse(pydantic.BaseModel):
    id: uuid.UUID
    summary: str
    action_items: list[str]


@router.post("/transcripts", response_model=AnalyzeResponse, status_code=201)
def analyze_transcript(request: AnalyzeRequest):
    if not request.transcript.strip():
        raise fastapi.HTTPException(status_code=422, detail="Transcript cannot be empty")
    # TODO: inject and call TranscriptService
    raise fastapi.HTTPException(status_code=501, detail="Not implemented")


@router.get("/transcripts/{id}", response_model=AnalyzeResponse)
def get_transcript(id: uuid.UUID):
    # TODO: inject and call TranscriptService
    raise fastapi.HTTPException(status_code=501, detail="Not implemented")
