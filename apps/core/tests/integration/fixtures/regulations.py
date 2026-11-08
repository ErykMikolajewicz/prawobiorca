from typing import Any
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.relational_db.schemas.regulations import regulations_table
from src.infrastructure.relational_db.schemas.sections import regulations_chunks_table, regulations_sections_table


async def insert_regulation(
    session: AsyncSession, user_id: UUID | None, presentation_name: str = "regulation.pdf", **values: Any
) -> UUID:
    result = await session.execute(
        insert(regulations_table)
        .values(user_id=user_id, presentation_name=presentation_name, **values)
        .returning(regulations_table.c.id)
    )
    return result.scalar_one()


async def insert_section(
    session: AsyncSession,
    regulation_id: UUID,
    text: str,
    chunk_vectors: list[list[float]],
    section_order: int = 0,
    user_id: UUID | None = None,
) -> UUID:
    result = await session.execute(
        insert(regulations_sections_table)
        .values(
            regulation_id=regulation_id,
            user_id=user_id,
            header="Art. 1",
            text=text,
            section_order=section_order,
            elements=[{"text": text, "subsection": None}],
        )
        .returning(regulations_sections_table.c.id)
    )
    section_id = result.scalar_one()

    chunks = [
        {
            "section_id": section_id,
            "chunk_index": chunk_index,
            "text": f"{text} chunk {chunk_index}",
            "vector": vector,
            "span_start_element": chunk_index,
            "span_end_element": chunk_index,
        }
        for chunk_index, vector in enumerate(chunk_vectors)
    ]
    await session.execute(insert(regulations_chunks_table).values(chunks))

    return section_id
