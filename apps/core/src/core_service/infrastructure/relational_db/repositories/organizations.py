from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.organizations import (
    NewOrganization,
    NewSuborganization,
    OrganizationData,
    SuborganizationData,
)
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.organizations import OrganizationNotFound, SuborganizationNotFound
from core_service.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table
from core_service.infrastructure.relational_db.session import sqla_session


class SqlaOrganizationsRepository:
    @staticmethod
    async def list_all(session: AsyncSession) -> list[OrganizationData]:
        session = sqla_session(session)
        organizations_statement = select(
            organizations_table.c.id, organizations_table.c.name, organizations_table.c.short_name
        ).order_by(organizations_table.c.create_date)
        organizations_result = await session.execute(organizations_statement)

        suborganizations_statement = select(
            suborganizations_table.c.id, suborganizations_table.c.organization_id, suborganizations_table.c.name
        ).order_by(suborganizations_table.c.name)
        suborganizations_result = await session.execute(suborganizations_statement)

        suborganizations_by_organization = defaultdict(list)
        for suborganization in suborganizations_result:
            suborganizations_by_organization[suborganization.organization_id].append(
                SuborganizationData(id=suborganization.id, name=suborganization.name)
            )

        organizations = [
            OrganizationData(
                id=organization.id,
                name=organization.name,
                short_name=organization.short_name,
                suborganizations=suborganizations_by_organization[organization.id],
            )
            for organization in organizations_result
        ]
        return organizations

    @staticmethod
    async def add(session: AsyncSession, new_organization: NewOrganization) -> UUID:
        session = sqla_session(session)
        statement = (
            insert(organizations_table).values(**new_organization.model_dump()).returning(organizations_table.c.id)
        )
        result = await session.execute(statement)
        organization_id = result.scalar_one()
        return organization_id

    @staticmethod
    async def update(session: AsyncSession, organization_id: UUID, new_organization: NewOrganization) -> None:
        session = sqla_session(session)
        statement = (
            update(organizations_table)
            .where(organizations_table.c.id == organization_id)
            .values(**new_organization.model_dump())
            .returning(organizations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise OrganizationNotFound

    @staticmethod
    async def delete(session: AsyncSession, organization_id: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(organizations_table)
            .where(organizations_table.c.id == organization_id)
            .returning(organizations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise OrganizationNotFound


class SqlaSuborganizationsRepository:
    @staticmethod
    async def add(session: AsyncSession, organization_id: UUID, new_suborganization: NewSuborganization) -> UUID:
        session = sqla_session(session)
        statement = (
            insert(suborganizations_table)
            .values(organization_id=organization_id, **new_suborganization.model_dump())
            .returning(suborganizations_table.c.id)
        )
        try:
            result = await session.execute(statement)
        except IntegrityError:
            raise OrganizationNotFound
        suborganization_id = result.scalar_one()
        return suborganization_id

    @staticmethod
    async def update(
        session: AsyncSession, organization_id: UUID, suborganization_id: UUID, new_suborganization: NewSuborganization
    ) -> None:
        session = sqla_session(session)
        statement = (
            update(suborganizations_table)
            .where(
                suborganizations_table.c.id == suborganization_id,
                suborganizations_table.c.organization_id == organization_id,
            )
            .values(**new_suborganization.model_dump())
            .returning(suborganizations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise SuborganizationNotFound

    @staticmethod
    async def delete(session: AsyncSession, organization_id: UUID, suborganization_id: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(suborganizations_table)
            .where(
                suborganizations_table.c.id == suborganization_id,
                suborganizations_table.c.organization_id == organization_id,
            )
            .returning(suborganizations_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise SuborganizationNotFound
