from openai import APIError, AsyncOpenAI

from src.shared.exceptions import ServiceUnavailable


class LlmChat:
    def __init__(self, client: AsyncOpenAI, model_name: str, temperature: float, top_p: float, max_tokens: int):
        self._client = client
        self._model_name = model_name
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                top_p=self._top_p,
                presence_penalty=0.1,
            )
        except APIError as e:
            raise ServiceUnavailable() from e

        if not response.choices or not response.choices[0].message.content:
            raise ServiceUnavailable()

        return response.choices[0].message.content.strip()
