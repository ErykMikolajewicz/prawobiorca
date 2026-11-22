import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from core_service.application.dtos.oauth import (
    AuthorizationRedirect,
    AuthorizationRequest,
    AuthorizationRequestDetails,
    CreatedOAuthClient,
    NewOAuthClient,
    OAuthClientCredentials,
    OAuthClientData,
    OAuthTokens,
)
from core_service.application.ports.oauth import (
    OAuthAuthorizationCodesRepository,
    OAuthClientsRepository,
    OAuthTokensRepository,
)
from core_service.application.ports.relational import AsyncSession, SessionMaker
from core_service.application.ports.users import UsersRepository
from core_service.domain.exceptions.access import AccessForbidden
from core_service.domain.exceptions.oauth import (
    InvalidAuthorizationRequest,
    InvalidClientCredentials,
    InvalidGrant,
    InvalidTarget,
    OAuthClientNotFound,
)
from core_service.domain.services.mcp_access import resolve_mcp_administrator
from core_service.domain.services.oauth import build_redirect_url, is_redirect_uri_allowed, verify_pkce_s256
from core_service.domain.services.security import generate_authorization_token, hash_token, verify_token_hash
from core_service.domain.value_objects.oauth import AuthorizationGrant, OAuthTokenHashes, OAuthTokenOwner
from core_service.domain.value_objects.users import Caller

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OAuthConfig:
    resource_url: str
    allowed_redirect_uris: tuple[str, ...]
    authorization_code_expiration_seconds: int
    access_token_expiration_seconds: int
    refresh_token_expiration_seconds: int


def issue_tokens(config: OAuthConfig) -> tuple[OAuthTokens, OAuthTokenHashes]:
    now = datetime.now(UTC)
    access_token = generate_authorization_token()
    refresh_token = generate_authorization_token()

    tokens = OAuthTokens(
        access_token=access_token,
        expires_in=config.access_token_expiration_seconds,
        refresh_token=refresh_token,
    )
    hashes = OAuthTokenHashes(
        access_token_hash=hash_token(access_token),
        access_valid_until=now + timedelta(seconds=config.access_token_expiration_seconds),
        refresh_token_hash=hash_token(refresh_token),
        refresh_valid_until=now + timedelta(seconds=config.refresh_token_expiration_seconds),
    )
    return tokens, hashes


async def require_current_admin(session: AsyncSession, users_repo: UsersRepository, caller: Caller) -> UUID:
    user_id = resolve_mcp_administrator(caller)
    privileges = await users_repo.get_user_privileges(session, user_id)
    if privileges is None or not privileges.is_admin:
        raise AccessForbidden
    return user_id


async def authenticate_client(
    session: AsyncSession, clients_repo: OAuthClientsRepository, credentials: OAuthClientCredentials
) -> None:
    secret_hash = await clients_repo.get_secret_hash(session, credentials.client_id)
    if secret_hash is None or not verify_token_hash(credentials.secret, secret_hash):
        logger.warning("Invalid OAuth client credentials!")
        raise InvalidClientCredentials


async def get_requesting_client_name(
    session: AsyncSession, clients_repo: OAuthClientsRepository, request: AuthorizationRequest, config: OAuthConfig
) -> str:
    if request.resource != config.resource_url:
        raise InvalidAuthorizationRequest
    if not is_redirect_uri_allowed(request.redirect_uri, config.allowed_redirect_uris):
        logger.warning("Authorization request with not allowed redirect URI: %s", request.redirect_uri)
        raise InvalidAuthorizationRequest

    client_name = await clients_repo.get_name(session, request.client_id)
    if client_name is None:
        logger.warning("Authorization request of unknown OAuth client!")
        raise InvalidAuthorizationRequest
    return client_name


@dataclass
class ListOAuthClients:
    session_maker: SessionMaker
    users_repo: UsersRepository
    clients_repo: OAuthClientsRepository

    async def execute(self, caller: Caller) -> list[OAuthClientData]:
        async with self.session_maker() as session:
            await require_current_admin(session, self.users_repo, caller)
            clients = await self.clients_repo.list_all(session)
        return clients


@dataclass
class CreateOAuthClient:
    session_maker: SessionMaker
    users_repo: UsersRepository
    clients_repo: OAuthClientsRepository

    async def execute(self, caller: Caller, new_client: NewOAuthClient) -> CreatedOAuthClient:
        secret = generate_authorization_token()
        async with self.session_maker.begin() as session:
            await require_current_admin(session, self.users_repo, caller)
            client_id = await self.clients_repo.add(session, new_client.name, hash_token(secret))
        return CreatedOAuthClient(id=client_id, secret=secret)


