from dataclasses import asdict
from uuid import UUID

from sqlalchemy import Select, and_, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.regulations import RegulationRepresentation, RegulationSearchResult
from core_service.application.ports.relational import AsyncSession
from core_service.domain.entities.regulation import Regulation
from core_service.domain.exceptions.organizations import OrganizationNotFound
from core_service.domain.exceptions.regulations import RegulationNotFound
from core_service.domain.exceptions.users import UserNotFound
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.domain.value_objects.regulations import (
    RegulationOwner,
    RegulationRegistrationData,
    RegulationType,
)
from core_service.infrastructure.relational_db.schemas.regulations import regulations_table
from core_service.infrastructure.relational_db.session import sqla_session


def _filter_regulations(
    statement: Select,
    user_id: UUID | None,
    regulation_type: RegulationType | None,
    organization_filter: OrganizationFilter | None,
) -> Select:
    statement = statement.where(regulations_table.c.user_id == user_id)

    if regulation_type is not None:
        statement = statement.where(regulations_table.c.regulation_type == regulation_type)

    if organization_filter is not None:
        organization_condition = regulations_table.c.organization_id == organization_filter.organization_id
        if organization_filter.suborganization_id is not None:
            organization_condition = and_(
                organization_condition,
                or_(
                    regulations_table.c.suborganization_id == organization_filter.suborganization_id,
                    regulations_table.c.suborganization_id.is_(None),
                ),
            )
        statement = statement.where(or_(organization_condition, regulations_table.c.organization_id.is_(None)))

    return statement


class RegulationsManagerRepository:
    @staticmethod
    async def list_regulations(
        session: AsyncSession,
        user_id: UUID | None,
        regulation_type: RegulationType | None,
        organization_filter: OrganizationFilter | None,
    ) -> list[RegulationRepresentation]:
        session = sqla_session(session)
        statement = _filter_regulations(select(RegulationRepresentation), user_id, regulation_type, organization_filter)

        result = await session.scalars(statement)
        regulations_representation = list(result.all())

        return regulations_representation

    @staticmethod
    async def search_regulations(
        session: AsyncSession,
        user_id: UUID | None,
        regulation_type: RegulationType | None,
        organization_filter: OrganizationFilter | None,
        vector: list[float],
        threshold: float,
    ) -> list[RegulationSearchResult]:
        session = sqla_session(session)
        distance = regulations_table.c.description_vector.cosine_distance(vector)
        score = (1 - distance).label("score")

        statement = _filter_regulations(
            select(RegulationRepresentation, score), user_id, regulation_type, organization_filter
        )
        statement = statement.where(
            regulations_table.c.description_vector.is_not(None),
            1 - distance >= threshold,
        ).order_by(distance.asc())

        result = await session.execute(statement)

        return [RegulationSearchResult(regulation=regulation, score=score) for regulation, score in result.all()]

    @staticmethod
    async def register_regulation(
        session: AsyncSession, user_id: UUID | None, regulation_registration_data: RegulationRegistrationData
    ) -> UUID:
        session = sqla_session(session)
        statement = (
            insert(regulations_table)
            .values(user_id=user_id, **asdict(regulation_registration_data))
            .returning(regulations_table.c.id)
        )

        try:
            result = await session.execute(statement)
        except IntegrityError:
            if user_id is None:
                raise OrganizationNotFound
            raise UserNotFound

        regulation_id = result.scalar_one()
        return regulation_id

    @staticmethod
    async def unregister_regulation(session: AsyncSession, user_id: UUID | None, id_: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def get_for_update(session: AsyncSession, user_id: UUID | None, id_: UUID) -> Regulation | None:
        session = sqla_session(session)
        statement = (
            select(Regulation)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .with_for_update()
        )
        result = await session.scalars(statement)

        return result.one_or_none()

    @staticmethod
    async def save(session: AsyncSession, regulation: Regulation) -> RegulationRepresentation:
        session = sqla_session(session)
        session.add(regulation)
        await session.flush()

        statement = (
            select(RegulationRepresentation)
            .where(regulations_table.c.id == regulation.id)
            .execution_options(populate_existing=True)
        )
        result = await session.scalars(statement)

        return result.one()

    @staticmethod
    async def set_description_vector(
        session: AsyncSession, user_id: UUID | None, id_: UUID, vector: list[float] | None
    ) -> None:
        session = sqla_session(session)
        statement = (
            update(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .values(description_vector=vector)
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def get_regulation_representation(
        session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None:
        session = sqla_session(session)
        statement = select(RegulationRepresentation).where(
            regulations_table.c.user_id == user_id, regulations_table.c.id == id_
        )
        result = await session.scalars(statement)

        regulation_representation = result.one_or_none()

        return regulation_representation

    @staticmethod
    async def get_regulation_owner(session: AsyncSession, id_: UUID) -> RegulationOwner:
        session = sqla_session(session)
        statement = select(regulations_table.c.user_id).where(regulations_table.c.id == id_)
        result = await session.execute(statement)

        row = result.one_or_none()
        if row is None:
            raise RegulationNotFound

        return RegulationOwner(user_id=row.user_id)
