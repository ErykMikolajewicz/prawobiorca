from dataclasses import dataclass, field
from enum import StrEnum

BREADCRUMB_SEPARATOR = " > "


class UsefulLabels(StrEnum):
    SECTION_HEADER = "section_header"
    LIST_ITEM = "list_item"
    TEXT = "text"


@dataclass
class RegulationElement:
    label: str
    text: str


class UnitType(StrEnum):
    ARTICLE = "ARTICLE"
    PARAGRAPH = "PARAGRAPH"
    UNNUMBERED = "UNNUMBERED"


UNIT_TYPE_PREFIXES = {
    UnitType.ARTICLE: "Art.",
    UnitType.PARAGRAPH: "§",
}


@dataclass
class LegalUnitElement:
    text: str
    subsection: str | None = None


@dataclass
class LegalUnit:
    unit_type: UnitType
    number: str | None = None
    title: str | None = None
    path: list[str] = field(default_factory=list)
    elements: list[LegalUnitElement] = field(default_factory=list)

    @property
    def citation(self) -> str | None:
        if self.number is None:
            return None
        return f"{UNIT_TYPE_PREFIXES[self.unit_type]} {self.number}"

    @property
    def breadcrumb_segments(self) -> list[str]:
        segments = list(self.path)

        unit_segment_parts = [part for part in (self.citation, self.title) if part]
        if unit_segment_parts:
            segments.append(" ".join(unit_segment_parts))

        return segments

    @property
    def breadcrumb(self) -> str | None:
        segments = self.breadcrumb_segments
        if not segments:
            return None
        return BREADCRUMB_SEPARATOR.join(segments)
