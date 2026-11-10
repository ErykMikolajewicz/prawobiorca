from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError

from core_service.application.dtos.application_templates import ApplicationTemplateUploadTarget
from core_service.application.dtos.regulations import RegulationUploadTarget
from core_service.domain.exceptions.application_templates import ApplicationTemplateContentNotFound
from core_service.domain.exceptions.regulations import RegulationContentNotFound
from core_service.infrastructure.service_errors import get_status_error
from core_service.shared.exceptions import ServiceUnavailable

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client


@contextmanager
def map_storage_errors(not_found_error: type[Exception] | None = None) -> Generator[None]:
    try:
        yield
    except ClientError as e:
        status_code = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", HTTPStatus.INTERNAL_SERVER_ERROR)
        if not_found_error is not None and status_code == HTTPStatus.NOT_FOUND:
            raise not_found_error from e
        raise get_status_error(status_code) from e
    except BotoCoreError as e:
        raise ServiceUnavailable() from e


@dataclass
class S3RegulationsStorage:
    client: S3Client
    presign_client: S3Client
    bucket: str
    signed_url_expiration_seconds: int
    max_file_size_bytes: int

    async def get_regulation(self, id_: UUID) -> bytes:
        with map_storage_errors(RegulationContentNotFound):
            response = await self.client.get_object(Bucket=self.bucket, Key=str(id_))
            async with response["Body"] as stream:
                return await stream.read()

    async def upload_regulation(self, id_: UUID, file_data: bytes) -> None:
        with map_storage_errors():
            await self.client.put_object(Bucket=self.bucket, Key=str(id_), Body=file_data)

    async def delete_regulation(self, id_: UUID) -> None:
        with map_storage_errors():
            await self.client.delete_object(Bucket=self.bucket, Key=str(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": str(id_),
                "ResponseContentDisposition": "inline",
                "ResponseContentType": "application/pdf",
            },
            ExpiresIn=self.signed_url_expiration_seconds,
        )

    async def get_upload_target(self, id_: UUID) -> RegulationUploadTarget:
        response = await self.presign_client.generate_presigned_post(
            Bucket=self.bucket,
            Key=str(id_),
            Conditions=[["content-length-range", 1, self.max_file_size_bytes]],
            ExpiresIn=self.signed_url_expiration_seconds,
        )

        return RegulationUploadTarget(id=id_, url=response["url"], fields=response["fields"])

    async def check_regulation_exists(self, id_: UUID) -> bool:
        try:
            with map_storage_errors(RegulationContentNotFound):
                await self.client.head_object(Bucket=self.bucket, Key=str(id_))
            return True
        except RegulationContentNotFound:
            return False


@dataclass
class S3ApplicationsStorage:
    client: S3Client
    presign_client: S3Client
    bucket: str
    signed_url_expiration_seconds: int

    async def upload_application(self, id_: UUID, file_data: bytes) -> None:
        with map_storage_errors():
            await self.client.put_object(Bucket=self.bucket, Key=self._get_key(id_), Body=file_data)

    async def delete_application(self, id_: UUID) -> None:
        with map_storage_errors():
            await self.client.delete_object(Bucket=self.bucket, Key=self._get_key(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": self._get_key(id_),
                "ResponseContentDisposition": f"attachment; filename=wniosek_{id_}.docx",
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            ExpiresIn=self.signed_url_expiration_seconds,
        )

    @staticmethod
    def _get_key(id_: UUID) -> str:
        return f"applications/{id_}"


@dataclass
class S3ApplicationTemplatesStorage:
    client: S3Client
    presign_client: S3Client
    bucket: str
    signed_url_expiration_seconds: int
    max_file_size_bytes: int

    async def get_upload_target(self, id_: UUID) -> ApplicationTemplateUploadTarget:
        response = await self.presign_client.generate_presigned_post(
            Bucket=self.bucket,
            Key=self._get_key(id_),
            Conditions=[["content-length-range", 1, self.max_file_size_bytes]],
            ExpiresIn=self.signed_url_expiration_seconds,
        )

        return ApplicationTemplateUploadTarget(id=id_, url=response["url"], fields=response["fields"])

    async def get_template(self, id_: UUID) -> bytes:
        with map_storage_errors(ApplicationTemplateContentNotFound):
            response = await self.client.get_object(Bucket=self.bucket, Key=self._get_key(id_))
            async with response["Body"] as stream:
                return await stream.read()

    async def delete_template(self, id_: UUID) -> None:
        with map_storage_errors():
            await self.client.delete_object(Bucket=self.bucket, Key=self._get_key(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": self._get_key(id_),
                "ResponseContentDisposition": f"attachment; filename=szablon_{id_}.docx",
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            ExpiresIn=self.signed_url_expiration_seconds,
        )

    @staticmethod
    def _get_key(id_: UUID) -> str:
        return f"application_templates/{id_}"
