from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from core_service.application.dtos.account import LoginData
from core_service.application.use_cases.auth import LogoutUser, LogUser, RefreshTokens
from core_service.domain.entities.user import User
from core_service.domain.exceptions.users import InvalidRefreshToken, UserCantLog
from core_service.domain.services.security import decode_access_token, hash_password, hash_refresh_token
from core_service.domain.value_objects.auth import UserSession
from core_service.domain.value_objects.users import UserPrivileges
from core_service.shared.consts import JWT_ALGORITHM
from tests.consts import AUTH_TOKENS_CONFIG, REFRESH_TOKEN, SESSION_ID, STRONG_PASSWORD, USER_ID, VALID_USERNAME
from tests.mocks import get_awaited_argument

STORED_USER = User(id=USER_ID, username=VALID_USERNAME, hashed_password=hash_password(SecretStr(STRONG_PASSWORD)))


def decode(access_token: str):
    return decode_access_token(access_token, AUTH_TOKENS_CONFIG.jwt_secret_key, JWT_ALGORITHM)


@pytest.fixture
def users_repository(mock_users_repo):
    mock_users_repo.get_by_username.return_value = STORED_USER
    mock_users_repo.get_user_privileges.return_value = UserPrivileges(is_admin=True)
    return mock_users_repo


@pytest.fixture
def sessions_repository(mock_sessions_repo):
    mock_sessions_repo.create_session.return_value = SESSION_ID
    mock_sessions_repo.rotate_session.return_value = UserSession(id=SESSION_ID, user_id=USER_ID)
    return mock_sessions_repo


@pytest.fixture
def mock_prevent_timing_attack():
    with patch(
        "core_service.application.use_cases.auth.prevent_timing_attack", new_callable=AsyncMock
    ) as prevent_timing_attack:
        yield prevent_timing_attack


@pytest.fixture
def log_user(mock_session_maker, users_repository, sessions_repository):
    return LogUser(
        session_maker=mock_session_maker,
        users_repo=users_repository,
        sessions_repo=sessions_repository,
        tokens_config=AUTH_TOKENS_CONFIG,
    )


@pytest.fixture
def refresh_tokens(mock_session_maker, users_repository, sessions_repository):
    return RefreshTokens(
        session_maker=mock_session_maker,
        users_repo=users_repository,
        sessions_repo=sessions_repository,
        tokens_config=AUTH_TOKENS_CONFIG,
    )


@pytest.fixture
def logout_user(mock_session_maker, sessions_repository):
    return LogoutUser(session_maker=mock_session_maker, sessions_repo=sessions_repository)


async def test_log_user_creates_session(log_user, sessions_repository):
    tokens = await log_user.execute(LoginData(username=VALID_USERNAME, password=SecretStr(STRONG_PASSWORD)))

    claims = decode(tokens.access_token)
    assert (claims.user_id, claims.session_id, claims.is_admin) == (USER_ID, SESSION_ID, True)
    stored_hash = get_awaited_argument(sessions_repository.create_session, "refresh_token_hash")
    assert stored_hash == hash_refresh_token(tokens.refresh_token)


@pytest.mark.parametrize(
    ("stored_user", "password"),
    [(None, STRONG_PASSWORD), (STORED_USER, "WrongPassword123!")],
    ids=("unknown user", "wrong password"),
)
async def test_log_user_rejected(
    log_user, users_repository, sessions_repository, mock_prevent_timing_attack, stored_user, password
):
    users_repository.get_by_username.return_value = stored_user

    with pytest.raises(UserCantLog):
        await log_user.execute(LoginData(username=VALID_USERNAME, password=SecretStr(password)))

    mock_prevent_timing_attack.assert_awaited_once()
    sessions_repository.create_session.assert_not_awaited()


async def test_refresh_tokens_rotates_session(refresh_tokens, users_repository, sessions_repository):
    users_repository.get_user_privileges.return_value = UserPrivileges(is_admin=False)

    tokens = await refresh_tokens.execute(REFRESH_TOKEN)

    claims = decode(tokens.access_token)
    assert (claims.user_id, claims.session_id, claims.is_admin) == (USER_ID, SESSION_ID, False)
    assert tokens.refresh_token != REFRESH_TOKEN
    rotate_session = sessions_repository.rotate_session
    assert get_awaited_argument(rotate_session, "old_refresh_token_hash") == hash_refresh_token(REFRESH_TOKEN)
    assert get_awaited_argument(rotate_session, "new_refresh_token_hash") == hash_refresh_token(tokens.refresh_token)


@pytest.mark.parametrize(
    ("user_session", "privileges"),
    [(None, UserPrivileges(is_admin=False)), (UserSession(id=SESSION_ID, user_id=USER_ID), None)],
    ids=("unknown token", "user without privileges"),
)
async def test_refresh_tokens_rejected(refresh_tokens, users_repository, sessions_repository, user_session, privileges):
    sessions_repository.rotate_session.return_value = user_session
    users_repository.get_user_privileges.return_value = privileges

    with pytest.raises(InvalidRefreshToken):
        await refresh_tokens.execute(REFRESH_TOKEN)


async def test_logout_user_by_session_id(logout_user, sessions_repository):
    await logout_user.execute(SESSION_ID, REFRESH_TOKEN)

    assert get_awaited_argument(sessions_repository.delete_session, "session_id") == SESSION_ID
    sessions_repository.delete_session_by_refresh_token_hash.assert_not_awaited()


async def test_logout_user_by_refresh_token(logout_user, sessions_repository):
    await logout_user.execute(None, REFRESH_TOKEN)

    delete_session_by_hash = sessions_repository.delete_session_by_refresh_token_hash
    assert get_awaited_argument(delete_session_by_hash, "refresh_token_hash") == hash_refresh_token(REFRESH_TOKEN)
    sessions_repository.delete_session.assert_not_awaited()


async def test_logout_user_without_credentials(logout_user, sessions_repository):
    await logout_user.execute(None, None)

    sessions_repository.delete_session.assert_not_awaited()
    sessions_repository.delete_session_by_refresh_token_hash.assert_not_awaited()
