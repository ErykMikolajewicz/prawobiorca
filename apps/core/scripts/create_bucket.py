import asyncio

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from core_service.shared.settings.object_storage import object_storage_settings


async def create_bucket():
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=object_storage_settings.ENDPOINT_URL,
        region_name=object_storage_settings.REGION,
        aws_access_key_id=object_storage_settings.ACCESS_KEY,
        aws_secret_access_key=object_storage_settings.SECRET_KEY.get_secret_value(),
        config=AioConfig(signature_version="s3v4"),
    ) as s3_client:
        try:
            await s3_client.head_bucket(Bucket=object_storage_settings.BUCKET)
        except ClientError:
            await s3_client.create_bucket(Bucket=object_storage_settings.BUCKET)


if __name__ == "__main__":
    asyncio.run(create_bucket())
