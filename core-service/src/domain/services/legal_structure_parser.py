import re
from collections.abc import Iterable

from src.domain.value_objects.legal_units import (
    LegalUnit,
    LegalUnitElement,
    RegulationElement,
    UnitType,
    UsefulLabels,
)

NOISE_LABELS = frozenset({"page_header", "page_footer", "footnote"})
PAGE_BREAK_LABELS = frozenset({"page_header", "page_footer"})

DIVISION_PATTERN = re.compile(
    r"^(?i:(ZAŁĄCZNIK|CZĘŚĆ|KSIĘGA|TYTUŁ|DZIAŁ|ROZDZIAŁ|ODDZIAŁ))\s+(?i:nr\s*)?"
    r"([IVXLCDM]+[A-Z]?\b|\d+[A-Za-z]*\b|[IVXLCDM]+?(?=[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]))"
)
ARTICLE_PATTERN = re.compile(r"^Art\.\s*(\d+[a-z]*)\s*\.")
PARAGRAPH_PATTERN = re.compile(r"^§\s*(\d+[a-z]*)\s*\.?")
ARTICLE_HEADER_PATTERN = re.compile(r"\bArt\.\s*(\d+[a-z]*)\s*\.?")
PARAGRAPH_HEADER_PATTERN = re.compile(r"§\s*(\d+[a-z]*)\s*\.?")
SUBSECTION_PATTERN = re.compile(r"^(\d+[a-z]*)\.\s")
POINT_PATTERN = re.compile(r"^<?\d+[a-z]*\)\s")
LETTER_PATTERN = re.compile(r"^<?[a-z]\)\s")
MARKED_SUBSECTION_PATTERN = re.compile(r"^[<\[]\d+[a-z]*\.\s")
DASH_PATTERN = re.compile(r"^[-–]")
ATTACHMENT_MARKER_PATTERN = re.compile(r"^(Załącznik\s+nr\s*\d+[a-z]*)(?:\s\d+\))?(?:\s\1(?:\s\d+\))?)*$")
GLUED_ARTICLE_PATTERN = re.compile(r"(?<=[.;:])\s+(?=Art\.\s*\d+[a-z]*\s*\.)")

WHITESPACE_PATTERN = re.compile(r"[\s﻿]+")
SPACE_BEFORE_PUNCTUATION_PATTERN = re.compile(r"\s+([.,;:)])")
SPACE_AFTER_OPENING_BRACKET_PATTERN = re.compile(r"\(\s+")
FOOTNOTE_MARKER_AFTER_NUMBER_PATTERN = re.compile(r"^(§\s*\d+[a-z]*\.(?:\s\d+[a-z]*\.)?|\d+[a-z]*\.)\s\d+\)\s")
TRAILING_FOOTNOTE_MARKER_PATTERN = re.compile(r"(?<=[.,;:])\s\d+\)$")
HEADER_FOOTNOTE_MARKER_PATTERN = re.compile(r"(?<=\w)\s\d+\)$")
SPLIT_PARAGRAPH_NUMBER_PATTERN = re.compile(r"^(§\s*\d+)\s(\d+[a-z]*\.)")
HYPHENATION_PATTERN = re.compile(r"(?<=\w) -(?=\w)")
SPACED_DASH = " - "

DIVISION_RANKS = {
    "ZAŁĄCZNIK": 0,
    "CZĘŚĆ": 1,
    "KSIĘGA": 2,
    "TYTUŁ": 3,
    "DZIAŁ": 4,
    "ROZDZIAŁ": 5,
    "ODDZIAŁ": 6,
}

GENERIC_HEADER_RANK = max(DIVISION_RANKS.values()) + 1

UNIT_PATTERNS = {
    UnitType.ARTICLE: ARTICLE_PATTERN,
    UnitType.PARAGRAPH: PARAGRAPH_PATTERN,
}

UNIT_HEADER_PATTERNS = {
    UnitType.ARTICLE: ARTICLE_HEADER_PATTERN,
    UnitType.PARAGRAPH: PARAGRAPH_HEADER_PATTERN,
}

CONTENT_PATTERNS = (PARAGRAPH_PATTERN, SUBSECTION_PATTERN, MARKED_SUBSECTION_PATTERN, POINT_PATTERN, LETTER_PATTERN)


