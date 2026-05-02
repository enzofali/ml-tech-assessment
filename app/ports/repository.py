import uuid
from abc import ABC, abstractmethod
from app.models.transcript import TranscriptAnalysis


class AnalysisRepository(ABC):
    @abstractmethod
    def save(self, analysis: TranscriptAnalysis) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        pass

    @abstractmethod
    def list_all(self) -> list[TranscriptAnalysis]:
        pass

    @abstractmethod
    def delete(self, id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    def delete_many(self, ids: list[uuid.UUID]) -> int:
        """Delete multiple analyses. Returns the count of successfully deleted items."""
        pass
