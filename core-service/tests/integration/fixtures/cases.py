from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.value_objects.applications import ApplicationGenerationStatus
from src.infrastructure.relational_db.schemas.applications import applications_table
from src.infrastructure.relational_db.schemas.cases import case_documents_table, cases_table
from tests.consts import USER_ID


async def insert_case(session: AsyncSession, user_id: UUID = USER_ID, name: str = "Case", **values: Any) -> UUID:
    result = await session.execute(
        insert(cases_table).values(user_id=user_id, name=name, **values).returning(cases_table.c.id)
    )
    return result.scalar_one()


async def insert_case_document(
    session: AsyncSession,
    case_id: UUID,
    user_id: UUID = USER_ID,
    presentation_name: str = "document.pdf",
    content: str = "Document content",
    **values: Any,
) -> UUID:
    result = await session.execute(
        insert(case_documents_table)
        .values(case_id=case_id, user_id=user_id, presentation_name=presentation_name, content=content, **values)
        .returning(case_documents_table.c.id)
    )
    return result.scalar_one()


async def insert_application(
    session: AsyncSession,
    case_id: UUID,
    generation_status: ApplicationGenerationStatus = ApplicationGenerationStatus.GENERATED,
    **values: Any,
) -> UUID:
    result = await session.execute(
        insert(applications_table)
        .values(
            case_id=case_id,
            user_id=USER_ID,
            template_name="Wniosek o urlop",
            generation_status=generation_status,
            **values,
        )
        .returning(applications_table.c.id)
    )
    return result.scalar_one()
