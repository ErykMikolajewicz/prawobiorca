from typing import Annotated

from fastapi import Depends

from core_service.application.ports.oauth import (
    OAuthAuthorizationCodesRepository,
    OAuthClientsRepository,
    OAuthTokensRepository,
)
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.users import UsersRepository
from core_service.application.use_cases.oauth import (
    AuthorizeOAuthClient,
    CreateOAuthClient,
    DeleteOAuthClient,
    ExchangeAuthorizationCode,
    GetAuthorizationRequestDetails,
    ListOAuthClients,
    OAuthConfig,
    RefreshOAuthTokens,
)
from core_service.framework.consts import MCP_PATH
from core_service.framework.dependencies.relational import get_session_maker
from core_service.framework.dependencies.users import get_users_repository
from core_service.infrastructure.relational_db.repositories.oauth import (
    SqlaOAuthAuthorizationCodesRepository,
    SqlaOAuthClientsRepository,
    SqlaOAuthTokensRepository,
)
from core_service.shared.settings.oauth import oauth_settings


def get_oauth_config() -> OAuthConfig:
    return OAuthConfig(
        resource_url=f"{oauth_settings.PUBLIC_URL}{MCP_PATH}",
        allowed_redirect_uris=tuple(oauth_settings.REDIRECT_URIS),
        authorization_code_expiration_seconds=oauth_settings.AUTHORIZATION_CODE_EXPIRATION_SECONDS,
        access_token_expiration_seconds=oauth_settings.ACCESS_TOKEN_EXPIRATION_SECONDS,
        refresh_token_expiration_seconds=oauth_settings.REFRESH_TOKEN_EXPIRATION_SECONDS,
    )


def get_oauth_clients_repo() -> OAuthClientsRepository:
    return SqlaOAuthClientsRepository()


def get_oauth_codes_repo() -> OAuthAuthorizationCodesRepository:
    return SqlaOAuthAuthorizationCodesRepository()


def get_oauth_tokens_repo() -> OAuthTokensRepository:
    return SqlaOAuthTokensRepository()


def get_list_oauth_clients(
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
) -> ListOAuthClients:
    return ListOAuthClients(session_maker, users_repo, clients_repo)


def get_create_oauth_client(
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
) -> CreateOAuthClient:
    return CreateOAuthClient(session_maker, users_repo, clients_repo)


def get_delete_oauth_client(
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
) -> DeleteOAuthClient:
    return DeleteOAuthClient(session_maker, users_repo, clients_repo)


def get_get_authorization_request_details(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
    config: Annotated[OAuthConfig, Depends(get_oauth_config)],
) -> GetAuthorizationRequestDetails:
    return GetAuthorizationRequestDetails(session_maker, clients_repo, config)


def get_authorize_oauth_client(
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
    codes_repo: Annotated[OAuthAuthorizationCodesRepository, Depends(get_oauth_codes_repo)],
    config: Annotated[OAuthConfig, Depends(get_oauth_config)],
) -> AuthorizeOAuthClient:
    return AuthorizeOAuthClient(session_maker, users_repo, clients_repo, codes_repo, config)


def get_exchange_authorization_code(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
    codes_repo: Annotated[OAuthAuthorizationCodesRepository, Depends(get_oauth_codes_repo)],
    tokens_repo: Annotated[OAuthTokensRepository, Depends(get_oauth_tokens_repo)],
    config: Annotated[OAuthConfig, Depends(get_oauth_config)],
) -> ExchangeAuthorizationCode:
    return ExchangeAuthorizationCode(session_maker, clients_repo, codes_repo, tokens_repo, config)


def get_refresh_oauth_tokens(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    clients_repo: Annotated[OAuthClientsRepository, Depends(get_oauth_clients_repo)],
    tokens_repo: Annotated[OAuthTokensRepository, Depends(get_oauth_tokens_repo)],
    config: Annotated[OAuthConfig, Depends(get_oauth_config)],
) -> RefreshOAuthTokens:
    return RefreshOAuthTokens(session_maker, clients_repo, tokens_repo, config)
