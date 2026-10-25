from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.app.dtos.regulations import (
    RegulationData,
    RegulationDetailsData,
    RegulationRepresentation,
    RegulationUploadTarget,
)
from src.app.dtos.search import SearchParams, SearchResult
from src.app.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    GetRegulation,
    GetRegulationDownloadUrl,
    ListRegulations,
    RegenerateRegulationDescription,
    RetryRegulationPreparation,
    SearchRegulation,
    UpdateRegulation,
)
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationDescriptionGenerationInProgress,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationsNotPreparedToSearch,
)
from src.domain.exceptions.users import UserNotFound
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.regulations import RegulationScope, RegulationType
from src.domain.value_objects.users import Caller
from src.framework.dependencies.authentication import get_caller
from src.framework.dependencies.organizations import get_organization_filter
from src.framework.dependencies.regulations import (
    get_add_regulation,
    get_confirm_regulation_upload,
    get_delete_regulation,
    get_list_regulations,
    get_regenerate_regulation_description,
    get_regulation,
    get_regulation_download_url,
    get_retry_regulation_preparation,
    get_search_regulation,
    get_update_regulation,
)

regulations_router = APIRouter(
    tags=["regulations"],
    prefix="/api",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Login required!"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission required!"},
    },
)


@regulations_router.get(
    "/regulations",
    response_model=list[RegulationRepresentation],
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Suborganization given without organization!"},
    },
)
async def get_regulations(
    list_regulations: Annotated[ListRegulations, Depends(get_list_regulations)],
    caller: Annotated[Caller, Depends(get_caller)],
    organization_filter: Annotated[OrganizationFilter | None, Depends(get_organization_filter)],
    scope: RegulationScope = Query(default=RegulationScope.PUBLIC),
    regulation_type: RegulationType | None = Query(default=None, alias="documentType"),
) -> list[RegulationRepresentation]:
    return await list_regulations.execute(caller, scope, regulation_type, organization_filter)


@regulations_router.get(
    "/regulations/{regulationId}",
    response_model=RegulationRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def get_regulation_by_id(
    get_regulation_: Annotated[GetRegulation, Depends(get_regulation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
) -> RegulationRepresentation:
    try:
        return await get_regulation_.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@regulations_router.get(
    "/regulations/{regulationId}/documents",
    response_model=list[SearchResult],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Regulation not prepared, normally should not occur."},
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found."},
    },
)
async def search_regulation_documents(
    search_regulation: Annotated[SearchRegulation, Depends(get_search_regulation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
    search_params: Annotated[SearchParams, Query()],
) -> list[SearchResult]:
    try:
        results = await search_regulation.execute(caller, regulation_id, search_params)
    except RegulationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Regulation with id {regulation_id} not found."
        )
    except RegulationsNotPreparedToSearch as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Regulation {e.regulations_name}, not prepared to search,"
            f" report problem to application administrator.",
        )

    return results


@regulations_router.post(
    "/regulations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Organization or user not found!"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Organization given for private regulation, or suborganization given without organization!"
        },
    },
)
async def add_regulation(
    add_regulation_: Annotated[AddRegulation, Depends(get_add_regulation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_data: RegulationData,
) -> RegulationUploadTarget:
    try:
        return await add_regulation_.execute(caller, regulation_data)
    except OrganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found!")
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")


@regulations_router.post(
    "/regulations/{regulationId}/confirm-upload",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation upload already confirmed, or its content not found on storage!"
        },
    },
)
async def confirm_regulation_upload(
    confirm_upload: Annotated[ConfirmRegulationUpload, Depends(get_confirm_regulation_upload)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    try:
        await confirm_upload.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")
    except RegulationContentNotFound:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation content not found in storage!",
        )
    except RegulationAlreadyInitialized:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation is already prepared!",
        )
    except RegulationPreparationInProgress:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation preparation already in progress!",
        )
    except RegulationInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation upload already confirmed!",
        )


@regulations_router.get(
    "/regulations/{regulationId}/download-url",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def get_regulation_download_url_by_id(
    get_download_url: Annotated[GetRegulationDownloadUrl, Depends(get_regulation_download_url)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
) -> str:
    try:
        return await get_download_url.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@regulations_router.patch(
    "/regulations/{regulationId}",
    response_model=RegulationRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def update_regulation(
    update_regulation_: Annotated[UpdateRegulation, Depends(get_update_regulation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
    regulation_details_data: RegulationDetailsData,
) -> RegulationRepresentation:
    try:
        return await update_regulation_.execute(caller, regulation_id, regulation_details_data)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@regulations_router.delete(
    "/regulations/{regulationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def delete_regulation(
    delete_regulation_: Annotated[DeleteRegulation, Depends(get_delete_regulation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: UUID = Path(alias="regulationId"),
):
    try:
        await delete_regulation_.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@regulations_router.post(
    "/regulations/{regulationId}/preparation-retry",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation to prepare not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation already prepared, preparation in progress, or its content not uploaded!"
        },
    },
)
async def retry_regulation_preparation(
    retry_regulation_preparation_: Annotated[RetryRegulationPreparation, Depends(get_retry_regulation_preparation)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    try:
        await retry_regulation_preparation_.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulation to prepare not found!",
        )
    except RegulationAlreadyInitialized:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation already prepared to search!",
        )
    except RegulationPreparationInProgress:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation preparation already in progress!",
        )
    except RegulationInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation content not uploaded!",
        )


@regulations_router.post(
    "/regulations/{regulationId}/description-generation",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation not prepared, or its description generation already in progress!"
        },
    },
)
async def regenerate_regulation_description(
    regenerate_description: Annotated[RegenerateRegulationDescription, Depends(get_regenerate_regulation_description)],
    caller: Annotated[Caller, Depends(get_caller)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    try:
        await regenerate_description.execute(caller, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")
    except RegulationInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation not prepared!",
        )
    except RegulationDescriptionGenerationInProgress:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Regulation description generation already in progress!",
        )
