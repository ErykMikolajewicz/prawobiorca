from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.app.dtos.organizations import NewOrganization, NewSuborganization, OrganizationData
from src.app.use_cases.organizations import (
    AddOrganization,
    AddSuborganization,
    DeleteOrganization,
    DeleteSuborganization,
    ListOrganizations,
    UpdateOrganization,
    UpdateSuborganization,
)
from src.domain.exceptions.organizations import OrganizationNotFound, SuborganizationNotFound
from src.framework.dependencies.authentication import require_admin
from src.framework.dependencies.organizations import (
    get_add_organization,
    get_add_suborganization,
    get_delete_organization,
    get_delete_suborganization,
    get_list_organizations,
    get_update_organization,
    get_update_suborganization,
)

organizations_router = APIRouter(tags=["organizations"], prefix="/api")


@organizations_router.get(
    "/organizations",
    response_model=list[OrganizationData],
)
async def get_organizations(
    list_organizations: Annotated[ListOrganizations, Depends(get_list_organizations)],
) -> list[OrganizationData]:
    return await list_organizations.execute()


@organizations_router.post(
    "/admin/organizations",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_201_CREATED,
)
async def add_organization(
    add_organization_: Annotated[AddOrganization, Depends(get_add_organization)],
    new_organization: NewOrganization,
) -> UUID:
    return await add_organization_.execute(new_organization)


@organizations_router.put(
    "/admin/organizations/{organizationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization not found!"},
    },
)
async def update_organization(
    update_organization_: Annotated[UpdateOrganization, Depends(get_update_organization)],
    organization_id: Annotated[UUID, Path(alias="organizationId")],
    new_organization: NewOrganization,
):
    try:
        await update_organization_.execute(organization_id, new_organization)
    except OrganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found!")


@organizations_router.delete(
    "/admin/organizations/{organizationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization not found!"},
    },
)
async def delete_organization(
    delete_organization_: Annotated[DeleteOrganization, Depends(get_delete_organization)],
    organization_id: Annotated[UUID, Path(alias="organizationId")],
):
    try:
        await delete_organization_.execute(organization_id)
    except OrganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found!")


@organizations_router.post(
    "/admin/organizations/{organizationId}/suborganizations",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization not found!"},
    },
)
async def add_suborganization(
    add_suborganization_: Annotated[AddSuborganization, Depends(get_add_suborganization)],
    organization_id: Annotated[UUID, Path(alias="organizationId")],
    new_suborganization: NewSuborganization,
) -> UUID:
    try:
        return await add_suborganization_.execute(organization_id, new_suborganization)
    except OrganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found!")


@organizations_router.put(
    "/admin/suborganizations/{suborganizationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Suborganization not found!"},
    },
)
async def update_suborganization(
    update_suborganization_: Annotated[UpdateSuborganization, Depends(get_update_suborganization)],
    suborganization_id: Annotated[UUID, Path(alias="suborganizationId")],
    new_suborganization: NewSuborganization,
):
    try:
        await update_suborganization_.execute(suborganization_id, new_suborganization)
    except SuborganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suborganization not found!")


@organizations_router.delete(
    "/admin/suborganizations/{suborganizationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Suborganization not found!"},
    },
)
async def delete_suborganization(
    delete_suborganization_: Annotated[DeleteSuborganization, Depends(get_delete_suborganization)],
    suborganization_id: Annotated[UUID, Path(alias="suborganizationId")],
):
    try:
        await delete_suborganization_.execute(suborganization_id)
    except SuborganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suborganization not found!")
