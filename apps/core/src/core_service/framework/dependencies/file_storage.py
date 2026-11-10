from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from fastapi import Request

from core_service.application.ports.application_templates import ApplicationTemplatesStorage
from core_service.application.ports.applications import ApplicationsStorage
from core_service.application.ports.regulations import RegulationsStorage
from core_service.infrastructure.object_storage.connection import init_object_storage_client
from core_service.infrastructure.object_storage.repository import (
    S3ApplicationsStorage,
    S3ApplicationTemplatesStorage,
    S3RegulationsStorage,
)
from core_service.shared.settings.object_storage import object_storage_settings

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client


async def init_file_storage_client() -> tuple[S3Client, S3Client, Callable[..., Awaitable[None]]]:
    return await init_object_storage_client()


def get_file_storage_client(request: Request) -> Any:
    return request.app.state.file_storage_client


def get_file_storage_presign_client(request: Request) -> Any:
    return request.app.state.file_storage_presign_client


def create_regulations_storage(client: S3Client, presign_client: S3Client) -> RegulationsStorage:
    return S3RegulationsStorage(
        client,
        presign_client,
        bucket=object_storage_settings.BUCKET,
        signed_url_expiration_seconds=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        max_file_size_bytes=object_storage_settings.MAX_FILE_SIZE_BYTES,
    )


def create_applications_storage(client: S3Client, presign_client: S3Client) -> ApplicationsStorage:
    return S3ApplicationsStorage(
        client,
        presign_client,
        bucket=object_storage_settings.BUCKET,
        signed_url_expiration_seconds=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
    )


def create_application_templates_storage(client: S3Client, presign_client: S3Client) -> ApplicationTemplatesStorage:
    return S3ApplicationTemplatesStorage(
        client,
        presign_client,
        bucket=object_storage_settings.BUCKET,
        signed_url_expiration_seconds=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        max_file_size_bytes=object_storage_settings.MAX_FILE_SIZE_BYTES,
    )
