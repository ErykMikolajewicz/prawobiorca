from uuid import UUID

from sqlalchemy import Select, and_, case, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.domain.exceptions.application_templates import ApplicationTemplateNotFound
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.domain.value_objects.organizations import OrganizationFilter
from src.infrastructure.relational_db.schemas.application_templates import application_templates_table


def _filter_templates(
    statement: Select, status: ApplicationTemplateStatus | None, organization_filter: OrganizationFilter | None
) -> Select:
    if status is not None:
        statement = statement.where(application_templates_table.c.status == status)

    if organization_filter is not None:
        organization_condition = application_templates_table.c.organization_id == organization_filter.organization_id
        if organization_filter.suborganization_id is not None:
            organization_condition = and_(
                organization_condition,
                or_(
                    application_templates_table.c.suborganization_id == organization_filter.suborganization_id,
                    application_templates_table.c.suborganization_id.is_(None),
                ),
            )
        statement = statement.where(
            or_(organization_condition, application_templates_table.c.organization_id.is_(None))
        )

    return statement


class ApplicationTemplatesRepository:
    @staticmethod
    async def list_templates(
        session: AsyncSession,
        status: ApplicationTemplateStatus | None = None,
        organization_filter: OrganizationFilter | None = None,
    ) -> list[ApplicationTemplateRepresentation]:
        statement = _filter_templates(
            select(ApplicationTemplateRepresentation).order_by(application_templates_table.c.create_date),
            status,
            organization_filter,
        )

        result = await session.scalars(statement)
        templates = result.all()
        return templates

    @staticmethod
    async def search_templates(
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        vector: list[float],
        threshold: float,
    ) -> list[tuple[ApplicationTemplateRepresentation, float]]:
        distance = application_templates_table.c.description_vector.cosine_distance(vector)
        score = (1 - distance).label("score")

        statement = _filter_templates(select(ApplicationTemplateRepresentation, score), status, organization_filter)
        statement = statement.where(
            application_templates_table.c.description_vector.is_not(None),
            1 - distance >= threshold,
        ).order_by(distance.asc())

        result = await session.execute(statement)

        return [(template, score) for template, score in result.all()]

    @staticmethod
    async def get(session: AsyncSession, id_: UUID) -> ApplicationTemplateRepresentation | None:
        statement = select(ApplicationTemplateRepresentation).where(application_templates_table.c.id == id_)
        result = await session.scalars(statement)
        template = result.one_or_none()
        return template

    @staticmethod
    async def add(session: AsyncSession, name: str, instructions: str) -> UUID:
        statement = (
            insert(application_templates_table)
            .values(name=name, instructions=instructions)
            .returning(application_templates_table.c.id)
        )
        result = await session.execute(statement)
        template_id = result.scalar_one()
        return template_id

    @staticmethod
    async def confirm_upload(
        session: AsyncSession, id_: UUID, fields: list[ApplicationTemplateField]
    ) -> ApplicationTemplateRepresentation | None:
        statement = (
            update(ApplicationTemplateRepresentation)
            .where(
                application_templates_table.c.id == id_,
                application_templates_table.c.status == ApplicationTemplateStatus.NOT_UPLOADED,
            )
            .values(fields=fields, status=ApplicationTemplateStatus.DRAFT)
            .returning(ApplicationTemplateRepresentation)
        )
        result = await session.scalars(statement)
        template = result.one_or_none()
        return template

    async def set_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateStatus
    ) -> ApplicationTemplateRepresentation:
        return await self._update(session, id_, status=status)

    async def set_description_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateDescriptionStatus
    ) -> ApplicationTemplateRepresentation:
        return await self._update(session, id_, description_status=status)

    async def set_generated_description(
        self, session: AsyncSession, id_: UUID, description: str, vector: list[float]
    ) -> ApplicationTemplateRepresentation:
        return await self._update(
            session,
            id_,
            description=description,
            description_vector=vector,
            description_status=ApplicationTemplateDescriptionStatus.GENERATED,
        )

    async def update_details(
        self, session: AsyncSession, id_: UUID, details: ApplicationTemplateDetails
    ) -> ApplicationTemplateRepresentation:
        description_vector = case(
            (
                application_templates_table.c.description.is_not_distinct_from(details.description),
                application_templates_table.c.description_vector,
            ),
            else_=None,
        )
        try:
            return await self._update(
                session,
                id_,
                name=details.name,
                instructions=details.instructions,
                fields=details.fields,
                description=details.description,
                description_vector=description_vector,
                organization_id=details.organization_id,
                suborganization_id=details.suborganization_id,
            )
        except IntegrityError:
            raise OrganizationNotFound

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
            .values({application_templates_table.c[key]: value for key, value in values.items()})
            .returning(ApplicationTemplateRepresentation)
        )
        result = await session.scalars(statement)

        template = result.one_or_none()
        if template is None:
            raise ApplicationTemplateNotFound

        return template
