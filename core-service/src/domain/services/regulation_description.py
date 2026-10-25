from src.domain.value_objects.legal_units import BREADCRUMB_SEPARATOR
from src.domain.value_objects.regulations import RegulationDescriptionSource, SectionContent

MAX_DESCRIPTION_HEADINGS = 100

MAX_DESCRIPTION_BEGINNING_CHARS = 4000


def create_description_source(presentation_name: str, sections: list[SectionContent]) -> RegulationDescriptionSource:
    headings = []
    for section in sections:
        if section.header is None:
            continue
        heading = BREADCRUMB_SEPARATOR.join(section.header.split(BREADCRUMB_SEPARATOR)[:-1])
        if heading and heading not in headings:
            headings.append(heading)

    beginning = "\n".join(section.text for section in sections)[:MAX_DESCRIPTION_BEGINNING_CHARS]

    return RegulationDescriptionSource(
        presentation_name=presentation_name,
        headings=headings[:MAX_DESCRIPTION_HEADINGS],
        beginning=beginning,
    )
