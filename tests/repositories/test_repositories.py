import uuid
import pytest
from app.models.transcript import TranscriptAnalysis
from app.ports.repository import AnalysisRepository
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.repositories.sqlite_in_memory import SQLiteInMemoryAnalysisRepository


def make_analysis() -> TranscriptAnalysis:
    return TranscriptAnalysis(
        id=uuid.uuid4(),
        summary="Test summary",
        action_items=["Action 1", "Action 2"],
    )


@pytest.fixture(params=[InMemoryAnalysisRepository, SQLiteInMemoryAnalysisRepository])
def repository(request) -> AnalysisRepository:
    return request.param()


def test_save_and_get_by_id(repository: AnalysisRepository) -> None:
    analysis = make_analysis()
    repository.save(analysis)
    result = repository.get_by_id(analysis.id)
    assert result == analysis


def test_get_by_id_returns_none_when_not_found(repository: AnalysisRepository) -> None:
    result = repository.get_by_id(uuid.uuid4())
    assert result is None


def test_save_multiple_and_retrieve_correct_one(repository: AnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repository.save(first)
    repository.save(second)
    assert repository.get_by_id(first.id) == first
    assert repository.get_by_id(second.id) == second
