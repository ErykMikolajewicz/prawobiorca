import logging
import os

from openai import APIConnectionError, APIError, AsyncOpenAI

from src.domain.exceptions.cases import LLMGenerationError

logger = logging.getLogger("app.ai")


class OpenVINOClient:
    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
    ):
        base_url = base_url or os.getenv("OPENVINO_BASE_URL") or os.getenv("LLM_BASE_URL") or "http://localhost:8083/v1"
        configured_model = os.getenv("OPENVINO_MODEL_NAME") or os.getenv("LLM_MODEL_NAME") or "qwen-2.5-7b-it"
        model_name = model_name or configured_model
        api_key = api_key or os.getenv("OPENVINO_API_KEY") or "dummy-api-key"

        if temperature is None:
            try:
                temperature = float(os.getenv("OPENVINO_TEMPERATURE", "0.7"))
            except ValueError:
                temperature = 0.7

        if max_tokens is None:
            try:
                max_tokens = int(os.getenv("OPENVINO_MAX_TOKENS", "1000"))
            except ValueError:
                max_tokens = 1000

        if top_p is None:
            try:
                top_p = float(os.getenv("OPENVINO_TOP_P", "0.9"))
            except ValueError:
                top_p = 0.9

        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        """
        Generuje treść oficjalnego wniosku za pomocą serwera OpenVINO Model Server (OpenAI API compatible).
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            effective_temp = self.temperature if temperature is None else temperature

            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=effective_temp,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                presence_penalty=0.1,
            )

            if not response.choices:
                logger.error("Model OpenVINO zwrócił pustą listę odpowiedzi (brak choices).")
                raise LLMGenerationError("Serwer OpenVINO nie zwrócił żadnej odpowiedzi.")

            content = response.choices[0].message.content
            if not content or not content.strip():
                logger.error("Model OpenVINO zwrócił pustą treść odpowiedzi.")
                raise LLMGenerationError("Model OpenVINO wygenerował pustą treść wniosku.")

            return content.strip()
        except APIConnectionError as e:
            logger.error(f"Błąd połączenia z serwerem OpenVINO ({self._client.base_url}): {e}")
            raise LLMGenerationError(
                f"Nie można połączyć się z serwerem OpenVINO na {self._client.base_url}. Upewnij się, że usługa działa."
            ) from e
        except APIError as e:
            logger.error(f"Błąd API OpenAI/OpenVINO na modelu '{self.model_name}': {e}")
            raise LLMGenerationError(f"Błąd serwera OpenVINO: {e.message}") from e
        except LLMGenerationError:
            raise
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas generacji z OpenVINO na modelu '{self.model_name}': {e}")
            raise LLMGenerationError(f"Błąd podczas komunikacji z serwerem OpenVINO: {e}") from e
