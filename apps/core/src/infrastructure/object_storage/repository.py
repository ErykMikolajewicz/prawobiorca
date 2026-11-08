from dataclasses import dataclass
from typing import Any
from uuid import UUID

from botocore.exceptions import ClientError

from src.app.dtos.application_templates import ApplicationTemplateUploadTarget
from src.app.dtos.regulations import RegulationUploadTarget
from src.domain.exceptions.application_templates import ApplicationTemplateContentNotFound
from src.domain.exceptions.regulations import RegulationContentNotFound
from src.shared.settings.object_storage import object_storage_settings


@dataclass
class S3RegulationsStorage:
    client: Any
    presign_client: Any

    async def get_regulation(self, id_: UUID) -> bytes:
        try:
            response = await self.client.get_object(Bucket=object_storage_settings.BUCKET, Key=str(id_))
        except ClientError:
            raise RegulationContentNotFound

        async with response["Body"] as stream:
            return await stream.read()

    async def upload_regulation(self, id_: UUID, file_data: bytes) -> None:
        await self.client.put_object(Bucket=object_storage_settings.BUCKET, Key=str(id_), Body=file_data)

    async def delete_regulation(self, id_: UUID) -> None:
        await self.client.delete_object(Bucket=object_storage_settings.BUCKET, Key=str(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": object_storage_settings.BUCKET,
                "Key": str(id_),
                "ResponseContentDisposition": "inline",
                "ResponseContentType": "application/pdf",
            },
            ExpiresIn=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        )

    async def get_upload_target(self, id_: UUID) -> RegulationUploadTarget:
        response = await self.presign_client.generate_presigned_post(
            Bucket=object_storage_settings.BUCKET,
            Key=str(id_),
            Conditions=[["content-length-range", 1, object_storage_settings.MAX_FILE_SIZE_BYTES]],
            ExpiresIn=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        )

        return RegulationUploadTarget(id=id_, url=response["url"], fields=response["fields"])

    async def check_regulation_exists(self, id_: UUID) -> bool:
        try:
            await self.client.head_object(Bucket=object_storage_settings.BUCKET, Key=str(id_))
            return True
        except ClientError:
            return False


@dataclass
class S3ApplicationsStorage:
    client: Any
    presign_client: Any

    async def upload_application(self, id_: UUID, file_data: bytes) -> None:
        await self.client.put_object(Bucket=object_storage_settings.BUCKET, Key=self._get_key(id_), Body=file_data)

    async def delete_application(self, id_: UUID) -> None:
        await self.client.delete_object(Bucket=object_storage_settings.BUCKET, Key=self._get_key(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": object_storage_settings.BUCKET,
                "Key": self._get_key(id_),
                "ResponseContentDisposition": f"attachment; filename=wniosek_{id_}.docx",
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            ExpiresIn=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        )

    @staticmethod
    def _get_key(id_: UUID) -> str:
        return f"applications/{id_}"


@dataclass
class S3ApplicationTemplatesStorage:
    client: Any
    presign_client: Any

    async def get_upload_target(self, id_: UUID) -> ApplicationTemplateUploadTarget:
        response = await self.presign_client.generate_presigned_post(
            Bucket=object_storage_settings.BUCKET,
            Key=self._get_key(id_),
            Conditions=[["content-length-range", 1, object_storage_settings.MAX_FILE_SIZE_BYTES]],
            ExpiresIn=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        )

        return ApplicationTemplateUploadTarget(id=id_, url=response["url"], fields=response["fields"])

    async def get_template(self, id_: UUID) -> bytes:
        try:
            response = await self.client.get_object(Bucket=object_storage_settings.BUCKET, Key=self._get_key(id_))
        except ClientError:
            raise ApplicationTemplateContentNotFound

        async with response["Body"] as stream:
            return await stream.read()

    async def delete_template(self, id_: UUID) -> None:
        await self.client.delete_object(Bucket=object_storage_settings.BUCKET, Key=self._get_key(id_))

    async def get_download_url(self, id_: UUID) -> str:
        return await self.presign_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": object_storage_settings.BUCKET,
                "Key": self._get_key(id_),
                "ResponseContentDisposition": f"attachment; filename=szablon_{id_}.docx",
                "ResponseContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            ExpiresIn=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
        )

    @staticmethod
    def _get_key(id_: UUID) -> str:
        return f"application_templates/{id_}"
