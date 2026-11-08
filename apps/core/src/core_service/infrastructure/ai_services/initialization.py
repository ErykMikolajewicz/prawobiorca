from collections.abc import Awaitable, Callable
from typing import Any

from core_service.shared.settings.application import HttpClientType, app_settings


async def init_ai_services_client() -> tuple[Any, Callable[..., Awaitable[None]]]:
    match app_settings.HTTP_CLIENT:
        case HttpClientType.HTTPX:
            from core_service.infrastructure.ai_services.httpx_client.connection import client

            return client, client.aclose
        case _:
            raise Exception(f"Invalid httpx client configuration {app_settings.HTTP_CLIENT} !")
