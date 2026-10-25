import re

from src.domain.value_objects.legal_units import BREADCRUMB_SEPARATOR
from src.domain.value_objects.regulations import RegulationDescriptionSource, RegulationHeading, SectionContent

MAX_DESCRIPTION_HEADINGS = 300

MAX_DESCRIPTION_BEGINNING_CHARS = 4000

UNIT_CITATION_PATTERN = re.compile(r"^(Art\.|§)\s*\d[\d\s]*[a-z]?\s*\.?\s*")


def create_description_source(presentation_name: str, sections: list[SectionContent]) -> RegulationDescriptionSource:
    headings = []
    last_chapter = None
    for section in sections:
        if section.header is None:
            continue
        segments = section.header.split(BREADCRUMB_SEPARATOR)
        unit_segment = segments.pop() if UNIT_CITATION_PATTERN.match(segments[-1]) else None

        chapter = BREADCRUMB_SEPARATOR.join(segments)
        if chapter and chapter != last_chapter:
            headings.append(RegulationHeading(text=chapter, level=0))
            last_chapter = chapter

        unit_title = UNIT_CITATION_PATTERN.sub("", unit_segment).strip() if unit_segment else ""
        if unit_title:
            headings.append(RegulationHeading(text=unit_title, level=1 if chapter else 0))

    beginning = "\n".join(section.text for section in sections)[:MAX_DESCRIPTION_BEGINNING_CHARS]

    return RegulationDescriptionSource(
        presentation_name=presentation_name,
        headings=headings[:MAX_DESCRIPTION_HEADINGS],
        beginning=beginning,
    )
