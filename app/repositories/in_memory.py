import uuid
from app.models.transcript import TranscriptAnalysis
from app.ports.repository import AnalysisRepository
from app.metrics import repository_operations_total, repository_size


class InMemoryAnalysisRepository(AnalysisRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, TranscriptAnalysis] = {}

    def save(self, analysis: TranscriptAnalysis) -> None:
        try:
            self._store[analysis.id] = analysis
            repository_operations_total.labels(operation="save", result="success").inc()
            repository_size.set(len(self._store))
        except Exception:
            repository_operations_total.labels(operation="save", result="error").inc()
            raise

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        try:
            result = self._store.get(id)
            repository_operations_total.labels(operation="get", result="success" if result else "miss").inc()
            return result
        except Exception:
            repository_operations_total.labels(operation="get", result="error").inc()
            raise

    def list_all(self) -> list[TranscriptAnalysis]:
        try:
            repository_operations_total.labels(operation="list", result="success").inc()
            return sorted(self._store.values(), key=lambda a: a.created_at, reverse=True)
        except Exception:
            repository_operations_total.labels(operation="list", result="error").inc()
            raise

    def delete(self, id: uuid.UUID) -> bool:
        try:
            if id not in self._store:
                repository_operations_total.labels(operation="delete", result="miss").inc()
                return False
            del self._store[id]
            repository_operations_total.labels(operation="delete", result="success").inc()
            repository_size.set(len(self._store))
            return True
        except Exception:
            repository_operations_total.labels(operation="delete", result="error").inc()
            raise

    def delete_many(self, ids: list[uuid.UUID]) -> int:
        # No concurrency needed: dict ops are nanosecond CPU work with no I/O to await.
        # On a real DB, replace with a single DELETE WHERE id = ANY($1) — one round-trip beats N concurrent ones.
        try:
            ids_set = set(ids)
            to_delete = ids_set & self._store.keys()
            missed = len(ids_set) - len(to_delete)
            for id in to_delete:
                del self._store[id]
            if to_delete:
                repository_operations_total.labels(operation="delete", result="success").inc(len(to_delete))
                repository_size.set(len(self._store))
            if missed:
                repository_operations_total.labels(operation="delete", result="miss").inc(missed)
            return len(to_delete)
        except Exception:
            repository_operations_total.labels(operation="delete", result="error").inc()
            raise
