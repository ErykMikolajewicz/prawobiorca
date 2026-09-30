import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.app.dtos.account import LoginData
from src.app.dtos.auth import AuthTokens
from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.users import UsersRepository, UsersSessionsRepository
from src.app.services.accounts import check_user_can_log
from src.domain.exceptions.users import InvalidRefreshToken, UserCantLog
from src.domain.services.security import (
    create_access_token,
    generate_authorization_token,
    hash_refresh_token,
    prevent_timing_attack,
)
from src.domain.value_objects.auth import AccessTokenClaims
from src.shared.consts import JWT_ALGORITHM
from src.shared.settings.application import app_settings

logger = logging.getLogger(__name__)

jwt_secret_key = app_settings.JWT_SECRET_KEY
access_token_expiration_seconds = app_settings.ACCESS_TOKEN_EXPIRATION_SECONDS
refresh_token_expiration_seconds = app_settings.REFRESH_TOKEN_EXPIRATION_SECONDS


def build_auth_tokens(claims: AccessTokenClaims, refresh_token: str) -> AuthTokens:
    access_token = create_access_token(claims, jwt_secret_key, JWT_ALGORITHM, access_token_expiration_seconds)

    return AuthTokens(
        access_token=access_token,
        access_expires_in=access_token_expiration_seconds,
        refresh_token=refresh_token,
        refresh_expires_in=refresh_token_expiration_seconds,
    )


def build_refresh_token_validity() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=refresh_token_expiration_seconds)


@dataclass
class LogUser:
    session_maker: SessionMaker
    users_repo: UsersRepository
    sessions_repo: UsersSessionsRepository

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
                session, user_id, hash_refresh_token(refresh_token), build_refresh_token_validity()
            )

        claims = AccessTokenClaims(user_id=user_id, session_id=session_id, is_admin=user_privileges.is_admin)

        return build_auth_tokens(claims, refresh_token)


@dataclass
class RefreshTokens:
    session_maker: SessionMaker
    users_repo: UsersRepository
    sessions_repo: UsersSessionsRepository

    async def execute(self, refresh_token: str) -> AuthTokens:
        new_refresh_token = generate_authorization_token()

        async with self.session_maker.begin() as session:
            user_session = await self.sessions_repo.rotate_session(
                session,
                hash_refresh_token(refresh_token),
                hash_refresh_token(new_refresh_token),
                build_refresh_token_validity(),
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

        return build_auth_tokens(claims, new_refresh_token)


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
            else:
                await self.sessions_repo.delete_session_by_refresh_token_hash(
                    session, hash_refresh_token(refresh_token)
                )
