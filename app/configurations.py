import pydantic_settings
from typing import Literal


class EnvConfigs(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    LLM_PROVIDER: Literal["openai", "gemini", "groq"] = "groq"
    LLM_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    DATABASE_URL: str | None = None  # postgresql://user:pass@host:5432/db — falls back to in-memory when unset
