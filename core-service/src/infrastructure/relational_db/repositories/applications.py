from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.applications import ApplicationRepresentation
from src.domain.exceptions.applications import ApplicationNotFound
from src.domain.exceptions.cases import CaseNotFound
from src.domain.value_objects.applications import ApplicationGenerationStatus, ApplicationType
from src.infrastructure.relational_db.schemas.applications import applications_table


class ApplicationsRepository:
    @staticmethod
    async def list_by_case_id(session: AsyncSession, user_id: UUID, case_id: UUID) -> list[ApplicationRepresentation]:
        statement = (
            select(ApplicationRepresentation)
            .where(applications_table.c.case_id == case_id, applications_table.c.user_id == user_id)
            .order_by(applications_table.c.create_date.desc())
        )
        result = await session.scalars(statement)
        applications = result.all()
        return applications

    @staticmethod
    async def list_ids_by_case_id(session: AsyncSession, user_id: UUID, case_id: UUID) -> list[UUID]:
        statement = select(applications_table.c.id).where(
            applications_table.c.case_id == case_id, applications_table.c.user_id == user_id
        )
        result = await session.scalars(statement)
        application_ids = result.all()
        return application_ids

    @staticmethod
    async def get(session: AsyncSession, user_id: UUID, application_id: UUID) -> ApplicationRepresentation | None:
        statement = select(ApplicationRepresentation).where(
            applications_table.c.id == application_id, applications_table.c.user_id == user_id
        )
        result = await session.scalars(statement)
        application = result.one_or_none()
        return application

    @staticmethod
    async def add(session: AsyncSession, user_id: UUID, case_id: UUID, application_type: ApplicationType) -> UUID:
        statement = (
            insert(applications_table)
            .values(case_id=case_id, user_id=user_id, application_type=application_type)
            .returning(applications_table.c.id)
        )
        try:
            result = await session.execute(statement)
        except IntegrityError:
            raise CaseNotFound
        application_id = result.scalar_one()
        return application_id

    @staticmethod
    async def set_generation_status(
        session: AsyncSession, user_id: UUID, application_id: UUID, status: ApplicationGenerationStatus
    ) -> None:
        statement = (
            update(applications_table)
            .where(applications_table.c.id == application_id, applications_table.c.user_id == user_id)
            .values(generation_status=status)
            .returning(applications_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ApplicationNotFound

    @staticmethod
    async def set_name(session: AsyncSession, user_id: UUID, application_id: UUID, name: str) -> None:
        statement = (
            update(applications_table)
            .where(applications_table.c.id == application_id, applications_table.c.user_id == user_id)
            .values(name=name)
            .returning(applications_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ApplicationNotFound

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, application_id: UUID) -> None:
        statement = (
            delete(applications_table)
            .where(applications_table.c.id == application_id, applications_table.c.user_id == user_id)
            .returning(applications_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ApplicationNotFound
