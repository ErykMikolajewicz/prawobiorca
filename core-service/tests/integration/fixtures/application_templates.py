from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.value_objects.application_templates import ApplicationTemplateStatus
from src.infrastructure.relational_db.schemas.application_templates import application_templates_table


async def insert_application_template(
    session: AsyncSession,
    name: str = "Wniosek",
    status: ApplicationTemplateStatus = ApplicationTemplateStatus.DRAFT,
    **values: Any,
) -> UUID:
    result = await session.execute(
        insert(application_templates_table)
        .values(name=name, status=status, **values)
        .returning(application_templates_table.c.id)
    )
    return result.scalar_one()
