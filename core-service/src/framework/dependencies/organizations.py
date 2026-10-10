from typing import Annotated

from fastapi import Depends

import src.infrastructure.relational_db.repositories.organizations as sqla_repos
from src.app.interfaces.organizations import OrganizationsRepository, SuborganizationsRepository
from src.app.interfaces.relational import SessionMaker
from src.app.use_cases.organizations import (
    AddOrganization,
    AddSuborganization,
    DeleteOrganization,
    DeleteSuborganization,
    ListOrganizations,
    UpdateOrganization,
    UpdateSuborganization,
)
from src.framework.dependencies.relational import get_session_maker


def get_organizations_repo() -> OrganizationsRepository:
    return sqla_repos.OrganizationsRepository()


def get_suborganizations_repo() -> SuborganizationsRepository:
    return sqla_repos.SuborganizationsRepository()


def get_list_organizations(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    organizations_repo: Annotated[OrganizationsRepository, Depends(get_organizations_repo)],
) -> ListOrganizations:
    return ListOrganizations(session_maker, organizations_repo)


def get_add_organization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    organizations_repo: Annotated[OrganizationsRepository, Depends(get_organizations_repo)],
) -> AddOrganization:
    return AddOrganization(session_maker, organizations_repo)


def get_update_organization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    organizations_repo: Annotated[OrganizationsRepository, Depends(get_organizations_repo)],
) -> UpdateOrganization:
    return UpdateOrganization(session_maker, organizations_repo)


def get_delete_organization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    organizations_repo: Annotated[OrganizationsRepository, Depends(get_organizations_repo)],
) -> DeleteOrganization:
    return DeleteOrganization(session_maker, organizations_repo)


def get_add_suborganization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    suborganizations_repo: Annotated[SuborganizationsRepository, Depends(get_suborganizations_repo)],
) -> AddSuborganization:
    return AddSuborganization(session_maker, suborganizations_repo)


def get_update_suborganization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    suborganizations_repo: Annotated[SuborganizationsRepository, Depends(get_suborganizations_repo)],
) -> UpdateSuborganization:
    return UpdateSuborganization(session_maker, suborganizations_repo)


def get_delete_suborganization(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    suborganizations_repo: Annotated[SuborganizationsRepository, Depends(get_suborganizations_repo)],
) -> DeleteSuborganization:
    return DeleteSuborganization(session_maker, suborganizations_repo)
