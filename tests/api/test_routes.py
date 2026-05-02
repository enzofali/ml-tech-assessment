"""
End-to-end tests for the HTTP API layer.

The LLM is mocked so no real OpenAI calls are made; everything else — routing,
validation, service logic, and in-memory repository — runs for real.
"""
import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest
from starlette.testclient import TestClient

from main import app
from app.api.dependencies import get_service
from app.models.transcript import TranscriptAnalysis, TranscriptAnalysisDTO
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.transcript import TranscriptService

from tests.adapters.mock_data import TRANSCRIPT as COACHING_TRANSCRIPT

TIMESTAMPED_TRANSCRIPT = (
    "[00:00] Interviewer: Tell me about your biggest challenge this quarter.\n"
    "[00:15] Sarah: We struggled with cross-team communication.\n"
    "[00:45] Interviewer: What specific steps are you taking to improve it?\n"
    "[01:10] Sarah: Weekly syncs and a shared Slack channel for updates."
)

_SUMMARY = (
    "Liam and his coach Mark discussed strategies for improving Python best practices "
    "across his growing engineering team, focusing on PEP 8 enforcement, Google-style "
    "docstrings, and increasing test coverage to 80%."
)
_ACTIONS = [
    "Adopt Black for automated PEP 8 formatting across the codebase",
    "Enforce Google-style docstrings for all modules, classes, and key functions",
    "Target 80% test coverage and pilot TDD on major features",
    "Run weekly peer code-review sessions to maintain standards",
    "Pilot the changes on one module first before rolling out team-wide",
]


def _make_mock_service(summary: str = _SUMMARY, action_items: list[str] = _ACTIONS) -> TranscriptService:
    llm = MagicMock()
    dto = TranscriptAnalysisDTO(summary=summary, action_items=action_items)
    llm.run_completion.return_value = dto
    llm.run_completion_async = AsyncMock(return_value=dto)
    return TranscriptService(llm=llm, repository=InMemoryAnalysisRepository())


@pytest.fixture
def client():
    service = _make_mock_service()
    app.dependency_overrides[get_service] = lambda: service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /transcripts — single analysis
# ---------------------------------------------------------------------------

def test_analyze_returns_201_with_structured_body(client):
    response = client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["summary"] == _SUMMARY
    assert body["action_items"] == _ACTIONS
    assert "created_at" in body


def test_analyze_with_timestamped_transcript(client):
    response = client.post("/transcripts", json={"transcript": TIMESTAMPED_TRANSCRIPT})
    assert response.status_code == 201
    assert uuid.UUID(response.json()["id"])


def test_analyze_empty_transcript_returns_422(client):
    response = client.post("/transcripts", json={"transcript": "   "})
    assert response.status_code == 422


def test_analyze_missing_field_returns_422(client):
    response = client.post("/transcripts", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /transcripts — list all
# ---------------------------------------------------------------------------

def test_list_transcripts_empty(client):
    response = client.get("/transcripts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_transcripts_returns_all(client):
    client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})
    client.post("/transcripts", json={"transcript": TIMESTAMPED_TRANSCRIPT})

    response = client.get("/transcripts")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_transcripts_ordered_most_recent_first(client):
    client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})
    client.post("/transcripts", json={"transcript": TIMESTAMPED_TRANSCRIPT})

    results = client.get("/transcripts").json()
    assert results[0]["created_at"] >= results[1]["created_at"]


# ---------------------------------------------------------------------------
# GET /transcripts/{id} — retrieval
# ---------------------------------------------------------------------------

def test_get_by_id_returns_stored_analysis(client):
    create_resp = client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})
    analysis_id = create_resp.json()["id"]

    get_resp = client.get(f"/transcripts/{analysis_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["id"] == analysis_id
    assert body["summary"] == _SUMMARY


def test_get_by_id_not_found_returns_404(client):
    response = client.get(f"/transcripts/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transcript not found"


def test_get_by_id_invalid_uuid_returns_422(client):
    response = client.get("/transcripts/not-a-uuid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /transcripts/{id}
# ---------------------------------------------------------------------------

def test_delete_existing_returns_204(client):
    create_resp = client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})
    analysis_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/transcripts/{analysis_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.content == b""


def test_delete_removes_from_store(client):
    create_resp = client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT})
    analysis_id = create_resp.json()["id"]

    client.delete(f"/transcripts/{analysis_id}")
    get_resp = client.get(f"/transcripts/{analysis_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_returns_404(client):
    response = client.delete(f"/transcripts/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Transcript not found"


def test_delete_only_removes_target(client):
    id_a = client.post("/transcripts", json={"transcript": COACHING_TRANSCRIPT}).json()["id"]
    id_b = client.post("/transcripts", json={"transcript": TIMESTAMPED_TRANSCRIPT}).json()["id"]

    client.delete(f"/transcripts/{id_a}")
    assert client.get(f"/transcripts/{id_a}").status_code == 404
    assert client.get(f"/transcripts/{id_b}").status_code == 200


# ---------------------------------------------------------------------------
# POST /transcripts/batch — concurrent analysis
# ---------------------------------------------------------------------------

def test_batch_returns_201_with_all_results(client):
    response = client.post(
        "/transcripts/batch",
        json={"transcripts": [COACHING_TRANSCRIPT, TIMESTAMPED_TRANSCRIPT]},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 2
    for item in body:
        assert uuid.UUID(item["id"])
        assert "created_at" in item


def test_batch_each_result_has_unique_id(client):
    response = client.post(
        "/transcripts/batch",
        json={"transcripts": [COACHING_TRANSCRIPT, TIMESTAMPED_TRANSCRIPT]},
    )
    ids = [item["id"] for item in response.json()]
    assert len(set(ids)) == 2


def test_batch_empty_list_returns_422(client):
    response = client.post("/transcripts/batch", json={"transcripts": []})
    assert response.status_code == 422


def test_batch_blank_item_in_list_returns_422(client):
    response = client.post(
        "/transcripts/batch",
        json={"transcripts": [COACHING_TRANSCRIPT, "   "]},
    )
    assert response.status_code == 422


def test_batch_missing_field_returns_422(client):
    response = client.post("/transcripts/batch", json={})
    assert response.status_code == 422
