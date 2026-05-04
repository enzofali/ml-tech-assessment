"""Guardrail tests: per-IP RPM rate limit and batch size cap.

The default conftest sets RATE_LIMIT_PER_MINUTE=0 (limiter is disabled). This
module overrides those env vars and reloads the rate-limit / routes / main
modules so the slowapi limiter is actually active, then verifies the 429 / 422
paths. State is restored at teardown so other test modules see the disabled
limiter.
"""
import importlib

import pytest
from starlette.testclient import TestClient

from app.api.dependencies import get_service
from tests.adapters.mock_data import TRANSCRIPT
from tests.api.test_routes import _make_mock_service


@pytest.fixture
def limited_client(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    monkeypatch.setenv("MAX_BATCH_SIZE", "2")

    import app.api.rate_limit as rl
    import app.api.routes as routes_mod
    import main as main_mod

    importlib.reload(rl)
    importlib.reload(routes_mod)
    importlib.reload(main_mod)

    service = _make_mock_service()
    main_mod.app.dependency_overrides[get_service] = lambda: service
    with TestClient(main_mod.app) as c:
        yield c
    main_mod.app.dependency_overrides.clear()

    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("MAX_BATCH_SIZE", "50")
    importlib.reload(rl)
    importlib.reload(routes_mod)
    importlib.reload(main_mod)


def test_rate_limit_blocks_excess_requests(limited_client):
    for _ in range(3):
        r = limited_client.post("/transcripts", json={"transcript": TRANSCRIPT})
        assert r.status_code == 201

    blocked = limited_client.post("/transcripts", json={"transcript": TRANSCRIPT})
    assert blocked.status_code == 429


def test_rate_limit_429_includes_retry_after_and_limit_headers(limited_client):
    """RFC 6585: 429 SHOULD include Retry-After. slowapi headers_enabled also
    sets X-RateLimit-{Limit,Remaining,Reset} so clients can back off precisely."""
    for _ in range(3):
        limited_client.post("/transcripts", json={"transcript": TRANSCRIPT})

    blocked = limited_client.post("/transcripts", json={"transcript": TRANSCRIPT})
    assert blocked.status_code == 429

    retry_after = blocked.headers.get("Retry-After")
    assert retry_after is not None, "429 must include a Retry-After header"
    assert int(retry_after) > 0

    assert blocked.headers.get("X-RateLimit-Limit") == "3"
    assert blocked.headers.get("X-RateLimit-Remaining") == "0"
    assert blocked.headers.get("X-RateLimit-Reset") is not None


def test_batch_size_cap_rejects_oversized_payload(limited_client):
    response = limited_client.post(
        "/transcripts/batch",
        json={"transcripts": [TRANSCRIPT, TRANSCRIPT, TRANSCRIPT]},
    )
    assert response.status_code == 422
    assert "batch size exceeds limit" in response.text


def test_batch_at_cap_is_accepted(limited_client):
    response = limited_client.post(
        "/transcripts/batch",
        json={"transcripts": [TRANSCRIPT, TRANSCRIPT]},
    )
    assert response.status_code == 201
    assert len(response.json()) == 2
