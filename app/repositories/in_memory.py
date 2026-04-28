import uuid
from app.models.transcript import TranscriptAnalysis
from app.ports.repository import AnalysisRepository


class InMemoryAnalysisRepository(AnalysisRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, TranscriptAnalysis] = {}

    def save(self, analysis: TranscriptAnalysis) -> None:
        self._store[analysis.id] = analysis

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        return self._store.get(id)
