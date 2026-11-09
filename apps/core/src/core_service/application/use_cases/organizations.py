import logging
from dataclasses import dataclass
from uuid import UUID

from core_service.application.dtos.organizations import NewOrganization, NewSuborganization, OrganizationData
from core_service.application.ports.organizations import OrganizationsRepository, SuborganizationsRepository
from core_service.application.ports.relational import SessionMaker
from core_service.domain.exceptions.organizations import OrganizationNotFound, SuborganizationNotFound
from core_service.domain.services.organization_access import check_can_manage_organizations
from core_service.domain.value_objects.users import Caller

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

    async def execute(self, caller: Caller, new_organization: NewOrganization) -> UUID:
        check_can_manage_organizations(caller)

        async with self.session_maker.begin() as session:
            organization_id = await self.organizations_repo.add(session, new_organization)
        return organization_id


@dataclass
class UpdateOrganization:
    session_maker: SessionMaker
    organizations_repo: OrganizationsRepository

    async def execute(self, caller: Caller, organization_id: UUID, new_organization: NewOrganization) -> None:
        check_can_manage_organizations(caller)

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

    async def execute(self, caller: Caller, organization_id: UUID) -> None:
        check_can_manage_organizations(caller)

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

    async def execute(self, caller: Caller, organization_id: UUID, new_suborganization: NewSuborganization) -> UUID:
        check_can_manage_organizations(caller)

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

    async def execute(
        self,
        caller: Caller,
        organization_id: UUID,
        suborganization_id: UUID,
        new_suborganization: NewSuborganization,
    ) -> None:
        check_can_manage_organizations(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.suborganizations_repo.update(
                    session, organization_id, suborganization_id, new_suborganization
                )
            except SuborganizationNotFound:
                logger.warning("Suborganization not found!")
                raise


@dataclass
class DeleteSuborganization:
    session_maker: SessionMaker
    suborganizations_repo: SuborganizationsRepository

    async def execute(self, caller: Caller, organization_id: UUID, suborganization_id: UUID) -> None:
        check_can_manage_organizations(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.suborganizations_repo.delete(session, organization_id, suborganization_id)
            except SuborganizationNotFound:
                logger.warning("Suborganization not found!")
                raise
