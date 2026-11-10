from typing import Annotated

from fastapi import Depends, Request
from httpx2 import AsyncClient

from core_service.application.ports.texts import TextsEmbedder
from core_service.infrastructure.ai_services.text_embedder import HttpTextsEmbedder
from core_service.shared.settings.ai_services import embedding_service_settings


def get_ai_services_client(request: Request) -> AsyncClient:
    return request.app.state.ai_services_client


def get_texts_embedder(
    client: Annotated[AsyncClient, Depends(get_ai_services_client)],
) -> TextsEmbedder:
    return create_texts_embedder(client)


def create_texts_embedder(client: AsyncClient) -> TextsEmbedder:
    return HttpTextsEmbedder(client=client, embedding_service_url=embedding_service_settings.URL)
