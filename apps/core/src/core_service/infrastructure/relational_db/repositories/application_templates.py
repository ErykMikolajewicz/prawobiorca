from uuid import UUID

from sqlalchemy import ColumnElement, Select, and_, delete, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.application_templates import ApplicationTemplateNotFound
from core_service.domain.exceptions.organizations import OrganizationNotFound
from core_service.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.infrastructure.relational_db.schemas.application_templates import application_templates_table
from core_service.infrastructure.relational_db.session import sqla_session

TEMPLATE_NAME_SIMILARITY_THRESHOLD = 0.3

TEMPLATE_NAME_SCORE_WEIGHT = 0.6

HYBRID_TEMPLATE_SEARCH_LIMIT = 10


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


def _name_similarity(query: str) -> ColumnElement[float]:
    return func.word_similarity(func.unaccent(query), func.unaccent(application_templates_table.c.name))


class SqlaApplicationTemplatesRepository:
    @staticmethod
    async def list_templates(
        session: AsyncSession,
        status: ApplicationTemplateStatus | None = None,
        organization_filter: OrganizationFilter | None = None,
    ) -> list[ApplicationTemplateRepresentation]:
        session = sqla_session(session)
        statement = _filter_templates(
            select(ApplicationTemplateRepresentation).order_by(application_templates_table.c.create_date),
            status,
            organization_filter,
        )

        result = await session.scalars(statement)
        templates = list(result.all())
        return templates

    @staticmethod
    async def fuzzy_search_templates(
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        query: str,
    ) -> list[ApplicationTemplateRepresentation]:
        session = sqla_session(session)
        name_similarity = _name_similarity(query)

        statement = _filter_templates(select(ApplicationTemplateRepresentation), status, organization_filter)
        statement = statement.where(name_similarity >= TEMPLATE_NAME_SIMILARITY_THRESHOLD).order_by(
            name_similarity.desc(), application_templates_table.c.name
        )

        result = await session.scalars(statement)

        return list(result.all())

    @staticmethod
    async def hybrid_search_templates(
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        query: str,
        vector: list[float],
    ) -> list[ApplicationTemplateRepresentation]:
        session = sqla_session(session)
        distance = application_templates_table.c.description_vector.cosine_distance(vector)
        description_similarity = func.coalesce(1 - distance, 0)
        score = (
            TEMPLATE_NAME_SCORE_WEIGHT * _name_similarity(query)
            + (1 - TEMPLATE_NAME_SCORE_WEIGHT) * description_similarity
        )

        statement = _filter_templates(select(ApplicationTemplateRepresentation), status, organization_filter)
        statement = statement.order_by(score.desc(), application_templates_table.c.name).limit(
            HYBRID_TEMPLATE_SEARCH_LIMIT
        )

        result = await session.scalars(statement)

        return list(result.all())

    @staticmethod
    async def get(session: AsyncSession, id_: UUID) -> ApplicationTemplateRepresentation | None:
        session = sqla_session(session)
        statement = select(ApplicationTemplateRepresentation).where(application_templates_table.c.id == id_)
        result = await session.scalars(statement)
        template = result.one_or_none()
        return template

    @staticmethod
    async def add(session: AsyncSession, name: str, instructions: str) -> UUID:
        session = sqla_session(session)
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
        session = sqla_session(session)
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
        session = sqla_session(session)
        return await self._update(session, id_, status=status)

    async def set_description_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateDescriptionStatus
    ) -> ApplicationTemplateRepresentation:
        session = sqla_session(session)
        return await self._update(session, id_, description_status=status)

    async def set_generated_description(
        self, session: AsyncSession, id_: UUID, description: str, vector: list[float]
    ) -> ApplicationTemplateRepresentation:
        session = sqla_session(session)
        return await self._update(
            session,
            id_,
            description=description,
            description_vector=vector,
            description_status=ApplicationTemplateDescriptionStatus.GENERATED,
        )

    async def set_description_vector(
        self, session: AsyncSession, id_: UUID, vector: list[float] | None
    ) -> ApplicationTemplateRepresentation:
        session = sqla_session(session)
        return await self._update(session, id_, description_vector=vector)

    async def update_details(
        self, session: AsyncSession, id_: UUID, details: ApplicationTemplateDetails
    ) -> ApplicationTemplateRepresentation:
        session = sqla_session(session)
        try:
            return await self._update(
                session,
                id_,
                name=details.name,
                instructions=details.instructions,
                fields=details.fields,
                description=details.description,
                organization_id=details.organization_id,
                suborganization_id=details.suborganization_id,
            )
        except IntegrityError:
            raise OrganizationNotFound

    @staticmethod
    async def delete(session: AsyncSession, id_: UUID) -> None:
        session = sqla_session(session)
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
        session = sqla_session(session)
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
