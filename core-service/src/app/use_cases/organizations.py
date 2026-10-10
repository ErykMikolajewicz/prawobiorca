import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.organizations import NewOrganization, NewSuborganization, OrganizationData
from src.app.interfaces.organizations import OrganizationsRepository, SuborganizationsRepository
from src.app.interfaces.relational import SessionMaker
from src.domain.exceptions.organizations import OrganizationNotFound, SuborganizationNotFound

logger = logging.getLogger(__name__)


@dataclass
class ListOrganizations:
    session_maker: SessionMaker
    organizations_repo: OrganizationsRepository

    async def execute(self) -> list[OrganizationData]:
        async with self.session_maker() as session:
            organizations = await self.organizations_repo.list_all(session)
        return organizations


@dataclass
class AddOrganization:
    session_maker: SessionMaker
    organizations_repo: OrganizationsRepository

    async def execute(self, new_organization: NewOrganization) -> UUID:
        async with self.session_maker.begin() as session:
            organization_id = await self.organizations_repo.add(session, new_organization)
        return organization_id


@dataclass
class UpdateOrganization:
    session_maker: SessionMaker
    organizations_repo: OrganizationsRepository

    async def execute(self, organization_id: UUID, new_organization: NewOrganization) -> None:
        async with self.session_maker.begin() as session:
            try:
                await self.organizations_repo.update(session, organization_id, new_organization)
            except OrganizationNotFound:
                logger.warning("Organization not found!")
                raise


@dataclass
class DeleteOrganization:
    session_maker: SessionMaker
    organizations_repo: OrganizationsRepository

    async def execute(self, organization_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            try:
                await self.organizations_repo.delete(session, organization_id)
            except OrganizationNotFound:
                logger.warning("Organization not found!")
                raise


@dataclass
class AddSuborganization:
    session_maker: SessionMaker
    suborganizations_repo: SuborganizationsRepository

    async def execute(self, organization_id: UUID, new_suborganization: NewSuborganization) -> UUID:
        async with self.session_maker.begin() as session:
            try:
                suborganization_id = await self.suborganizations_repo.add(session, organization_id, new_suborganization)
            except OrganizationNotFound:
                logger.warning("Organization not found!")
                raise
        return suborganization_id


@dataclass
class UpdateSuborganization:
    session_maker: SessionMaker
    suborganizations_repo: SuborganizationsRepository

    async def execute(self, suborganization_id: UUID, new_suborganization: NewSuborganization) -> None:
        async with self.session_maker.begin() as session:
            try:
                await self.suborganizations_repo.update(session, suborganization_id, new_suborganization)
            except SuborganizationNotFound:
                logger.warning("Suborganization not found!")
                raise


@dataclass
class DeleteSuborganization:
    session_maker: SessionMaker
    suborganizations_repo: SuborganizationsRepository

    async def execute(self, suborganization_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            try:
                await self.suborganizations_repo.delete(session, suborganization_id)
            except SuborganizationNotFound:
                logger.warning("Suborganization not found!")
                raise
