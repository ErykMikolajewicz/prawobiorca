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
    RegulationsNotPreparedToSearch,
)
from src.domain.value_objects.regulations import RegulationType
from src.framework.dependencies.authentication import require_admin
from src.framework.dependencies.regulations import (
    get_add_regulation,
    get_confirm_regulation_upload,
    get_delete_regulation,
    get_list_regulations,
    get_regulation_download_url,
    get_retry_regulation_preparation,
    get_search_regulation,
)

public_regulations_router = APIRouter(tags=["regulations"], prefix="/api")


@public_regulations_router.get(
    "/regulations",
    response_model=list[RegulationRepresentation],
    responses={status.HTTP_204_NO_CONTENT: {"description": "No public files for given search criteria."}},
)
async def get_public_regulations(
    list_regulations: Annotated[ListRegulations, Depends(get_list_regulations)],
    regulation_type: RegulationType | None = Query(default=None, alias="documentType"),
) -> list[RegulationRepresentation] | Response:
    user_id = None
    public_regulations = await list_regulations.execute(user_id, regulation_type)
    if not public_regulations:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return public_regulations


@public_regulations_router.get(
    "/regulations/{regulationId}/documents",
    response_model=list[SearchResult],
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "No search results."},
        status.HTTP_400_BAD_REQUEST: {"description": "Regulation not prepared, normally should not occur."},
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found."},
    },
)
async def search_regulation_documents(
    search_regulation: Annotated[SearchRegulation, Depends(get_search_regulation)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
    search_params: Annotated[SearchParams, Query()],
) -> list[SearchResult] | Response:
    user_id = None
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


@public_regulations_router.post(
    "/regulations",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_201_CREATED,
)
async def add_public_regulation(
    add_regulation_: Annotated[AddRegulation, Depends(get_add_regulation)],
    regulation_data: RegulationData,
) -> RegulationUploadTarget:
    user_id = None

    return await add_regulation_.execute(user_id, regulation_data)


@public_regulations_router.post(
    "/regulations/{regulationId}/confirm-upload",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation upload already confirmed, or its content not found on storage!"
        },
    },
)
async def confirm_public_regulation_upload(
    confirm_upload: Annotated[ConfirmRegulationUpload, Depends(get_confirm_regulation_upload)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    user_id = None
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


@public_regulations_router.get(
    "/regulations/{regulationId}/download-url",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def get_public_regulation_download_url(
    get_download_url: Annotated[GetRegulationDownloadUrl, Depends(get_regulation_download_url)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
) -> str:
    user_id = None
    try:
        return await get_download_url.execute(user_id, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@public_regulations_router.delete(
    "/regulations/{regulationId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation not found!"},
    },
)
async def delete_public_regulation(
    delete_regulation_: Annotated[DeleteRegulation, Depends(get_delete_regulation)],
    regulation_id: UUID = Path(alias="regulationId"),
):
    user_id = None
    try:
        await delete_regulation_.execute(user_id, regulation_id)
    except RegulationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found!")


@public_regulations_router.post(
    "/regulations/{regulationId}/preparation-retry",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Regulation to prepare not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Regulation already prepared, preparation in progress, or its content not uploaded!"
        },
    },
)
async def retry_public_regulation_preparation(
    retry_regulation_preparation: Annotated[RetryRegulationPreparation, Depends(get_retry_regulation_preparation)],
    regulation_id: Annotated[UUID, Path(alias="regulationId")],
):
    user_id = None
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
