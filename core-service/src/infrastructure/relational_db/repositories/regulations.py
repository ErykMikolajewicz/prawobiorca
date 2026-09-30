from dataclasses import asdict
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.regulations import RegulationRepresentation
from src.domain.exceptions.regulations import RegulationNotFound
from src.domain.exceptions.users import UserNotFound
from src.domain.value_objects.regulations import (
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationType,
)
from src.infrastructure.relational_db.schemas.regulations import regulations_table


class RegulationsManagerRepository:
    @staticmethod
    async def list_regulations(
        session: AsyncSession, user_id: UUID | None, regulation_type: RegulationType | None
    ) -> list[RegulationRepresentation]:
        statement = select(RegulationRepresentation).where(regulations_table.c.user_id == user_id)

        if regulation_type is not None:
            statement = statement.where(regulations_table.c.regulation_type == regulation_type)

        result = await session.scalars(statement)
        regulations_representation = result.all()

        return regulations_representation

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
    async def get_regulation_representation(
        session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None:
        statement = select(RegulationRepresentation).where(
            regulations_table.c.user_id == user_id, regulations_table.c.id == id_
        )
        result = await session.scalars(statement)

        regulation_representation = result.one_or_none()

        return regulation_representation
