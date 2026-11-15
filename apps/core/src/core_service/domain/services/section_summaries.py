import re
from itertools import batched, groupby

from core_service.domain.services.breadcrumbs import split_unit_segment
from core_service.domain.value_objects.sections import SectionSummariesBatch, SectionSummary, SectionToSummarize

MAX_SUMMARY_BATCH_SECTIONS = 10

MAX_SUMMARY_SECTION_CHARS = 2000

REPEALED_UNIT_PATTERN = re.compile(r"^\(uchylon[aey]\)\.?$", re.IGNORECASE)

REPEALED_LABEL = "Uchylony"

REPEALED_SUMMARY = "Przepis został uchylony."


def is_repealed(section: SectionToSummarize) -> bool:
    return REPEALED_UNIT_PATTERN.match(section.text.strip()) is not None


def summarize_repealed_sections(sections: list[SectionToSummarize]) -> list[SectionSummary]:
    return [
        SectionSummary(section_id=section.id, label=REPEALED_LABEL, summary=REPEALED_SUMMARY)
        for section in sections
        if is_repealed(section)
    ]


def create_summary_batches(sections: list[SectionToSummarize]) -> list[SectionSummariesBatch]:
    sections_to_summarize = [section for section in sections if not is_repealed(section)]

    return [
        SectionSummariesBatch(chapter=chapter, sections=[_truncate(section) for section in batch])
        for chapter, chapter_sections in groupby(sections_to_summarize, key=_get_chapter)
        for batch in batched(chapter_sections, MAX_SUMMARY_BATCH_SECTIONS, strict=False)
    ]


def _get_chapter(section: SectionToSummarize) -> str | None:
    if section.header is None:
        return None
    chapter, _ = split_unit_segment(section.header)
    return chapter or None


def _truncate(section: SectionToSummarize) -> SectionToSummarize:
    return SectionToSummarize(id=section.id, header=section.header, text=section.text[:MAX_SUMMARY_SECTION_CHARS])
