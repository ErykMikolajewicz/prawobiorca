from dataclasses import asdict
from uuid import UUID

from sqlalchemy import Select, and_, case, delete, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.regulations import RegulationRepresentation, RegulationSearchResult
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.exceptions.regulations import RegulationNotFound
from src.domain.exceptions.users import UserNotFound
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationDetails,
    RegulationOwner,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationType,
)
from src.infrastructure.relational_db.schemas.regulations import regulations_table


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
        statement = _filter_regulations(select(RegulationRepresentation), user_id, regulation_type, organization_filter)

        result = await session.scalars(statement)
        regulations_representation = result.all()

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
        statement = (
            delete(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def set_preparation_status(
        session: AsyncSession, user_id: UUID | None, id_: UUID, status: RegulationPreparationStatus
    ) -> None:
        statement = (
            update(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .values(preparation_status=status)
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def set_description_status(
        session: AsyncSession, user_id: UUID | None, id_: UUID, status: RegulationDescriptionStatus
    ) -> None:
        statement = (
            update(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .values(description_status=status)
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def set_generated_description(
        session: AsyncSession, user_id: UUID | None, id_: UUID, description: str, vector: list[float]
    ) -> None:
        statement = (
            update(regulations_table)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .values(
                description=description,
                description_vector=vector,
                description_status=RegulationDescriptionStatus.GENERATED,
            )
            .returning(regulations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise RegulationNotFound

    @staticmethod
    async def update_regulation_details(
        session: AsyncSession, user_id: UUID | None, id_: UUID, regulation_details: RegulationDetails
    ) -> RegulationRepresentation:
        description_vector = case(
            (
                regulations_table.c.description.is_not_distinct_from(regulation_details.description),
                regulations_table.c.description_vector,
            ),
            else_=None,
        )
        statement = (
            update(RegulationRepresentation)
            .where(regulations_table.c.user_id == user_id, regulations_table.c.id == id_)
            .values(**asdict(regulation_details), description_vector=description_vector)
            .returning(RegulationRepresentation)
        )
        result = await session.scalars(statement)

        regulation_representation = result.one_or_none()
        if regulation_representation is None:
            raise RegulationNotFound

        return regulation_representation

    @staticmethod
    async def get_regulation_representation(
        session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None:
        statement = select(RegulationRepresentation).where(
            regulations_table.c.user_id == user_id, regulations_table.c.id == id_
        )
        result = await session.scalars(statement)

        regulation_representation = result.one_or_none()

        return regulation_representation

    @staticmethod
    async def get_regulation_owner(session: AsyncSession, id_: UUID) -> RegulationOwner:
        statement = select(regulations_table.c.user_id).where(regulations_table.c.id == id_)
        result = await session.execute(statement)

        row = result.one_or_none()
        if row is None:
            raise RegulationNotFound

        return RegulationOwner(user_id=row.user_id)