@dataclass
class DeleteOAuthClient:
    session_maker: SessionMaker
    users_repo: UsersRepository
    clients_repo: OAuthClientsRepository

    async def execute(self, caller: Caller, client_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            await require_current_admin(session, self.users_repo, caller)
            try:
                await self.clients_repo.delete(session, client_id)
            except OAuthClientNotFound:
                logger.warning("OAuth client not found!")
                raise


@dataclass
class GetAuthorizationRequestDetails:
    session_maker: SessionMaker
    clients_repo: OAuthClientsRepository
    config: OAuthConfig

    async def execute(self, request: AuthorizationRequest) -> AuthorizationRequestDetails:
        async with self.session_maker() as session:
            client_name = await get_requesting_client_name(session, self.clients_repo, request, self.config)
        return AuthorizationRequestDetails(client_name=client_name)


@dataclass
class AuthorizeOAuthClient:
    session_maker: SessionMaker
    users_repo: UsersRepository
    clients_repo: OAuthClientsRepository
    codes_repo: OAuthAuthorizationCodesRepository
    config: OAuthConfig

    async def execute(self, caller: Caller, request: AuthorizationRequest) -> AuthorizationRedirect:
        code = generate_authorization_token()
        valid_until = datetime.now(UTC) + timedelta(seconds=self.config.authorization_code_expiration_seconds)
        async with self.session_maker.begin() as session:
            user_id = await require_current_admin(session, self.users_repo, caller)
            await get_requesting_client_name(session, self.clients_repo, request, self.config)
            grant = AuthorizationGrant(
                client_id=request.client_id,
                user_id=user_id,
                redirect_uri=request.redirect_uri,
                code_challenge=request.code_challenge,
                resource=request.resource,
            )
            await self.codes_repo.add(session, hash_token(code), grant, valid_until)

        redirect_url = build_redirect_url(request.redirect_uri, {"code": code, "state": request.state})
        return AuthorizationRedirect(redirect_url=redirect_url)


@dataclass
class ExchangeAuthorizationCode:
    session_maker: SessionMaker
    clients_repo: OAuthClientsRepository
    codes_repo: OAuthAuthorizationCodesRepository
    tokens_repo: OAuthTokensRepository
    config: OAuthConfig

    async def execute(
        self,
        credentials: OAuthClientCredentials,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        resource: str | None,
    ) -> OAuthTokens:
        tokens, hashes = issue_tokens(self.config)

        async with self.session_maker.begin() as session:
            await authenticate_client(session, self.clients_repo, credentials)

            if resource != self.config.resource_url:
                raise InvalidTarget

            grant = await self.codes_repo.take(session, hash_token(code), datetime.now(UTC))
            if (
                grant is None
                or grant.resource != resource
                or grant.client_id != credentials.client_id
                or grant.redirect_uri != redirect_uri
                or not verify_pkce_s256(code_verifier, grant.code_challenge)
            ):
                logger.warning("Invalid authorization code exchange!")
                raise InvalidGrant

            await self.tokens_repo.add(session, grant.client_id, grant.user_id, resource, hashes)
        return tokens


@dataclass
class RefreshOAuthTokens:
    session_maker: SessionMaker
    clients_repo: OAuthClientsRepository
    tokens_repo: OAuthTokensRepository
    config: OAuthConfig

    async def execute(
        self, credentials: OAuthClientCredentials, refresh_token: str, resource: str | None
    ) -> OAuthTokens:
        tokens, hashes = issue_tokens(self.config)

        async with self.session_maker.begin() as session:
            await authenticate_client(session, self.clients_repo, credentials)

            if resource is not None and resource != self.config.resource_url:
                raise InvalidTarget

            is_rotated = await self.tokens_repo.rotate(
                session,
                credentials.client_id,
                self.config.resource_url,
                hash_token(refresh_token),
                datetime.now(UTC),
                hashes,
            )
            if not is_rotated:
                logger.warning("Invalid OAuth refresh token!")
                raise InvalidGrant
        return tokens


@dataclass
class AuthenticateMcpToken:
    session_maker: SessionMaker
    tokens_repo: OAuthTokensRepository

    async def execute(self, access_token: str) -> OAuthTokenOwner | None:
        async with self.session_maker() as session:
            owner = await self.tokens_repo.get_owner(session, hash_token(access_token), datetime.now(UTC))

        if owner is None or not owner.is_admin:
            logger.warning("Invalid MCP access token!")
            return None
        return owner


@dataclass
class DeleteExpiredOAuthGrants:
    session_maker: SessionMaker
    codes_repo: OAuthAuthorizationCodesRepository
    tokens_repo: OAuthTokensRepository

    async def execute(self) -> None:
        now = datetime.now(UTC)
        async with self.session_maker.begin() as session:
            await self.codes_repo.delete_expired(session, now)
            await self.tokens_repo.delete_expired(session, now)
