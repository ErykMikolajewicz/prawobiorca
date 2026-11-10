from typing import Protocol
from uuid import UUID

from core_service.application.dtos.search import SearchParams, SearchResult
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.regulations import SectionContent
from core_service.domain.value_objects.sections import SectionsCollection


class SectionsRepository(Protocol):
    async def add_sections(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID, sections: SectionsCollection
    ) -> None: ...

    async def list_sections_contents(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> list[SectionContent]: ...

    async def search(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        regulation_id: UUID,
        vector: list[float],
        search_params: SearchParams,
    ) -> list[SearchResult]: ...
