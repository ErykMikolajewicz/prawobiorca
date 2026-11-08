import pytest
from sqlalchemy import select

from core_service.domain.value_objects.legal_units import LegalUnitElement
from core_service.domain.value_objects.sections import ChunkSpan, RegulationSection, SectionChunk, SectionsCollection
from core_service.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository
from core_service.infrastructure.relational_db.schemas.sections import (
    regulations_chunks_table,
    regulations_sections_table,
)
from core_service.shared.consts import VECTOR_LENGTH
from tests.consts import USER_ID
from tests.integration.fixtures.regulations import insert_regulation

VECTOR = [0.1] * VECTOR_LENGTH


def create_sections_collection() -> SectionsCollection:
    return SectionsCollection(
        [
            RegulationSection(
                header="Art. 1",
                text="Content 1 Content 2",
                chunks=[
                    SectionChunk(text="Content 1", chunk_index=0, span=ChunkSpan(0, 0), vector=VECTOR),
                    SectionChunk(text="Content 2", chunk_index=1, span=ChunkSpan(1, 1), vector=VECTOR),
                ],
                section_order=0,
                elements=[
                    LegalUnitElement(text="Content 1", subsection="1"),
                    LegalUnitElement(text="Content 2", subsection="2"),
                ],
            ),
            RegulationSection(
                header="Art. 2",
                text="Content 3",
                chunks=[SectionChunk(text="Content 3", chunk_index=0, vector=VECTOR)],
                section_order=1,
            ),
        ]
    )


@pytest.fixture
async def regulation_id(session_maker, user):
    async with session_maker.begin() as session:
        return await insert_regulation(session, USER_ID)


async def get_sections(session_maker, regulation_id):
    async with session_maker() as session:
        result = await session.execute(
            select(regulations_sections_table)
            .where(
                regulations_sections_table.c.regulation_id == regulation_id,
                regulations_sections_table.c.user_id == USER_ID,
            )
            .order_by(regulations_sections_table.c.section_order)
        )
    return result.all()


async def get_chunks(session_maker, regulation_id):
    async with session_maker() as session:
        result = await session.execute(
            select(regulations_chunks_table)
            .join(regulations_sections_table, regulations_chunks_table.c.section_id == regulations_sections_table.c.id)
            .where(regulations_sections_table.c.regulation_id == regulation_id)
            .order_by(regulations_sections_table.c.section_order, regulations_chunks_table.c.chunk_index)
        )
    return result.all()


async def test_add_sections_saves_sections(session_maker, regulation_id):
    async with session_maker.begin() as session:
        await RegulationsSectionsRepository.add_sections(session, USER_ID, regulation_id, create_sections_collection())

    sections = await get_sections(session_maker, regulation_id)

    assert [(section.header, section.text, section.section_order, section.elements) for section in sections] == [
        (
            "Art. 1",
            "Content 1 Content 2",
            0,
            [{"text": "Content 1", "subsection": "1"}, {"text": "Content 2", "subsection": "2"}],
        ),
        ("Art. 2", "Content 3", 1, []),
    ]


async def test_add_sections_saves_chunks_with_their_section(session_maker, regulation_id):
    sections = create_sections_collection()

    async with session_maker.begin() as session:
        await RegulationsSectionsRepository.add_sections(session, USER_ID, regulation_id, sections)

    chunks = await get_chunks(session_maker, regulation_id)

    first_section, second_section = sections
    assert [
        (chunk.section_id, chunk.chunk_index, chunk.text, chunk.span_start_element, chunk.span_end_element)
        for chunk in chunks
    ] == [
        (first_section.id, 0, "Content 1", 0, 0),
        (first_section.id, 1, "Content 2", 1, 1),
        (second_section.id, 0, "Content 3", None, None),
    ]
