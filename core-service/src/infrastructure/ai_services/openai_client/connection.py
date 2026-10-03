from openai import AsyncOpenAI

from src.infrastructure.ai_services.openai_client.google_auth import get_access_token
from src.shared.settings.ai_services import llm_service_settings

client = AsyncOpenAI(
    base_url=llm_service_settings.URL,
    api_key=get_access_token if llm_service_settings.USE_GOOGLE_AUTH else "unused",
)
