import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock
from app.models.transcript import TranscriptAnalysis, TranscriptAnalysisDTO
from app.services.transcript import TranscriptService


def make_service():
    llm = MagicMock()
    repository = MagicMock()
    return TranscriptService(llm=llm, repository=repository), llm, repository


def test_analyze_calls_llm_with_formatted_prompt():
    service, llm, _ = make_service()
    llm.run_completion.return_value = TranscriptAnalysisDTO(
        summary="Summary", action_items=["Item 1"]
    )

    service.analyze("Hello world")

    llm.run_completion.assert_called_once()
    call = llm.run_completion.call_args
    user_prompt = call.kwargs.get("user_prompt") or call.args[1]
    assert "Hello world" in user_prompt


def test_analyze_saves_and_returns_analysis():
    service, llm, repository = make_service()
    llm.run_completion.return_value = TranscriptAnalysisDTO(
        summary="Test summary", action_items=["Do this", "Do that"]
    )

    result = service.analyze("Some transcript")

    assert isinstance(result.id, uuid.UUID)
    assert result.summary == "Test summary"
    assert result.action_items == ["Do this", "Do that"]
    repository.save.assert_called_once_with(result)


def test_get_by_id_delegates_to_repository():
    service, _, repository = make_service()
    expected = TranscriptAnalysis(
        id=uuid.uuid4(), summary="s", action_items=["a"]
    )
    repository.get_by_id.return_value = expected

    result = service.get_by_id(expected.id)

    assert result == expected
    repository.get_by_id.assert_called_once_with(expected.id)


def test_get_by_id_returns_none_when_not_found():
    service, _, repository = make_service()
    repository.get_by_id.return_value = None

    result = service.get_by_id(uuid.uuid4())

    assert result is None


def test_analyze_batch_runs_concurrently_and_returns_all():
    service, llm, repository = make_service()
    llm.run_completion_async = AsyncMock(side_effect=[
        TranscriptAnalysisDTO(summary="Summary A", action_items=["A1"]),
        TranscriptAnalysisDTO(summary="Summary B", action_items=["B1"]),
    ])

    results = asyncio.run(service.analyze_batch(["Transcript A", "Transcript B"]))

    assert len(results) == 2
    assert results[0].summary == "Summary A"
    assert results[1].summary == "Summary B"
    assert llm.run_completion_async.call_count == 2
    assert repository.save.call_count == 2


def test_analyze_batch_includes_transcript_in_prompt():
    service, llm, _ = make_service()
    llm.run_completion_async = AsyncMock(return_value=TranscriptAnalysisDTO(summary="s", action_items=[]))

    asyncio.run(service.analyze_batch(["Hello batch"]))

    call = llm.run_completion_async.call_args
    user_prompt = call.kwargs.get("user_prompt") or call.args[1]
    assert "Hello batch" in user_prompt
