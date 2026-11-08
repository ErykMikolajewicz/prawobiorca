from httpx2 import AsyncClient, Limits, Timeout

from src.shared.settings.httpx_client import httpx_client_settings

client = AsyncClient(
    timeout=Timeout(httpx_client_settings.TIMEOUT),
    limits=Limits(
        max_connections=httpx_client_settings.MAX_CONNECTIONS,
        max_keepalive_connections=httpx_client_settings.MAX_KEEP_ALIVE_CONNECTIONS,
    ),
)
