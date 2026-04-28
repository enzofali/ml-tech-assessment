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


def test_list_all_returns_all_saved(repository: AnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repository.save(first)
    repository.save(second)
    results = repository.list_all()
    assert len(results) == 2
    assert {r.id for r in results} == {first.id, second.id}


def test_list_all_empty_returns_empty_list(repository: AnalysisRepository) -> None:
    assert repository.list_all() == []


def test_list_all_ordered_most_recent_first(repository: AnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repository.save(first)
    repository.save(second)
    results = repository.list_all()
    assert results[0].created_at >= results[1].created_at


def test_delete_existing_returns_true(repository: AnalysisRepository) -> None:
    analysis = make_analysis()
    repository.save(analysis)
    assert repository.delete(analysis.id) is True
    assert repository.get_by_id(analysis.id) is None


def test_delete_nonexistent_returns_false(repository: AnalysisRepository) -> None:
    assert repository.delete(uuid.uuid4()) is False


def test_delete_removes_only_target(repository: AnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repository.save(first)
    repository.save(second)
    repository.delete(first.id)
    assert repository.get_by_id(first.id) is None
    assert repository.get_by_id(second.id) == second
