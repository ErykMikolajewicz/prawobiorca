import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import SecretStr

from core_service.application.dtos.account import LoginData
from core_service.application.dtos.auth import AuthTokens
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.users import UsersRepository, UsersSessionsRepository
from core_service.application.services.accounts import check_user_can_log
from core_service.domain.exceptions.users import InvalidRefreshToken, UserCantLog
from core_service.domain.services.security import (
    JWT_ALGORITHM,
    create_access_token,
    generate_authorization_token,
    hash_refresh_token,
    prevent_timing_attack,
)
from core_service.domain.value_objects.auth import AccessTokenClaims

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthTokensConfig:
    jwt_secret_key: SecretStr
    access_token_expiration_seconds: int
    refresh_token_expiration_seconds: int


def build_auth_tokens(claims: AccessTokenClaims, refresh_token: str, config: AuthTokensConfig) -> AuthTokens:
    access_token = create_access_token(
        claims, config.jwt_secret_key, JWT_ALGORITHM, config.access_token_expiration_seconds
    )

    return AuthTokens(
        access_token=access_token,
        access_expires_in=config.access_token_expiration_seconds,
        refresh_token=refresh_token,
        refresh_expires_in=config.refresh_token_expiration_seconds,
    )


def build_refresh_token_validity(config: AuthTokensConfig) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=config.refresh_token_expiration_seconds)


@dataclass
class LogUser:
    session_maker: SessionMaker
    users_repo: UsersRepository
    sessions_repo: UsersSessionsRepository
    tokens_config: AuthTokensConfig

    async def execute(self, login_data: LoginData) -> AuthTokens:
        execution_start_time = asyncio.get_event_loop().time()

        user_privileges = None
        async with self.session_maker() as session:
            user_id = await check_user_can_log(session, self.users_repo, login_data)
            if user_id is not None:
                user_privileges = await self.users_repo.get_user_privileges(session, user_id)
        if user_id is None or user_privileges is None:
            await prevent_timing_attack(execution_start_time)
            raise UserCantLog

        refresh_token = generate_authorization_token()

        async with self.session_maker.begin() as session:
            session_id = await self.sessions_repo.create_session(
                session, user_id, hash_refresh_token(refresh_token), build_refresh_token_validity(self.tokens_config)
            )

        claims = AccessTokenClaims(user_id=user_id, session_id=session_id, is_admin=user_privileges.is_admin)

        return build_auth_tokens(claims, refresh_token, self.tokens_config)


@dataclass
class RefreshTokens:
    session_maker: SessionMaker
    users_repo: UsersRepository
    sessions_repo: UsersSessionsRepository
    tokens_config: AuthTokensConfig

    async def execute(self, refresh_token: str) -> AuthTokens:
        new_refresh_token = generate_authorization_token()

        async with self.session_maker.begin() as session:
            user_session = await self.sessions_repo.rotate_session(
                session,
                hash_refresh_token(refresh_token),
                hash_refresh_token(new_refresh_token),
                build_refresh_token_validity(self.tokens_config),
            )
            if user_session is None:
                logger.warning("Refresh attempt with unknown or expired token!")
                raise InvalidRefreshToken

            user_privileges = await self.users_repo.get_user_privileges(session, user_session.user_id)
            if user_privileges is None:
                logger.error("Privileges for user %s not found!", user_session.user_id)
                raise InvalidRefreshToken

        claims = AccessTokenClaims(
            user_id=user_session.user_id, session_id=user_session.id, is_admin=user_privileges.is_admin
        )

        return build_auth_tokens(claims, new_refresh_token, self.tokens_config)


@dataclass
class LogoutUser:
    session_maker: SessionMaker
    sessions_repo: UsersSessionsRepository

    async def execute(self, session_id: UUID | None, refresh_token: str | None) -> None:
        if session_id is None and refresh_token is None:
            return

        async with self.session_maker.begin() as session:
            if session_id is not None:
                await self.sessions_repo.delete_session(session, session_id)
            elif refresh_token is not None:
                await self.sessions_repo.delete_session_by_refresh_token_hash(
                    session, hash_refresh_token(refresh_token)
                )
