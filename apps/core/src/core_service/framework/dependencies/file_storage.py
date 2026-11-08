from collections.abc import Awaitable, Callable
from typing import Any

from core_service.infrastructure.object_storage.connection import init_object_storage_client


async def init_file_storage_client() -> tuple[Any, Any, Callable[..., Awaitable[None]]]:
    return await init_object_storage_client()
