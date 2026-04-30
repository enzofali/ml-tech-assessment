import openai
import pydantic
from app import ports
from app.ports.llm import LLMError
from app.metrics import llm_requests_total, record_llm_error, record_llm_usage

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_PROVIDER = "groq"


class GroqAdapter(ports.LLm):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)
        self._aclient = openai.AsyncOpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)

    def run_completion(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            if completion.usage:
                record_llm_usage(_PROVIDER, self._model, completion.usage.prompt_tokens, completion.usage.completion_tokens)
            llm_requests_total.labels(provider=_PROVIDER, model=self._model, status="success").inc()
            return dto.model_validate_json(completion.choices[0].message.content)
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            record_llm_error(_PROVIDER, self._model, exc)
            raise LLMError(str(exc)) from exc

    async def run_completion_async(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        try:
            completion = await self._aclient.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            if completion.usage:
                record_llm_usage(_PROVIDER, self._model, completion.usage.prompt_tokens, completion.usage.completion_tokens)
            llm_requests_total.labels(provider=_PROVIDER, model=self._model, status="success").inc()
            return dto.model_validate_json(completion.choices[0].message.content)
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            record_llm_error(_PROVIDER, self._model, exc)
            raise LLMError(str(exc)) from exc
