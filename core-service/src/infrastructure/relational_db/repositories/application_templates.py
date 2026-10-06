from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.domain.exceptions.application_templates import ApplicationTemplateNotFound
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.infrastructure.relational_db.schemas.application_templates import application_templates_table


class ApplicationTemplatesRepository:
    @staticmethod
    async def list_templates(
        session: AsyncSession, status: ApplicationTemplateStatus | None = None
    ) -> list[ApplicationTemplateRepresentation]:
        statement = select(ApplicationTemplateRepresentation).order_by(application_templates_table.c.create_date)

        if status is not None:
            statement = statement.where(application_templates_table.c.status == status)

        result = await session.scalars(statement)
        templates = result.all()
        return templates

    @staticmethod
    async def get(session: AsyncSession, id_: UUID) -> ApplicationTemplateRepresentation | None:
        statement = select(ApplicationTemplateRepresentation).where(application_templates_table.c.id == id_)
        result = await session.scalars(statement)
        template = result.one_or_none()
        return template

    @staticmethod
    async def add(session: AsyncSession, name: str) -> UUID:
        statement = insert(application_templates_table).values(name=name).returning(application_templates_table.c.id)
        result = await session.execute(statement)
        template_id = result.scalar_one()
        return template_id

    async def set_fields(
        self, session: AsyncSession, id_: UUID, fields: list[ApplicationTemplateField]
    ) -> ApplicationTemplateRepresentation:
        return await self._update(session, id_, fields=fields)

    async def set_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateStatus
    ) -> ApplicationTemplateRepresentation:
        return await self._update(session, id_, status=status)

    async def update_details(
        self, session: AsyncSession, id_: UUID, details: ApplicationTemplateDetails
    ) -> ApplicationTemplateRepresentation:
        return await self._update(
            session, id_, name=details.name, instructions=details.instructions, fields=details.fields
        )

    @staticmethod
    async def delete(session: AsyncSession, id_: UUID) -> None:
        statement = (
            delete(application_templates_table)
            .where(application_templates_table.c.id == id_)
            .returning(application_templates_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ApplicationTemplateNotFound

    @staticmethod
    async def _update(session: AsyncSession, id_: UUID, **values) -> ApplicationTemplateRepresentation:
        statement = (
            update(ApplicationTemplateRepresentation)
            .where(application_templates_table.c.id == id_)
            .values(**values)
            .returning(ApplicationTemplateRepresentation)
        )
        result = await session.scalars(statement)

        template = result.one_or_none()
        if template is None:
            raise ApplicationTemplateNotFound

        return template
