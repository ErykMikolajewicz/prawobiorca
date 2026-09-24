import logging
import os
import sys
from pathlib import Path

# Zapewnienie dostępu do pakietu src przy bezpośrednim uruchomieniu pliku jako skrypt
core_service_dir = Path(__file__).resolve().parents[3]
if str(core_service_dir) not in sys.path:
    sys.path.insert(0, str(core_service_dir))

from openai import AsyncOpenAI  # noqa: E402

from src.domain.exceptions.cases import LLMGenerationError  # noqa: E402

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

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generuje treść oficjalnego wniosku za pomocą serwera OpenVINO Model Server (OpenAI API compatible).
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                presence_penalty=0.1,
            )
            content = response.choices[0].message.content
            if not content:
                logger.error("Model OpenVINO zwrócił pustą odpowiedź (content is None lub pusty).")
                raise LLMGenerationError("Model OpenVINO zwrócił pustą odpowiedź.")
            return content.strip()
        except Exception as e:
            logger.error(f"Błąd połączenia lub generacji z serwerem OpenVINO na modelu '{self.model_name}': {e}")
            raise LLMGenerationError(f"Błąd podczas komunikacji z serwerem OpenVINO: {e}") from e


if __name__ == "__main__":
    import asyncio
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    async def main():
        client = OpenVINOClient()
        print("[OpenVINOClient] Zainicjalizowano klienta:")
        print(f"  Model: {client.model_name}")
        print(f"  Endpoint: {client._client.base_url}")
        prompt = "Potwierdź jednym krótkim zdaniem, że serwer działa prawidłowo."
        print(f"[OpenVINOClient] Testowe zapytanie: '{prompt}'...")
        try:
            res = await client.generate_text("Jesteś pomocnym asystentem.", prompt)
            print(f"[OpenVINOClient] Odpowiedź modelu:\n{res}")
        except Exception as err:
            print(f"[OpenVINOClient] Błąd podczas wywołania: {err}")

    asyncio.run(main())

