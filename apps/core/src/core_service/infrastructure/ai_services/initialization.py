from collections.abc import Awaitable, Callable

from httpx2 import AsyncClient

from core_service.infrastructure.ai_services.httpx_client.connection import client


async def init_ai_services_client() -> tuple[AsyncClient, Callable[..., Awaitable[None]]]:
    return client, client.aclose
