import uuid
from unittest.mock import MagicMock
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
