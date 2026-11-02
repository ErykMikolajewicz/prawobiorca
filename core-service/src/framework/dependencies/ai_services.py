from typing import Annotated

from fastapi import Depends, Request
from httpx2 import AsyncClient

import src.infrastructure.ai_services.text_embedder as te
from src.app.ports.application_templates import ApplicationTemplateDescriptionWriter
from src.app.ports.regulations import RegulationDescriptionWriter
from src.app.ports.texts import TextsEmbedder
from src.infrastructure.ai_services.application_template_description_writer import (
    ApplicationTemplateDescriptionWriter as LlmApplicationTemplateDescriptionWriter,
)
from src.infrastructure.ai_services.llm_chat import LlmChat
from src.infrastructure.ai_services.llm_cost_limiter import LlmCostLimiter
from src.infrastructure.ai_services.openai_client.connection import client as llm_client
from src.infrastructure.ai_services.regulation_description_writer import (
    RegulationDescriptionWriter as LlmRegulationDescriptionWriter,
)
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.llm_usage import LlmUsageRepository
from src.shared.settings.ai_services import embedding_service_settings, llm_service_settings


def get_ai_services_client(request: Request) -> AsyncClient:
    return request.app.state.ai_services_client


def get_texts_embedder(
    client: Annotated[AsyncClient, Depends(get_ai_services_client)],
) -> TextsEmbedder:
    return te.TextsEmbedder(client=client, embedding_service_url=embedding_service_settings.URL)


def get_llm_chat() -> LlmChat:
    cost_limiter = None
    if llm_service_settings.MONTHLY_COST_LIMIT_PLN is not None:
        cost_limiter = LlmCostLimiter(
            async_session_maker, LlmUsageRepository(), llm_service_settings.MONTHLY_COST_LIMIT_PLN
        )
    return LlmChat(
        client=llm_client,
        model_name=llm_service_settings.MODEL_NAME,
        temperature=llm_service_settings.TEMPERATURE,
        top_p=llm_service_settings.TOP_P,
        max_tokens=llm_service_settings.MAX_TOKENS,
        cost_limiter=cost_limiter,
    )


def get_regulation_description_writer() -> RegulationDescriptionWriter:
    return LlmRegulationDescriptionWriter(get_llm_chat())


def get_application_template_description_writer() -> ApplicationTemplateDescriptionWriter:
    return LlmApplicationTemplateDescriptionWriter(get_llm_chat())
