from unittest.mock import AsyncMock
from uuid import uuid4

from src.domain.value_objects.legal_units import LegalUnitElement
from src.domain.value_objects.sections import RegulationSection, SectionChunk, SectionsCollection
from src.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository


def create_sections_collection() -> SectionsCollection:
    return SectionsCollection(
        [
            RegulationSection(
                header="Art. 1",
                text="Content 1 Content 2",
                chunks=[
                    SectionChunk(text="Content 1", embed_title="Art. 1 ust. 1", chunk_index=0, vector=[0.1]),
                    SectionChunk(text="Content 2", embed_title="Art. 1 ust. 2", chunk_index=1, vector=[0.2]),
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
                chunks=[SectionChunk(text="Content 3", embed_title="Art. 2", chunk_index=0, vector=[0.3])],
                section_order=1,
            ),
        ]
    )


SECTIONS_INSERT = 0
CHUNKS_INSERT = 1


def get_inserted_values(session: AsyncMock, insert_index: int, column: str) -> list:
    statement = session.execute.await_args_list[insert_index].args[0]
    parameters = statement.compile().params
    return [value for key, value in parameters.items() if key.startswith(column)]


async def test_add_sections_saves_sections_order():
    session = AsyncMock()

    await RegulationsSectionsRepository.add_sections(session, uuid4(), uuid4(), create_sections_collection())

    assert sorted(get_inserted_values(session, SECTIONS_INSERT, "section_order")) == [0, 1]


async def test_add_sections_saves_chunks_with_their_section():
    session = AsyncMock()
    sections = create_sections_collection()

    await RegulationsSectionsRepository.add_sections(session, uuid4(), uuid4(), sections)

    first_section, second_section = sections
    assert get_inserted_values(session, CHUNKS_INSERT, "section_id") == [
        first_section.id,
        first_section.id,
        second_section.id,
    ]
    assert get_inserted_values(session, CHUNKS_INSERT, "chunk_index") == [0, 1, 0]


async def test_add_sections_saves_elements_as_dicts():
    session = AsyncMock()

    await RegulationsSectionsRepository.add_sections(session, uuid4(), uuid4(), create_sections_collection())

    assert get_inserted_values(session, SECTIONS_INSERT, "elements") == [
        [{"text": "Content 1", "subsection": "1"}, {"text": "Content 2", "subsection": "2"}],
        [],
    ]
