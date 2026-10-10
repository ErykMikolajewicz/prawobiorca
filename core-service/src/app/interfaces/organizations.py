from typing import Protocol
from uuid import UUID

from src.app.dtos.organizations import NewOrganization, NewSuborganization, OrganizationData
from src.app.interfaces.relational import AsyncSession


class OrganizationsRepository(Protocol):
    async def list_all(self, session: AsyncSession) -> list[OrganizationData]: ...

    async def add(self, session: AsyncSession, new_organization: NewOrganization) -> UUID: ...

    async def update(self, session: AsyncSession, organization_id: UUID, new_organization: NewOrganization) -> None: ...

    async def delete(self, session: AsyncSession, organization_id: UUID) -> None: ...


class SuborganizationsRepository(Protocol):
    async def add(
        self, session: AsyncSession, organization_id: UUID, new_suborganization: NewSuborganization
    ) -> UUID: ...

    async def update(
        self, session: AsyncSession, suborganization_id: UUID, new_suborganization: NewSuborganization
    ) -> None: ...

    async def delete(self, session: AsyncSession, suborganization_id: UUID) -> None: ...
