import openai
import pydantic
from app import ports
from app.ports.llm import LLMError


class OpenAIAdapter(ports.LLm):
    def __init__(self, api_key: str, model: str) -> None:
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
            completion = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=dto,
            )
            return completion.choices[0].message.parsed
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            raise LLMError(str(exc)) from exc

    async def run_completion_async(self, system_prompt: str, user_prompt: str,
                                   dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
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
            completion = await self._aclient.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=dto,
            )
            return completion.choices[0].message.parsed
        except (openai.OpenAIError, pydantic.ValidationError) as exc:
            raise LLMError(str(exc)) from exc
