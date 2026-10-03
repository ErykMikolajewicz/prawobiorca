from openai import AsyncOpenAI

from src.shared.settings.ai_services import llm_service_settings

client = AsyncOpenAI(base_url=f"{llm_service_settings.URL}/v1", api_key="unused")
