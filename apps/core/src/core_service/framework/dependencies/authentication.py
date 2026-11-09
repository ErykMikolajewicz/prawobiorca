import logging
from typing import Annotated

from fastapi import Depends, Request

from core_service.application.interfaces.relational import SessionMaker
from core_service.application.interfaces.users import UsersRepository, UsersSessionsRepository
from core_service.application.use_cases.auth import AuthTokensConfig, LogoutUser, LogUser, RefreshTokens
from core_service.domain.exceptions.users import InvalidAccessToken
from core_service.domain.services.security import JWT_ALGORITHM, decode_access_token
from core_service.domain.value_objects.auth import AccessTokenClaims
from core_service.domain.value_objects.users import Caller
from core_service.framework.consts import ACCESS_COOKIE_NAME
from core_service.framework.dependencies.relational import get_session_maker
from core_service.framework.dependencies.users import get_users_repository, get_users_sessions_repository
from core_service.shared.settings.application import app_settings

logger = logging.getLogger(__name__)


def get_auth_tokens_config() -> AuthTokensConfig:
    return AuthTokensConfig(
        jwt_secret_key=app_settings.JWT_SECRET_KEY,
        access_token_expiration_seconds=app_settings.ACCESS_TOKEN_EXPIRATION_SECONDS,
        refresh_token_expiration_seconds=app_settings.REFRESH_TOKEN_EXPIRATION_SECONDS,
    )


async def get_access_token_claims(
    request: Request, tokens_config: Annotated[AuthTokensConfig, Depends(get_auth_tokens_config)]
) -> AccessTokenClaims | None:
    access_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if access_token is None:
        return None

    try:
        return decode_access_token(access_token, tokens_config.jwt_secret_key, JWT_ALGORITHM)
    except InvalidAccessToken:
        logger.warning("Request with invalid or expired access token!")
        return None


async def get_caller(claims: Annotated[AccessTokenClaims | None, Depends(get_access_token_claims)]) -> Caller:
    if claims is None:
        return Caller(user_id=None)

    return Caller(user_id=claims.user_id, is_admin=claims.is_admin)


def get_log_user(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    sessions_repo: Annotated[UsersSessionsRepository, Depends(get_users_sessions_repository)],
    tokens_config: Annotated[AuthTokensConfig, Depends(get_auth_tokens_config)],
) -> LogUser:
    return LogUser(session_maker, users_repo, sessions_repo, tokens_config)


def get_logout_user(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    sessions_repo: Annotated[UsersSessionsRepository, Depends(get_users_sessions_repository)],
) -> LogoutUser:
    return LogoutUser(session_maker, sessions_repo)


def get_refresh_tokens(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    sessions_repo: Annotated[UsersSessionsRepository, Depends(get_users_sessions_repository)],
    tokens_config: Annotated[AuthTokensConfig, Depends(get_auth_tokens_config)],
) -> RefreshTokens:
    return RefreshTokens(session_maker, users_repo, sessions_repo, tokens_config)
