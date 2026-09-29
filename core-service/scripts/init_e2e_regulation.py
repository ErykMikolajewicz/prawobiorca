import asyncio
import json
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path

sys.path.append("")

import httpx2
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from sqlalchemy import insert, select

from src.app.services.embedding import SectionsEmbedder
from src.app.services.regulations import RegulationPreparator
from src.domain.value_objects.legal_units import RegulationElement
from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.infrastructure.ai_services.text_embedder import TextsEmbedder
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository
from src.infrastructure.relational_db.schemas.regulations import regulations_table

# Unused import necessary for sqlalchemy
from src.infrastructure.relational_db.schemas.users import users_table  # noqa: F401
from src.infrastructure.tokenizers.mmlw import MmlwTokenizer
from src.shared.settings.ai_services import embedding_service_settings
from src.shared.settings.object_storage import object_storage_settings

REGULATION_ELEMENTS_FILE = Path("tests/data/ustawa-nauka_slice_30-31.json")
REGULATION_NAME = "Prawo o nauce i szkolnictwie wyższym - fragment"


class JsonRegulationSplitter:
    async def split(self, regulation: bytes) -> Iterable[RegulationElement]:
        return [RegulationElement(label=item["label"], text=item["text"]) for item in json.loads(regulation)]


async def create_bucket():
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=object_storage_settings.ENDPOINT_URL,
        region_name=object_storage_settings.REGION,
        aws_access_key_id=object_storage_settings.ACCESS_KEY,
        aws_secret_access_key=object_storage_settings.SECRET_KEY,
        config=AioConfig(signature_version="s3v4"),
    ) as s3_client:
        try:
            await s3_client.head_bucket(Bucket=object_storage_settings.BUCKET)
        except ClientError:
            await s3_client.create_bucket(Bucket=object_storage_settings.BUCKET)


async def regulation_exists() -> bool:
    async with async_session_maker() as session:
        result = await session.execute(
            select(regulations_table.c.id).where(
                regulations_table.c.presentation_name == REGULATION_NAME,
                regulations_table.c.user_id.is_(None),
            )
        )
        return result.first() is not None


async def init_e2e_regulation():
    await create_bucket()

    if await regulation_exists():
        print(f"Regulation already exists: {REGULATION_NAME}")
        return

    async with httpx2.AsyncClient(timeout=900) as client:
        texts_embedder = TextsEmbedder(
            client=client,
            embedding_service_url=embedding_service_settings.URL,
        )
        sections_embedder = SectionsEmbedder(texts_embedder, embedding_service_settings.BATCH_SIZE)
        regulation_preparator = RegulationPreparator(
            JsonRegulationSplitter(),
            sections_embedder,
            MmlwTokenizer(),
        )

        sections_to_embed = await regulation_preparator.prepare_regulation(REGULATION_ELEMENTS_FILE.read_bytes())

    regulation_id = uuid.uuid4()

    async with async_session_maker.begin() as session:
        await session.execute(
            insert(regulations_table),
            [
                {
                    "id": regulation_id,
                    "presentation_name": REGULATION_NAME,
                    "preparation_status": RegulationPreparationStatus.PREPARED,
                    "user_id": None,
                    "regulation_type": RegulationType.ACT,
                }
            ],
        )

        await RegulationsSectionsRepository.add_sections(session, None, regulation_id, sections_to_embed)

    print(f"Saved regulation: {REGULATION_NAME}")


if __name__ == "__main__":
    asyncio.run(init_e2e_regulation())