class _BreadcrumbTracker:
    """Owns the division-path stack together with the one bit of lookahead state needed to tell,
    one header later, whether a header was a breadcrumb segment or actually a unit's title.
    """

    def __init__(self) -> None:
        self._stack: list[tuple[int, str]] = []
        self._last_was_bare_division = False
        self._pending_generic_title: str | None = None
        self._generic_titles_content = False

    def path(self) -> list[str]:
        return [division for _, division in self._stack]

    def push_header(self, text: str) -> bool:
        """Returns whether the header opened a new part of the document."""
        division_match = DIVISION_PATTERN.match(text)

        if division_match is None and self._last_was_bare_division:
            rank, division = self._stack[-1]
            self._stack[-1] = (rank, f"{division} {text}")
            self._last_was_bare_division = False
            self._pending_generic_title = None
            self._generic_titles_content = False
            return True

        is_generic = division_match is None
        rank = GENERIC_HEADER_RANK if is_generic else DIVISION_RANKS[division_match.group(1).upper()]

        if not is_generic and self._is_repeated_division(rank, text):
            return False

        while self._stack and self._stack[-1][0] >= rank:
            self._stack.pop()
        self._stack.append((rank, text))

        self._last_was_bare_division = not is_generic
        self._pending_generic_title = text if is_generic else None
        self._generic_titles_content = False
        return True

    def _is_repeated_division(self, rank: int, text: str) -> bool:
        """Some documents repeat a division marker on every page, e.g. `Załącznik nr 1`."""
        return any(
            division_rank == rank and (division == text or division.startswith(f"{text} "))
            for division_rank, division in self._stack
        )

    def resolve_unit_title(self, existing_title: str | None) -> str | None:
        """If the unit still has no title, the last generic header was actually its title,
        not a breadcrumb segment, so it is popped back off the path. A generic header that already
        titled unnumbered content ends with that content, so it is popped as well.
        """
        resolved = existing_title
        if resolved is None and self._pending_generic_title is not None:
            resolved = self._pending_generic_title
            self._stack.pop()
        elif self._generic_titles_content:
            self._stack.pop()

        self._last_was_bare_division = False
        self._pending_generic_title = None
        self._generic_titles_content = False
        return resolved

    def mark_content(self) -> None:
        if self._pending_generic_title is not None:
            self._generic_titles_content = True
        self._last_was_bare_division = False
        self._pending_generic_title = None


