from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.relational_db.schemas.regulations import regulations_table


async def insert_regulation(
    session: AsyncSession, user_id: UUID | None, presentation_name: str = "regulation.pdf", **values: Any
) -> UUID:
    result = await session.execute(
        insert(regulations_table)
        .values(user_id=user_id, presentation_name=presentation_name, **values)
        .returning(regulations_table.c.id)
    )
    return result.scalar_one()
