"""
Postgres repository integration tests.
Require a live Postgres instance — run with:
    pytest tests/adapters/test_postgres_repository.py

Default pytest run (pyproject.toml) excludes this directory.
Set DATABASE_URL env var or use the default docker-compose URL.
"""
import os
import uuid
import pytest
import psycopg2

from app.models.transcript import TranscriptAnalysis
from app.repositories.postgres import PostgresAnalysisRepository

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://transcript:transcript@localhost:5432/transcript",
)


def _can_connect() -> bool:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_connect(),
    reason="Postgres not reachable — start docker compose or set DATABASE_URL",
)


@pytest.fixture()
def repo() -> PostgresAnalysisRepository:
    r = PostgresAnalysisRepository(DATABASE_URL)
    yield r
    # clean up all rows written during the test
    with r._conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM transcript_analysis")


def make_analysis() -> TranscriptAnalysis:
    return TranscriptAnalysis(
        id=uuid.uuid4(),
        summary="Test summary",
        action_items=["Action 1", "Action 2"],
    )


def test_save_and_get_by_id(repo: PostgresAnalysisRepository) -> None:
    analysis = make_analysis()
    repo.save(analysis)
    result = repo.get_by_id(analysis.id)
    assert result is not None
    assert result.id == analysis.id
    assert result.summary == analysis.summary
    assert result.action_items == analysis.action_items


def test_get_by_id_returns_none_when_not_found(repo: PostgresAnalysisRepository) -> None:
    assert repo.get_by_id(uuid.uuid4()) is None


def test_save_upsert_updates_existing(repo: PostgresAnalysisRepository) -> None:
    analysis = make_analysis()
    repo.save(analysis)
    updated = TranscriptAnalysis(
        id=analysis.id,
        summary="Updated summary",
        action_items=["New action"],
        created_at=analysis.created_at,
    )
    repo.save(updated)
    result = repo.get_by_id(analysis.id)
    assert result.summary == "Updated summary"
    assert result.action_items == ["New action"]


def test_list_all_returns_all_saved(repo: PostgresAnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repo.save(first)
    repo.save(second)
    results = repo.list_all()
    ids = {r.id for r in results}
    assert first.id in ids
    assert second.id in ids


def test_list_all_ordered_most_recent_first(repo: PostgresAnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repo.save(first)
    repo.save(second)
    results = repo.list_all()
    assert results[0].created_at >= results[1].created_at


def test_list_all_empty(repo: PostgresAnalysisRepository) -> None:
    assert repo.list_all() == []


def test_delete_existing_returns_true(repo: PostgresAnalysisRepository) -> None:
    analysis = make_analysis()
    repo.save(analysis)
    assert repo.delete(analysis.id) is True
    assert repo.get_by_id(analysis.id) is None


def test_delete_nonexistent_returns_false(repo: PostgresAnalysisRepository) -> None:
    assert repo.delete(uuid.uuid4()) is False


def test_delete_removes_only_target(repo: PostgresAnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    repo.save(first)
    repo.save(second)
    repo.delete(first.id)
    assert repo.get_by_id(first.id) is None
    assert repo.get_by_id(second.id) is not None


def test_delete_many_returns_count(repo: PostgresAnalysisRepository) -> None:
    first = make_analysis()
    second = make_analysis()
    third = make_analysis()
    repo.save(first)
    repo.save(second)
    repo.save(third)
    deleted = repo.delete_many([first.id, third.id])
    assert deleted == 2
    assert repo.get_by_id(first.id) is None
    assert repo.get_by_id(second.id) is not None
    assert repo.get_by_id(third.id) is None


def test_delete_many_skips_missing_ids(repo: PostgresAnalysisRepository) -> None:
    analysis = make_analysis()
    repo.save(analysis)
    deleted = repo.delete_many([analysis.id, uuid.uuid4()])
    assert deleted == 1


def test_delete_many_empty_list_returns_zero(repo: PostgresAnalysisRepository) -> None:
    assert repo.delete_many([]) == 0


def test_delete_many_all_missing_returns_zero(repo: PostgresAnalysisRepository) -> None:
    assert repo.delete_many([uuid.uuid4(), uuid.uuid4()]) == 0
