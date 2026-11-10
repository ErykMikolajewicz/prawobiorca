from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session

from core_service.shared.settings.object_storage import object_storage_settings

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

session = get_session()
exit_stack = AsyncExitStack()


async def _create_client(endpoint_url: str) -> S3Client:
    return await exit_stack.enter_async_context(
        session.create_client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=object_storage_settings.REGION,
            aws_access_key_id=object_storage_settings.ACCESS_KEY,
            aws_secret_access_key=object_storage_settings.SECRET_KEY,
            config=AioConfig(
                signature_version="s3v4",
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )
    )


async def init_object_storage_client() -> tuple[S3Client, S3Client, Callable[..., Awaitable[None]]]:
    client = await _create_client(object_storage_settings.ENDPOINT_URL)
    await client.head_bucket(Bucket=object_storage_settings.BUCKET)

    public_endpoint_url = object_storage_settings.PUBLIC_ENDPOINT_URL or object_storage_settings.ENDPOINT_URL
    if public_endpoint_url == object_storage_settings.ENDPOINT_URL:
        presign_client = client
    else:
        presign_client = await _create_client(public_endpoint_url)

    return client, presign_client, exit_stack.aclose
