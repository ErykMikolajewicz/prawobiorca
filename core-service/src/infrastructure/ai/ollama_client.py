import logging
import os

import ollama

from src.domain.exceptions.cases import LLMGenerationError

logger = logging.getLogger("app.ai.ollama")


class OllamaClient:
    def __init__(self, model_name: str | None = None, host: str | None = None):
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME") or "qwen2.5:3b"
        self.host = host or os.getenv("OLLAMA_HOST")
        self._client = ollama.AsyncClient(host=self.host) if self.host else ollama.AsyncClient()

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generuje tekst formalnego wniosku z poziomu modelu Ollama.
        """
        try:
            response = await self._client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.get("message", {}).get("content")
            if not content or not content.strip():
                logger.error("Model Ollama zwrócił pustą odpowiedź.")
                raise LLMGenerationError("Model Ollama wygenerował pustą treść wniosku.")

            return content.strip()
        except LLMGenerationError:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas komunikacji z Ollama (host={self.host}, model={self.model_name}): {e}")
            raise LLMGenerationError(f"Błąd podczas komunikacji z Ollama: {e}") from e
