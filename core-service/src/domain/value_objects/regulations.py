import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from src.domain.services.legal_structure_parser import (
    LETTER_PATTERN,
    POINT_PATTERN,
    SUBSECTION_PATTERN,
    LegalStructureParser,
)
from src.domain.value_objects.legal_units import (
    BREADCRUMB_SEPARATOR,
    LegalUnit,
    LegalUnitElement,
    RegulationElement,
)
from src.domain.value_objects.sections import ChunkSpan, RegulationSection, SectionChunk, SectionsCollection

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.;])\s+")

BLOCK_PATTERNS = (SUBSECTION_PATTERN, POINT_PATTERN, LETTER_PATTERN)

CHUNK_MAX_TOKENS = 200

MIN_CONTENT_TOKENS = 32

MAX_TITLE_TOKENS_SHARE = 0.25


@dataclass
class ChunkAtom:
    text: str
    subsection: str | None
    element_index: int
    start: int
    end: int


@dataclass
class ChunkPart:
    atoms: list[ChunkAtom]
    context: list[str] = field(default_factory=list)


class Tokenizer(Protocol):
    max_tokens: int

    def count_tokens(self, text: str) -> int: ...


@dataclass
class RegulationAct:
    _elements: Iterable[RegulationElement]
    _tokenizer: Tokenizer

    def get_sections_to_embed(self) -> SectionsCollection:
        units = LegalStructureParser().parse(self._elements)

        sections = []
        for unit in units:
            section = self._create_section(unit)
            if section is not None:
                sections.append(section)

        for index, section in enumerate(sections):
            section.section_order = index

        return SectionsCollection(sections)

    def _create_section(self, unit: LegalUnit) -> RegulationSection | None:
        if not unit.elements:
            return None

        embed_title = self._fit_title(unit)
        tokens_limit = min(CHUNK_MAX_TOKENS, self._tokenizer.max_tokens)
        content_budget = self._count_content_budget(embed_title, tokens_limit)
        chunks = self._create_chunks(unit.elements, embed_title, content_budget)
        overflow = self._count_overflow(chunks, tokens_limit)
        while overflow > 0 and content_budget > MIN_CONTENT_TOKENS:
            content_budget = max(content_budget - overflow, MIN_CONTENT_TOKENS)
            chunks = self._create_chunks(unit.elements, embed_title, content_budget)
            overflow = self._count_overflow(chunks, tokens_limit)

        return RegulationSection(
            header=unit.breadcrumb,
            text="\n".join(element.text for element in unit.elements),
            chunks=chunks,
            unit_type=unit.unit_type,
            unit_number=unit.number,
            unit_path=list(unit.path),
            elements=list(unit.elements),
        )

    def _create_chunks(
        self, elements: list[LegalUnitElement], embed_title: str | None, content_budget: int
    ) -> list[SectionChunk]:
        parts = self._split_to_parts(elements, content_budget)
        part_titles = self._create_part_titles(embed_title, parts)

        return [
            SectionChunk(
                text=" ".join(atom.text for atom in part.atoms),
                embed_title=part_title,
                chunk_index=chunk_index,
                span=ChunkSpan(
                    part.atoms[0].element_index,
                    part.atoms[0].start,
                    part.atoms[-1].element_index,
                    part.atoms[-1].end,
                ),
            )
            for chunk_index, (part, part_title) in enumerate(zip(parts, part_titles, strict=True))
        ]

    def _count_overflow(self, chunks: list[SectionChunk], tokens_limit: int) -> int:
        max_chunk_tokens = max(self._tokenizer.count_tokens(chunk.embedding_text) for chunk in chunks)

        return max_chunk_tokens - tokens_limit

    def _fit_title(self, unit: LegalUnit) -> str | None:
        segments = unit.breadcrumb_segments
        if not segments:
            return None

        max_title_tokens = int(CHUNK_MAX_TOKENS * MAX_TITLE_TOKENS_SHARE)
        title = BREADCRUMB_SEPARATOR.join(segments)
        while len(segments) > 1 and self._tokenizer.count_tokens(title) > max_title_tokens:
            segments = segments[1:]
            title = BREADCRUMB_SEPARATOR.join(segments)

        return title

    def _count_content_budget(self, title: str | None, tokens_limit: int) -> int:
        prefix_tokens = self._tokenizer.count_tokens(SectionChunk(text="", embed_title=title).embedding_text)

        content_budget = tokens_limit - prefix_tokens

        return max(content_budget, MIN_CONTENT_TOKENS)

    def _split_to_parts(self, elements: list[LegalUnitElement], content_budget: int) -> list[ChunkPart]:
        return self._split_block(elements, list(range(len(elements))), 0, content_budget)

    def _split_block(
        self, elements: list[LegalUnitElement], indices: list[int], level: int, content_budget: int
    ) -> list[ChunkPart]:
        if self._count_block_tokens(elements, indices) <= content_budget:
            return [ChunkPart(self._create_element_atoms(elements, indices))]

        if level == len(BLOCK_PATTERNS):
            return self._split_elements(elements, indices, content_budget)

        return self._split_children(elements, indices, level, content_budget)

    def _split_children(
        self, elements: list[LegalUnitElement], indices: list[int], level: int, content_budget: int
    ) -> list[ChunkPart]:
        children = self._group_indices(elements, indices, BLOCK_PATTERNS[level])
        if len(children) == 1:
            return self._split_block(elements, indices, level + 1, content_budget)

        parts = []
        fitting_children = []
        for child in children:
            if self._count_block_tokens(elements, child) <= content_budget:
                fitting_children.append(child)
                continue

            parts.extend(self._pack_children(elements, fitting_children, content_budget))
            fitting_children = []
            parts.extend(self._split_block(elements, child, level + 1, content_budget))

        parts.extend(self._pack_children(elements, fitting_children, content_budget))

        if level > 0:
            lead = self._find_lead(elements, indices, BLOCK_PATTERNS[level])
            for part in parts[1:]:
                if part.context[: len(lead)] != lead:
                    part.context[:0] = lead

        return parts

    def _pack_children(
        self, elements: list[LegalUnitElement], children: list[list[int]], content_budget: int
    ) -> list[ChunkPart]:
        children_tokens = [self._count_block_tokens(elements, child) for child in children]

        return [
            ChunkPart(self._create_element_atoms(elements, [index for child in group for index in children[child]]))
            for group in self._pack_evenly(children_tokens, content_budget)
        ]

    def _split_elements(
        self, elements: list[LegalUnitElement], indices: list[int], content_budget: int
    ) -> list[ChunkPart]:
        atoms = []
        for element_index in indices:
            atoms.extend(self._split_long_element(elements[element_index], element_index, content_budget))

        atoms_tokens = [self._tokenizer.count_tokens(atom.text) for atom in atoms]

        return [ChunkPart([atoms[atom] for atom in group]) for group in self._pack_evenly(atoms_tokens, content_budget)]

    @staticmethod
    def _group_indices(elements: list[LegalUnitElement], indices: list[int], pattern: re.Pattern) -> list[list[int]]:
        groups = []
        has_child = False
        for element_index in indices:
            is_child_start = pattern.match(elements[element_index].text) is not None
            if not groups or (is_child_start and has_child):
                groups.append([])
            groups[-1].append(element_index)
            has_child = has_child or is_child_start

        return groups

    @staticmethod
    def _find_lead(elements: list[LegalUnitElement], indices: list[int], pattern: re.Pattern) -> list[str]:
        lead = []
        for element_index in indices:
            if pattern.match(elements[element_index].text):
                break
            lead.append(elements[element_index].text)

        return lead

    def _count_block_tokens(self, elements: list[LegalUnitElement], indices: list[int]) -> int:
        return sum(self._tokenizer.count_tokens(elements[element_index].text) for element_index in indices)

    @staticmethod
    def _create_element_atoms(elements: list[LegalUnitElement], indices: list[int]) -> list[ChunkAtom]:
        return [
            ChunkAtom(
                elements[element_index].text,
                elements[element_index].subsection,
                element_index,
                0,
                len(elements[element_index].text),
            )
            for element_index in indices
        ]

    @staticmethod
    def _pack_evenly(items_tokens: list[int], content_budget: int) -> list[list[int]]:
        groups_count = len(RegulationAct._pack_greedily(items_tokens, content_budget))

        low = max(items_tokens, default=0)
        high = max(content_budget, low)
        while low < high:
            middle = (low + high) // 2
            if len(RegulationAct._pack_greedily(items_tokens, middle)) <= groups_count:
                high = middle
            else:
                low = middle + 1

        return RegulationAct._pack_greedily(items_tokens, low)

    @staticmethod
    def _pack_greedily(items_tokens: list[int], content_budget: int) -> list[list[int]]:
        groups = []
        current_tokens = 0
        for item_index, item_tokens in enumerate(items_tokens):
            if not groups or current_tokens + item_tokens > content_budget:
                groups.append([])
                current_tokens = 0

            groups[-1].append(item_index)
            current_tokens += item_tokens

        return groups

    def _split_long_element(
        self, element: LegalUnitElement, element_index: int, content_budget: int
    ) -> list[ChunkAtom]:
        if self._tokenizer.count_tokens(element.text) <= content_budget:
            return [ChunkAtom(element.text, element.subsection, element_index, 0, len(element.text))]

        fragments = []
        for sentence in SENTENCE_SPLIT_PATTERN.split(element.text):
            fragments.extend(self._split_by_tokens(sentence, content_budget))

        atoms = []
        cursor = 0
        for fragment in fragments:
            start = element.text.find(fragment, cursor)
            cursor = start + len(fragment)
            atoms.append(ChunkAtom(fragment, element.subsection, element_index, start, cursor))

        return atoms

    def _split_by_tokens(self, text: str, content_budget: int) -> list[str]:
        if self._tokenizer.count_tokens(text) <= content_budget:
            return [text]

        fragments = []
        current_words = []
        current_tokens = 0
        for word in text.split(" "):
            word_tokens = self._tokenizer.count_tokens(word)

            if current_words and current_tokens + word_tokens > content_budget:
                fragments.append(" ".join(current_words))
                current_words = []
                current_tokens = 0

            current_words.append(word)
            current_tokens += word_tokens

        if current_words:
            fragments.append(" ".join(current_words))

        return fragments

    @staticmethod
    def _create_part_titles(title: str | None, parts: list[ChunkPart]) -> list[str | None]:
        parts_total = len(parts)
        if parts_total == 1:
            return [title]

        subsection_suffixes = [RegulationAct._create_subsection_suffix(part.atoms) for part in parts]
        are_suffixes_unambiguous = None not in subsection_suffixes and len(set(subsection_suffixes)) == parts_total

        part_titles = []
        for part_index, (part, subsection_suffix) in enumerate(zip(parts, subsection_suffixes, strict=True), start=1):
            if are_suffixes_unambiguous:
                part_suffix = subsection_suffix
            elif subsection_suffix is None:
                part_suffix = f"(część {part_index}/{parts_total})"
            else:
                part_suffix = f"{subsection_suffix} (część {part_index}/{parts_total})"

            part_title = part_suffix if title is None else f"{title} {part_suffix}"
            part_titles.append("\n".join([part_title, *part.context]))

        return part_titles

    @staticmethod
    def _create_subsection_suffix(part: list[ChunkAtom]) -> str | None:
        subsections = [element.subsection for element in part if element.subsection is not None]
        if not subsections:
            return None

        if subsections[0] == subsections[-1]:
            return f"ust. {subsections[0]}"

        return f"ust. {subsections[0]}-{subsections[-1]}"


class RegulationType(StrEnum):
    ACT = "ACT"
    DECREE = "DECREE"
    STATUTE = "STATUTE"


class RegulationPreparationStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PREPARED = "PREPARED"
    FAILED = "FAILED"


@dataclass
class RegulationRegistrationData:
    presentation_name: str
    regulation_type: RegulationType | None = None


@dataclass
class RegulationDetails:
    presentation_name: str
    description: str | None = None
