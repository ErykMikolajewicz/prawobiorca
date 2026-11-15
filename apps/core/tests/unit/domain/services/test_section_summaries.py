from uuid import UUID

from core_service.domain.services.section_summaries import (
    MAX_SUMMARY_BATCH_SECTIONS,
    MAX_SUMMARY_SECTION_CHARS,
    REPEALED_LABEL,
    REPEALED_SUMMARY,
    create_summary_batches,
    summarize_repealed_sections,
)
from core_service.domain.value_objects.sections import SectionSummary, SectionToSummarize


def create_section(index: int, header: str | None, text: str = "Treść przepisu.") -> SectionToSummarize:
    return SectionToSummarize(id=UUID(int=index), header=header, text=text)


def test_create_summary_batches_groups_sections_by_chapter():
    sections = [
        create_section(1, None, "Preambuła."),
        create_section(2, "Rozdział 1 Przepisy ogólne > Art. 1"),
        create_section(3, "Rozdział 1 Przepisy ogólne > Art. 2 Definicje"),
        create_section(4, "Rozdział 2 Studia > Art. 3"),
        create_section(5, "Art. 4"),
        create_section(6, "Załącznik 1 > Rozdział 1 Wzory"),
        create_section(7, "Załącznik 1 > Rozdział 1 Wzory"),
    ]

    batches = create_summary_batches(sections)

    assert [(batch.chapter, [section.id for section in batch.sections]) for batch in batches] == [
        (None, [UUID(int=1)]),
        ("Rozdział 1 Przepisy ogólne", [UUID(int=2), UUID(int=3)]),
        ("Rozdział 2 Studia", [UUID(int=4)]),
        (None, [UUID(int=5)]),
        ("Załącznik 1 > Rozdział 1 Wzory", [UUID(int=6), UUID(int=7)]),
    ]


def test_create_summary_batches_splits_long_chapter():
    sections = [create_section(index, f"Rozdział 1 > Art. {index}") for index in range(MAX_SUMMARY_BATCH_SECTIONS + 1)]

    batches = create_summary_batches(sections)

    assert [len(batch.sections) for batch in batches] == [MAX_SUMMARY_BATCH_SECTIONS, 1]
    assert {batch.chapter for batch in batches} == {"Rozdział 1"}


def test_create_summary_batches_truncates_long_sections():
    sections = [create_section(1, "Art. 1", "a" * (MAX_SUMMARY_SECTION_CHARS + 10))]

    (batch,) = create_summary_batches(sections)

    assert batch.sections[0].text == "a" * MAX_SUMMARY_SECTION_CHARS


def test_repealed_sections_are_summarized_without_llm():
    sections = [
        create_section(1, "Rozdział 1 > Art. 1", "(uchylony)"),
        create_section(2, "Rozdział 1 > Art. 2", " (uchylona). "),
        create_section(3, "Rozdział 1 > Art. 3", "1. (uchylony).\n2. Student może złożyć wniosek."),
    ]

    repealed_summaries = summarize_repealed_sections(sections)
    batches = create_summary_batches(sections)

    assert repealed_summaries == [
        SectionSummary(section_id=UUID(int=1), label=REPEALED_LABEL, summary=REPEALED_SUMMARY),
        SectionSummary(section_id=UUID(int=2), label=REPEALED_LABEL, summary=REPEALED_SUMMARY),
    ]
    assert [[section.id for section in batch.sections] for batch in batches] == [[UUID(int=3)]]