class LegalStructureParser:
    """Rebuilds the editorial structure of a Polish legal act from flat, layout-based extraction output.

    Layout labels alone are not enough: in the `Dziennik Ustaw` format an article opens the same paragraph
    as its first subsection, so it never gets a `section_header` label. The structure is therefore recovered
    from the numbering scheme itself (`Art.`, `§`, `Rozdział`, ...).
    """

    def parse(self, elements: Iterable[RegulationElement]) -> list[LegalUnit]:
        prepared_elements = self._prepare_elements(elements)
        unit_type = self._detect_unit_type(prepared_elements)

        return self._build_units(prepared_elements, unit_type)

    def _prepare_elements(self, elements: Iterable[RegulationElement]) -> list[RegulationElement]:
        prepared_elements = []
        for page in self._split_into_pages(elements):
            page_elements = [
                RegulationElement(label=element.label, text=self._normalize_text(element.text))
                for element in page
                if element.label not in NOISE_LABELS
            ]
            joins_hyphenated_words = any(SPACED_DASH in element.text for element in page_elements)

            for element in page_elements:
                text = HYPHENATION_PATTERN.sub("", element.text) if joins_hyphenated_words else element.text
                if not text:
                    continue

                if element.label == UsefulLabels.SECTION_HEADER:
                    text = HEADER_FOOTNOTE_MARKER_PATTERN.sub("", text)
                    label = UsefulLabels.TEXT if self._opens_unit_content(text) else element.label
                    prepared_elements.append(RegulationElement(label=label, text=text))
                    continue

                if (attachment_match := ATTACHMENT_MARKER_PATTERN.match(text)) is not None:
                    prepared_elements.append(
                        RegulationElement(label=UsefulLabels.SECTION_HEADER, text=attachment_match.group(1))
                    )
                    continue

                for fragment in GLUED_ARTICLE_PATTERN.split(text):
                    prepared_elements.append(RegulationElement(label=element.label, text=fragment))

        return prepared_elements

    @staticmethod
    def _opens_unit_content(text: str) -> bool:
        """Docling labels some articles as headers when they open with their first subsection
        (`Art. 19. 1. W skład rady uczelni wchodzi:`). Articles have no titles, and a paragraph
        title never starts with a subsection, so both are content, not headers.
        """
        if ARTICLE_PATTERN.match(text) is not None:
            return True

        paragraph_match = PARAGRAPH_PATTERN.match(text)
        return paragraph_match is not None and any(
            pattern.match(text[paragraph_match.end() :].strip()) is not None
            for pattern in (SUBSECTION_PATTERN, MARKED_SUBSECTION_PATTERN)
        )

    @staticmethod
    def _split_into_pages(elements: Iterable[RegulationElement]) -> list[list[RegulationElement]]:
        """Hyphenated words and dashes are rendered alike (`złoże -nia`, `braku -numer`), but a page that also
        contains a spaced dash (` - `) renders its dashes that way, so its ` -` can only be a hyphenation.
        """
        pages: list[list[RegulationElement]] = [[]]
        for element in elements:
            if element.label in PAGE_BREAK_LABELS:
                if pages[-1]:
                    pages.append([])
                continue
            pages[-1].append(element)

        return pages

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized_text = WHITESPACE_PATTERN.sub(" ", text).strip()
        normalized_text = SPACE_BEFORE_PUNCTUATION_PATTERN.sub(r"\1", normalized_text)
        normalized_text = SPACE_AFTER_OPENING_BRACKET_PATTERN.sub("(", normalized_text)
        normalized_text = FOOTNOTE_MARKER_AFTER_NUMBER_PATTERN.sub(r"\1 ", normalized_text)
        normalized_text = TRAILING_FOOTNOTE_MARKER_PATTERN.sub("", normalized_text)
        normalized_text = SPLIT_PARAGRAPH_NUMBER_PATTERN.sub(r"\1\2", normalized_text)
        return normalized_text

    @staticmethod
    def _detect_unit_type(elements: Iterable[RegulationElement]) -> UnitType:
        """Acts numbered with articles keep `§` as a subunit (as codes do), so articles always win."""
        for element in elements:
            if ARTICLE_PATTERN.match(element.text):
                return UnitType.ARTICLE
        return UnitType.PARAGRAPH

    def _build_units(self, elements: Iterable[RegulationElement], unit_type: UnitType) -> list[LegalUnit]:
        units = []
        breadcrumbs = _BreadcrumbTracker()
        current_unit = None

        for element in elements:
            is_header = element.label == UsefulLabels.SECTION_HEADER

            if (unit_match := self._match_unit(element, unit_type)) is not None:
                current_unit = LegalUnit(unit_type=unit_type, number=unit_match.group(1))
                units.append(current_unit)

                text_before_number = element.text[: unit_match.start()].strip()
                text_after_number = element.text[unit_match.end() :].strip()

                if is_header:
                    current_unit.title = f"{text_before_number} {text_after_number}".strip() or None
                elif text_after_number:
                    self._append_element(current_unit, text_after_number)

                current_unit.title = breadcrumbs.resolve_unit_title(current_unit.title)
                current_unit.path = breadcrumbs.path()
                continue

            if is_header and not self._is_unit_like(element.text):
                if breadcrumbs.push_header(element.text):
                    current_unit = None
                continue

            if current_unit is None:
                current_unit = LegalUnit(unit_type=UnitType.UNNUMBERED, path=breadcrumbs.path())
                units.append(current_unit)

            self._append_element(current_unit, element.text)
            breadcrumbs.mark_content()

        return [unit for unit in units if unit.elements or unit.title]

    @staticmethod
    def _match_unit(element: RegulationElement, unit_type: UnitType) -> re.Match | None:
        """Headers may carry the unit marker after their title, content elements must open with it."""
        if element.label == UsefulLabels.SECTION_HEADER:
            return UNIT_HEADER_PATTERNS[unit_type].search(element.text)

        return UNIT_PATTERNS[unit_type].match(element.text)

    @staticmethod
    def _is_unit_like(text: str) -> bool:
        """Docling mislabels numbered provisions and continuations after a dash as headers.
        ARTICLE_PATTERN is never needed here: any header starting with "Art." would already have been
        caught by _match_unit (ARTICLE_HEADER_PATTERN.search matches everything ARTICLE_PATTERN.match does,
        and more), so execution never reaches this point with such text.
        """
        return DASH_PATTERN.match(text) is not None or any(
            pattern.match(text) is not None for pattern in CONTENT_PATTERNS
        )

    @staticmethod
    def _append_element(unit: LegalUnit, text: str) -> None:
        if (subsection_match := SUBSECTION_PATTERN.match(text)) is not None:
            subsection = subsection_match.group(1)
        elif unit.elements:
            subsection = unit.elements[-1].subsection
        else:
            subsection = None

        unit.elements.append(LegalUnitElement(text=text, subsection=subsection))
