import openai
import pydantic
from app import ports

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiAdapter(ports.LLm):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=_GEMINI_BASE_URL)
        self._aclient = openai.AsyncOpenAI(api_key=api_key, base_url=_GEMINI_BASE_URL)

    def run_completion(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        completion = self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=dto,
        )
        return completion.choices[0].message.parsed

    async def run_completion_async(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        completion = await self._aclient.beta.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=dto,
        )
        return completion.choices[0].message.parsed
