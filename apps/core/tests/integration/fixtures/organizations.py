from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table


async def insert_organization(
    session: AsyncSession, name: str = "Uniwersytet Wrocławski", short_name: str = "UWr", **values: Any
) -> UUID:
    result = await session.execute(
        insert(organizations_table)
        .values(name=name, short_name=short_name, **values)
        .returning(organizations_table.c.id)
    )
    return result.scalar_one()


async def insert_suborganization(
    session: AsyncSession, organization_id: UUID, name: str = "Wydział Prawa", **values: Any
) -> UUID:
    result = await session.execute(
        insert(suborganizations_table)
        .values(organization_id=organization_id, name=name, **values)
        .returning(suborganizations_table.c.id)
    )
    return result.scalar_one()
