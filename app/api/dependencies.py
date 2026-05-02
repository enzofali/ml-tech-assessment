import fastapi
from functools import lru_cache
from app.adapters.openai import OpenAIAdapter
from app.adapters.gemini import GeminiAdapter
from app.adapters.groq import GroqAdapter
from app.configurations import EnvConfigs
from app.ports.llm import LLm
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.transcript import TranscriptService


@lru_cache
def get_configs() -> EnvConfigs:
    return EnvConfigs()


@lru_cache
def get_repository() -> InMemoryAnalysisRepository:
    return InMemoryAnalysisRepository()


@lru_cache
def get_llm() -> LLm:
    configs = get_configs()
    if configs.LLM_PROVIDER == "openai":
        return OpenAIAdapter(api_key=configs.LLM_API_KEY, model=configs.LLM_MODEL)
    if configs.LLM_PROVIDER == "gemini":
        return GeminiAdapter(api_key=configs.LLM_API_KEY, model=configs.LLM_MODEL)
    if configs.LLM_PROVIDER == "groq":
        return GroqAdapter(api_key=configs.LLM_API_KEY, model=configs.LLM_MODEL)
    raise ValueError(f"Unknown LLM provider: {configs.LLM_PROVIDER}")


def get_service(
    llm: LLm = fastapi.Depends(get_llm),
    repository: InMemoryAnalysisRepository = fastapi.Depends(get_repository),
) -> TranscriptService:
    return TranscriptService(llm=llm, repository=repository)
