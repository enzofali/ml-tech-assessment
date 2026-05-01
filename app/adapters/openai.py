import time
import openai
import pydantic
from app import ports
from app.ports.llm import LLMError
from app.metrics import llm_request_duration_seconds, llm_requests_total, record_llm_error, record_llm_usage

_PROVIDER = "openai"


class OpenAIAdapter(ports.LLm):
    def __init__(self, api_key: str, model: str) -> None:
        """
        Initializes the OpenAI adapter with the given API key and model.

        Args:
            api_key (str): The OpenAI API key used to authenticate requests.
            model (str): The model identifier to use for completions (e.g. "gpt-4o").
        """
        self._model = model
        self._client = openai.OpenAI(api_key=api_key)
        self._aclient = openai.AsyncOpenAI(api_key=api_key)

    def run_completion(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        """
        Executes a completion request using the OpenAI API with the provided prompts and response format.

        Args:
            system_prompt (str): The system's introductory message for the chat.
            user_prompt (str): The user input for which a response is needed.
            dto (Type[pydantic.BaseModel]): A Pydantic model class used to define the structure of the API response.

        Returns:
            pydantic.BaseModel: An instance of the provided DTO class populated with the API response data.
            more info: https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat
        """
        try:
            t0 = time.perf_counter()
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=dto,
            )
            llm_request_duration_seconds.labels(provider=_PROVIDER, model=self._model).observe(time.perf_counter() - t0)
            if completion.usage:
                record_llm_usage(_PROVIDER, self._model, completion.usage.prompt_tokens, completion.usage.completion_tokens)
            llm_requests_total.labels(provider=_PROVIDER, model=self._model, status="success").inc()
            return completion.choices[0].message.parsed
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            record_llm_error(_PROVIDER, self._model, exc)
            raise LLMError(str(exc)) from exc

    async def run_completion_async(self, system_prompt: str, user_prompt: str,
                                   dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        """
        Asynchronously executes a completion request using the OpenAI API with the provided prompts and response format.

        Args:
            system_prompt (str): The system's introductory message for the chat.
            user_prompt (str): The user input for which a response is needed.
            dto (Type[pydantic.BaseModel]): A Pydantic model class used to define the structure of the API response.

        Returns:
            pydantic.BaseModel: An instance of the provided DTO class populated with the API response data.
            more info: https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat
        """
        try:
            t0 = time.perf_counter()
            completion = await self._aclient.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=dto,
            )
            llm_request_duration_seconds.labels(provider=_PROVIDER, model=self._model).observe(time.perf_counter() - t0)
            if completion.usage:
                record_llm_usage(_PROVIDER, self._model, completion.usage.prompt_tokens, completion.usage.completion_tokens)
            llm_requests_total.labels(provider=_PROVIDER, model=self._model, status="success").inc()
            return completion.choices[0].message.parsed
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            record_llm_error(_PROVIDER, self._model, exc)
            raise LLMError(str(exc)) from exc
