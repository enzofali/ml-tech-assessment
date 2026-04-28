import fastapi
from functools import lru_cache
from app.adapters.openai import OpenAIAdapter
from app.configurations import EnvConfigs
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.transcript import TranscriptService


@lru_cache
def get_configs() -> EnvConfigs:
    return EnvConfigs()


@lru_cache
def get_repository() -> InMemoryAnalysisRepository:
    return InMemoryAnalysisRepository()


@lru_cache
def get_llm() -> OpenAIAdapter:
    configs = get_configs()
    return OpenAIAdapter(api_key=configs.OPENAI_API_KEY, model=configs.OPENAI_MODEL)


def get_service(
    llm: OpenAIAdapter = fastapi.Depends(get_llm),
    repository: InMemoryAnalysisRepository = fastapi.Depends(get_repository),
) -> TranscriptService:
    return TranscriptService(llm=llm, repository=repository)
