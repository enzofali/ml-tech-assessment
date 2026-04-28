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

    def list_all(self) -> list[TranscriptAnalysis]:
        return sorted(self._store.values(), key=lambda a: a.created_at, reverse=True)

    def delete(self, id: uuid.UUID) -> bool:
        if id not in self._store:
            return False
        del self._store[id]
        return True
