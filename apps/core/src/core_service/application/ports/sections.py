from typing import Protocol
from uuid import UUID

from core_service.application.dtos.search import SearchParams, SearchResult, SectionRepresentation
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.regulations import SectionContent
from core_service.domain.value_objects.sections import SectionsCollection, SectionSummary, SectionToSummarize


class SectionsRepository(Protocol):
    async def add_sections(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID, sections: SectionsCollection
    ) -> None: ...

    async def list_sections_contents(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> list[SectionContent]: ...

    async def list_sections_to_summarize(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> list[SectionToSummarize]: ...

    async def set_summaries(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID, summaries: list[SectionSummary]
    ) -> None: ...

    async def clear_summaries(self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID) -> None: ...

    async def list_sections(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> list[SectionRepresentation]: ...

    async def search(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        regulation_id: UUID,
        vector: list[float],
        search_params: SearchParams,
    ) -> list[SearchResult]: ...
