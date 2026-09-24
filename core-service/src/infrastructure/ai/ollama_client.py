import os

import ollama

from src.domain.exceptions.cases import LLMGenerationError


class OllamaClient:
    def __init__(self, model_name: str | None = None, host: str | None = None):
        if not model_name:
            model_name = os.getenv("OLLAMA_MODEL_NAME")
            if not model_name:
                try:
                    with open(".env", "r") as f:
                        for line in f:
                            if line.startswith("OLLAMA_MODEL_NAME="):
                                model_name = line.strip().split("=", 1)[1].strip('"').strip("'")
                                break
                except Exception:
                    pass

        self.model_name = model_name
        if not self.model_name:
            raise ValueError("Brak zmiennej środowiskowej OLLAMA_MODEL_NAME")
        host = host or os.getenv("OLLAMA_HOST")
        self._client = ollama.AsyncClient(host=host) if host else ollama.AsyncClient()

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
            return response["message"]["content"].strip()
        except Exception as e:
            raise LLMGenerationError(f"Błąd podczas komunikacji z Ollama: {e}") from e
