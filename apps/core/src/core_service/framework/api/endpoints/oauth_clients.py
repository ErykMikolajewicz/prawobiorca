from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from core_service.application.dtos.oauth import CreatedOAuthClient, NewOAuthClient, OAuthClientData
from core_service.application.use_cases.oauth import CreateOAuthClient, DeleteOAuthClient, ListOAuthClients
from core_service.domain.exceptions.oauth import OAuthClientNotFound
from core_service.domain.value_objects.users import Caller
from core_service.framework.dependencies.authentication import get_caller
from core_service.framework.dependencies.oauth import (
    get_create_oauth_client,
    get_delete_oauth_client,
    get_list_oauth_clients,
)

oauth_clients_router = APIRouter(tags=["oauth-clients"], prefix="/api")


@oauth_clients_router.get(
    "/oauth-clients",
    response_model=list[OAuthClientData],
)
async def get_oauth_clients(
    caller: Annotated[Caller, Depends(get_caller)],
    list_oauth_clients: Annotated[ListOAuthClients, Depends(get_list_oauth_clients)],
) -> list[OAuthClientData]:
    return await list_oauth_clients.execute(caller)


@oauth_clients_router.post(
    "/oauth-clients",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedOAuthClient,
)
async def create_oauth_client(
    caller: Annotated[Caller, Depends(get_caller)],
    create_oauth_client_: Annotated[CreateOAuthClient, Depends(get_create_oauth_client)],
    new_client: NewOAuthClient,
) -> CreatedOAuthClient:
    return await create_oauth_client_.execute(caller, new_client)


@oauth_clients_router.delete(
    "/oauth-clients/{clientId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "OAuth client not found!"},
    },
)
async def delete_oauth_client(
    caller: Annotated[Caller, Depends(get_caller)],
    delete_oauth_client_: Annotated[DeleteOAuthClient, Depends(get_delete_oauth_client)],
    client_id: Annotated[UUID, Path(alias="clientId")],
):
    try:
        await delete_oauth_client_.execute(caller, client_id)
    except OAuthClientNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth client not found!")
