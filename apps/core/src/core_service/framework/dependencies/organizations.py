from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status

from core_service.application.ports.organizations import OrganizationsRepository, SuborganizationsRepository
from core_service.application.ports.relational import SessionMaker
from core_service.application.use_cases.organizations import (
    AddOrganization,
    AddSuborganization,
    DeleteOrganization,
    DeleteSuborganization,
    ListOrganizations,
    UpdateOrganization,
    UpdateSuborganization,
)
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.relational_db.repositories.organizations import (
    SqlaOrganizationsRepository,
    SqlaSuborganizationsRepository,
)


def get_organization_filter(
    organization_id: UUID | None = Query(default=None, alias="organizationId"),
    suborganization_id: UUID | None = Query(default=None, alias="suborganizationId"),
) -> OrganizationFilter | None:
    if organization_id is None:
        if suborganization_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Suborganization given without organization!",
            )
        return None

    return OrganizationFilter(organization_id, suborganization_id)


def get_organizations_repo() -> OrganizationsRepository:
    return SqlaOrganizationsRepository()


def get_suborganizations_repo() -> SuborganizationsRepository:
    return SqlaSuborganizationsRepository()


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
