from typing import Protocol
from uuid import UUID

from src.app.dtos.search import SearchParams, SearchResult
from src.app.interfaces.relational import AsyncSession
from src.domain.value_objects.regulations import SectionContent
from src.domain.value_objects.sections import SectionsCollection


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

    async def remove_sections(self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID) -> None: ...
