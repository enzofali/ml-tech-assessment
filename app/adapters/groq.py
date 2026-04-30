import openai
import pydantic
from app import ports

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqAdapter(ports.LLm):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)
        self._aclient = openai.AsyncOpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)

    def run_completion(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return dto.model_validate_json(completion.choices[0].message.content)

    async def run_completion_async(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        completion = await self._aclient.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return dto.model_validate_json(completion.choices[0].message.content)
