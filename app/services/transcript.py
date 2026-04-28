import asyncio
import uuid
from app.models.transcript import TranscriptAnalysis, TranscriptAnalysisDTO
from app.ports.llm import LLm
from app.ports.repository import AnalysisRepository
from app.prompts import SYSTEM_PROMPT, RAW_USER_PROMPT
from app.text_normalizer import NormalizationStrategy, normalize


class TranscriptService:
    def __init__(
        self,
        llm: LLm,
        repository: AnalysisRepository,
        normalization_strategy: NormalizationStrategy = NormalizationStrategy.CONSERVATIVE,
    ) -> None:
        self._llm = llm
        self._repository = repository
        self._normalization_strategy = normalization_strategy

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        user_prompt = RAW_USER_PROMPT.format(transcript=normalize(transcript, self._normalization_strategy))
        dto: TranscriptAnalysisDTO = self._llm.run_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            dto=TranscriptAnalysisDTO,
        )
        analysis = TranscriptAnalysis(
            id=uuid.uuid4(),
            summary=dto.summary,
            action_items=dto.action_items,
        )
        self._repository.save(analysis)
        return analysis

    async def analyze_async(self, transcript: str) -> TranscriptAnalysis:
        user_prompt = RAW_USER_PROMPT.format(transcript=normalize(transcript, self._normalization_strategy))
        dto: TranscriptAnalysisDTO = await self._llm.run_completion_async(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            dto=TranscriptAnalysisDTO,
        )
        analysis = TranscriptAnalysis(
            id=uuid.uuid4(),
            summary=dto.summary,
            action_items=dto.action_items,
        )
        self._repository.save(analysis)
        return analysis

    async def analyze_batch(self, transcripts: list[str], max_concurrent: int = 5) -> list[TranscriptAnalysis]:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded(transcript: str) -> TranscriptAnalysis:
            async with semaphore:
                return await self.analyze_async(transcript)

        return list(await asyncio.gather(*[bounded(t) for t in transcripts]))

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        return self._repository.get_by_id(id)

    def list_all(self) -> list[TranscriptAnalysis]:
        return self._repository.list_all()

    def delete(self, id: uuid.UUID) -> bool:
        return self._repository.delete(id)
