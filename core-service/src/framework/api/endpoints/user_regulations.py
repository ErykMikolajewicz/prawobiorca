from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from src.app.dtos.regulations import RegulationData, RegulationRepresentation, RegulationUploadTarget
from src.app.dtos.search import SearchParams, SearchResult
from src.app.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    GetRegulationDownloadUrl,
    ListRegulations,
    RetryRegulationPreparation,
    SearchRegulation,
)
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationServiceUnavailable,
    RegulationsNotPreparedToSearch,
)
from src.domain.exceptions.users import UserNotFound
from src.domain.value_objects.regulations import RegulationType
from src.framework.dependencies.authentication import require_logged_user
from src.framework.dependencies.regulations import (
    get_add_regulation,
    get_confirm_regulation_upload,
    get_delete_regulation,
    get_list_regulations,
    get_regulation_download_url,
    get_retry_regulation_preparation,
    get_search_regulation,
)

user_regulations_router = APIRouter(
    tags=["user_regulations"], dependencies=(Depends(require_logged_user),), prefix="/api"
)


@user_regulations_router.get(
    "/user/regulations",
    response_model=list[RegulationRepresentation],
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Not found user files with that criteria."},
    },
)
async def get_user_regulations(
    list_regulations: Annotated[ListRegulations, Depends(get_list_regulations)],
    user_id: Annotated[UUID, Depends(require_logged_user)],
    regulation_type: RegulationType | None = Query(default=None, alias="documentType"),
) -> list[RegulationRepresentation] | Response:
    user_regulations = await list_regulations.execute(user_id, regulation_type)

    if not user_regulations:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return user_regulations


@user_regulations_router.post(
    "/user/regulations",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Can't add empty regulation."},
        status.HTTP_404_NOT_FOUND: {"description": "User not found!"},
    },
)
async def add_user_regulation(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    add_regulation_: Annotated[AddRegulation, Depends(get_add_regulation)],
    regulation_data: RegulationData,
) -> RegulationUploadTarget:
    try:
        return await add_regulation_.execute(user_id, regulation_data)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found!")


@user_regulations_router.post(
    "/user/regulations/{regulationId}/confirm-upload",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation upload already confirmed, or its content not found on storage!"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Preparation service not working!"},
    },
)
async def confirm_user_regulation_upload(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    confirm_upload: Annotated[ConfirmRegulationUpload, Depends(get_confirm_regulation_upload)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    try:
        await confirm_upload.execute(user_id, regulation_id)
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
    except RegulationServiceUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Preparation service not working!",
        )


@user_regulations_router.get(
    "/user/regulations/{regulationId}/download-url",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def get_user_regulation_download_url(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    get_download_url: Annotated[GetRegulationDownloadUrl, Depends(get_regulation_download_url)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
) -> str:
    try:
        return await get_download_url.execute(user_id, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@user_regulations_router.delete(
    "/user/regulations/{regulationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def delete_user_regulation(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    delete_user_regulation_: Annotated[DeleteRegulation, Depends(get_delete_regulation)],
    regulation_id: UUID = Path(alias="regulationId"),
):
    try:
        await delete_user_regulation_.execute(user_id, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@user_regulations_router.get(
    "/user/regulations/{regulationId}/documents",
    response_model=list[SearchResult],
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "No search results."},
        status.HTTP_400_BAD_REQUEST: {"description": "Regulation not prepared, by user, can't search."},
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found."},
    },
)
async def search_regulation_documents(
    search_regulation: Annotated[SearchRegulation, Depends(get_search_regulation)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
    user_id: Annotated[UUID, Depends(require_logged_user)],
    search_params: Annotated[SearchParams, Query()],
) -> list[SearchResult] | Response:
    try:
        results = await search_regulation.execute(user_id, regulation_id, search_params)
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

    if not results:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return results


@user_regulations_router.post(
    "/user/regulations/{regulationId}/preparation-retry",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation to prepare not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation already prepared, preparation in progress, or its content not uploaded!"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Preparation service not working!"},
    },
)
async def retry_user_regulation_preparation(
    retry_regulation_preparation: Annotated[RetryRegulationPreparation, Depends(get_retry_regulation_preparation)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
    user_id: Annotated[UUID, Depends(require_logged_user)],
):
    try:
        await retry_regulation_preparation.execute(user_id, regulation_id)
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
    except RegulationServiceUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Preparation service not working!",
        )
