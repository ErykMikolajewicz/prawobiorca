from dataclasses import dataclass, field
from itertools import batched
from typing import Iterable
from uuid import UUID, uuid4

from src.domain.value_objects.legal_units import LegalUnitElement


@dataclass
class ChunkSpan:
    start_element: int
    end_element: int


@dataclass
class SectionChunk:
    text: str
    embed_title: str | None = None
    chunk_index: int = 0
    span: ChunkSpan | None = None
    vector: list[float] | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def embedding_text(self) -> str:
        if not self.embed_title:
            return self.text
        return f"{self.embed_title}\n{self.text}"


@dataclass
class RegulationSection:
    header: str | None
    text: str
    chunks: list[SectionChunk]
    section_order: int | None = None
    elements: list[LegalUnitElement] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


@dataclass
class SectionsCollection:
    _sections: list[RegulationSection]

    def __iter__(self) -> Iterable[RegulationSection]:
        return iter(self._sections)

    def get_chunks_batch_iterator(self, batch_size: int) -> list[list[SectionChunk]]:
        chunks_to_embed = [chunk for section in self._sections for chunk in section.chunks]
        chunks_to_embed.sort(key=lambda chunk: len(chunk.text))

        batches = []
        for batch in batched(chunks_to_embed, batch_size, strict=False):
            batches.append(batch)
        return batches
