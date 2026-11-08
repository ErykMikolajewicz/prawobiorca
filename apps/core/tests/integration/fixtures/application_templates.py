from io import BytesIO
from typing import Any
from uuid import UUID

from docx import Document
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.domain.value_objects.application_templates import ApplicationTemplateStatus
from core_service.infrastructure.relational_db.schemas.application_templates import application_templates_table


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


def create_docx_template() -> bytes:
    document = Document()
    document.add_paragraph("{{ student_id }}, {{ department }}, {{ current_date }}")
    document.add_paragraph("{%p for paragraph in paragraphs %}")
    document.add_paragraph("{{ paragraph }}")
    document.add_paragraph("{%p endfor %}")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
