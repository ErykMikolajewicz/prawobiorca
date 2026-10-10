import asyncio
import sys
import uuid
from pathlib import Path

sys.path.append("")

import httpx2
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from sqlalchemy import insert

from src.app.services.embedding import SectionsEmbedder
from src.app.services.regulations import RegulationPreparator
from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.infrastructure.ai_services.regulation_splitter import RegulationSplitter
from src.infrastructure.ai_services.text_embedder import TextsEmbedder
from src.infrastructure.object_storage.repository import S3RegulationsStorage
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository

# Unused import necessary for sqlalchemy
from src.infrastructure.relational_db.schemas.organizations import organizations_table  # noqa: F401
from src.infrastructure.relational_db.schemas.regulations import regulations_table
from src.infrastructure.relational_db.schemas.users import users_table  # noqa: F401
from src.infrastructure.tokenizers.mmlw import MmlwTokenizer
from src.shared.settings.ai_services import (
    embedding_service_settings,
    extraction_service_settings,
)
from src.shared.settings.object_storage import object_storage_settings

REGULATION_TYPES_BY_FILE_NAME = {
    "Prawo o nauce i szkolnictwie wyższym.pdf": RegulationType.ACT,
    "PWr - regulamin studiow.pdf": RegulationType.STATUTE,
    "PWr - reguamin akademik.pdf": RegulationType.STATUTE,
}


async def init_regulations():
    init_files_dir = Path("scripts/files")
    session = get_session()

    async with (
        httpx2.AsyncClient(timeout=900) as client,
        session.create_client(
            "s3",
            endpoint_url=object_storage_settings.ENDPOINT_URL,
            region_name=object_storage_settings.REGION,
            aws_access_key_id=object_storage_settings.ACCESS_KEY,
            aws_secret_access_key=object_storage_settings.SECRET_KEY,
            config=AioConfig(signature_version="s3v4"),
        ) as s3_client,
    ):
        try:
            await s3_client.head_bucket(Bucket=object_storage_settings.BUCKET)
        except ClientError:
            await s3_client.create_bucket(Bucket=object_storage_settings.BUCKET)

        regulations_storage = S3RegulationsStorage(s3_client, s3_client)
        texts_embedder = TextsEmbedder(
            client=client,
            embedding_service_url=embedding_service_settings.URL,
        )
        regulation_splitter = RegulationSplitter(
            client=client,
            extraction_service_url=extraction_service_settings.URL,
        )
        sections_embedder = SectionsEmbedder(texts_embedder, embedding_service_settings.BATCH_SIZE)
        tokenizer = MmlwTokenizer()
        regulation_preparator = RegulationPreparator(
            regulation_splitter,
            sections_embedder,
            tokenizer,
        )

        print("Start preparing regulations")
        for file_path in init_files_dir.iterdir():
            file_name = file_path.name

            with open(file_path, "rb") as file:
                file_content = file.read()

            regulation_id = uuid.uuid4()
            regulation_type = REGULATION_TYPES_BY_FILE_NAME.get(file_name)

            sections_to_embed = await regulation_preparator.prepare_regulation(file_content)
            print(f"Embedded regulation: {file_name}")

            async with async_session_maker.begin() as session:
                await session.execute(
                    insert(regulations_table),
                    [
                        {
                            "id": regulation_id,
                            "presentation_name": file_name,
                            "preparation_status": RegulationPreparationStatus.PREPARED,
                            "user_id": None,
                            "regulation_type": regulation_type,
                        }
                    ],
                )

                await RegulationsSectionsRepository.add_sections(session, None, regulation_id, sections_to_embed)

                await regulations_storage.upload_regulation(id_=regulation_id, file_data=file_content)

            print(f"Saved regulation: {file_name}, ")


async def main():
    await init_regulations()


if __name__ == "__main__":
    asyncio.run(main())
