import re

from core_service.domain.services.legal_structure_parser import SUPERSCRIPT_DIGITS
from core_service.domain.value_objects.legal_units import BREADCRUMB_SEPARATOR

UNIT_CITATION_PATTERN = re.compile(rf"^(Art\.|§)\s*\d[\d\s]*[a-z]?[{SUPERSCRIPT_DIGITS}]*\s*\.?\s*")


def split_unit_segment(header: str) -> tuple[str, str | None]:
    segments = header.split(BREADCRUMB_SEPARATOR)
    unit_segment = segments.pop() if UNIT_CITATION_PATTERN.match(segments[-1]) else None
    return BREADCRUMB_SEPARATOR.join(segments), unit_segment
