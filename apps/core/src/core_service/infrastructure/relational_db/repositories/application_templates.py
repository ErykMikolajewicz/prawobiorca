from uuid import UUID

from sqlalchemy import ColumnElement, Select, and_, delete, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.application.ports.relational import AsyncSession
from core_service.domain.entities.application_template import ApplicationTemplate
from core_service.domain.exceptions.application_templates import ApplicationTemplateNotFound
from core_service.domain.exceptions.organizations import OrganizationNotFound
from core_service.domain.value_objects.application_templates import ApplicationTemplateStatus
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.infrastructure.relational_db.integrity import get_violated_constraint
from core_service.infrastructure.relational_db.schemas.application_templates import (
    APPLICATION_TEMPLATES_ORGANIZATION_FOREIGN_KEY,
    APPLICATION_TEMPLATES_ORGANIZATION_SUBORGANIZATION_FOREIGN_KEY,
    APPLICATION_TEMPLATES_SUBORGANIZATION_FOREIGN_KEY,
    application_templates_table,
)
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
    async def get_for_update(session: AsyncSession, id_: UUID) -> ApplicationTemplate | None:
        session = sqla_session(session)
        statement = select(ApplicationTemplate).where(application_templates_table.c.id == id_).with_for_update()
        result = await session.scalars(statement)

        return result.one_or_none()

    @staticmethod
    async def save(session: AsyncSession, template: ApplicationTemplate) -> ApplicationTemplateRepresentation:
        session = sqla_session(session)
        session.add(template)
        try:
            await session.flush()
        except IntegrityError as e:
            if get_violated_constraint(e) in (
                APPLICATION_TEMPLATES_ORGANIZATION_FOREIGN_KEY,
                APPLICATION_TEMPLATES_SUBORGANIZATION_FOREIGN_KEY,
                APPLICATION_TEMPLATES_ORGANIZATION_SUBORGANIZATION_FOREIGN_KEY,
            ):
                raise OrganizationNotFound from e
            raise

        statement = (
            select(ApplicationTemplateRepresentation)
            .where(application_templates_table.c.id == template.id)
            .execution_options(populate_existing=True)
        )
        result = await session.scalars(statement)

        return result.one()

    @staticmethod
    async def set_description_vector(session: AsyncSession, id_: UUID, vector: list[float] | None) -> None:
        session = sqla_session(session)
        statement = (
            update(application_templates_table)
            .where(application_templates_table.c.id == id_)
            .values(description_vector=vector)
            .returning(application_templates_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ApplicationTemplateNotFound

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
