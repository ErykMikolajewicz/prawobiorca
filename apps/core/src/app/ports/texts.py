from collections.abc import Iterable
from typing import Protocol

from src.domain.value_objects.sections import SectionChunk


class TextsEmbedder(Protocol):
    async def embed_chunks(self, chunks: Iterable[SectionChunk]) -> list[list[float]]: ...

    async def embed_texts(self, texts: Iterable[str]) -> list[list[float]]: ...

    async def embed_queries(self, queries: Iterable[str]) -> list[list[float]]: ...
