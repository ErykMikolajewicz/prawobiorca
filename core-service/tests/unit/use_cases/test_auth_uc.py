from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import SecretStr

from src.app.dtos.account import LoginData
from src.app.dtos.auth import AuthTokens
from src.app.use_cases.auth import LogoutUser, LogUser, RefreshTokens
from src.domain.exceptions.users import InvalidRefreshToken, UserCantLog
from src.domain.services.security import decode_access_token, hash_refresh_token
from src.domain.value_objects.auth import UserSession
from src.domain.value_objects.users import UserPrivileges
from src.shared.consts import JWT_ALGORITHM
from src.shared.settings.application import app_settings
from tests.consts import REFRESH_TOKEN, SESSION_ID, UNKNOWN_REFRESH_TOKEN, VALID_USERNAME


def decode(access_token: str):
    return decode_access_token(access_token, app_settings.JWT_SECRET_KEY, JWT_ALGORITHM)


async def test_log_user_success(
    mock_opened_session,
    mock_session_maker,
    mock_users_repo,
    mock_sessions_repo,
    uuid_generator,
):
    login_data = LoginData(username=VALID_USERNAME, password=SecretStr("Password123!"))
    user_id = next(uuid_generator)
    mock_users_repo.get_user_privileges.return_value = UserPrivileges(is_admin=True)
    mock_sessions_repo.create_session.return_value = SESSION_ID

    with (
        patch("src.app.use_cases.auth.check_user_can_log", new_callable=AsyncMock) as mock_check,
        patch("src.app.use_cases.auth.generate_authorization_token") as mock_gen_token,
        patch("src.app.use_cases.auth.prevent_timing_attack", new_callable=AsyncMock) as mock_prevent,
    ):
        mock_check.return_value = user_id
        mock_gen_token.return_value = REFRESH_TOKEN

        use_case = LogUser(
            session_maker=mock_session_maker, users_repo=mock_users_repo, sessions_repo=mock_sessions_repo
        )

        result = await use_case.execute(login_data)

        mock_check.assert_called_once_with(mock_opened_session, mock_users_repo, login_data)
        mock_prevent.assert_not_called()
        mock_gen_token.assert_called_once()

        mock_sessions_repo.create_session.assert_called_once()
        call_args = mock_sessions_repo.create_session.call_args
        assert call_args[0][1] == user_id
        assert call_args[0][2] == hash_refresh_token(REFRESH_TOKEN)
        assert isinstance(call_args[0][3], datetime)
        assert call_args[0][3].tzinfo == UTC

        assert isinstance(result, AuthTokens)
        assert result.refresh_token == REFRESH_TOKEN
        assert result.access_expires_in > 0
        assert result.refresh_expires_in > 0

        claims = decode(result.access_token)
        assert claims.user_id == user_id
        assert claims.session_id == SESSION_ID
        assert claims.is_admin is True


async def test_log_user_failure(
    mock_opened_session,
    mock_session_maker,
    mock_users_repo,
    mock_sessions_repo,
):
    login_data = LoginData(username=VALID_USERNAME, password=SecretStr("WrongPassword123!"))

    with (
        patch("src.app.use_cases.auth.check_user_can_log", new_callable=AsyncMock) as mock_check,
        patch("src.app.use_cases.auth.generate_authorization_token") as mock_gen_token,
        patch("src.app.use_cases.auth.prevent_timing_attack", new_callable=AsyncMock) as mock_prevent,
        patch("src.app.use_cases.auth.asyncio.get_event_loop") as mock_loop,
    ):
        mock_check.return_value = None
        fake_time = 12345.6
        mock_loop.return_value.time.return_value = fake_time

        use_case = LogUser(
            session_maker=mock_session_maker, users_repo=mock_users_repo, sessions_repo=mock_sessions_repo
        )

        with pytest.raises(UserCantLog):
            await use_case.execute(login_data)

        mock_check.assert_called_once_with(mock_opened_session, mock_users_repo, login_data)
        mock_prevent.assert_called_once_with(fake_time)
        mock_gen_token.assert_not_called()
        mock_sessions_repo.create_session.assert_not_called()


async def test_refresh_tokens_rotates_session(
    mock_opened_session,
    mock_session_maker,
    mock_users_repo,
    mock_sessions_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    mock_sessions_repo.rotate_session.return_value = UserSession(id=SESSION_ID, user_id=user_id)
    mock_users_repo.get_user_privileges.return_value = UserPrivileges(is_admin=False)

    use_case = RefreshTokens(
        session_maker=mock_session_maker, users_repo=mock_users_repo, sessions_repo=mock_sessions_repo
    )

    result = await use_case.execute(REFRESH_TOKEN)

    mock_sessions_repo.rotate_session.assert_called_once()
    call_args = mock_sessions_repo.rotate_session.call_args
    assert call_args[0][0] == mock_opened_session
    assert call_args[0][1] == hash_refresh_token(REFRESH_TOKEN)
    assert call_args[0][2] == hash_refresh_token(result.refresh_token)
    assert result.refresh_token != REFRESH_TOKEN

    claims = decode(result.access_token)
    assert claims.user_id == user_id
    assert claims.session_id == SESSION_ID
    assert claims.is_admin is False


async def test_refresh_tokens_with_unknown_token(
    mock_session_maker,
    mock_users_repo,
    mock_sessions_repo,
):
    mock_sessions_repo.rotate_session.return_value = None

    use_case = RefreshTokens(
        session_maker=mock_session_maker, users_repo=mock_users_repo, sessions_repo=mock_sessions_repo
    )

    with pytest.raises(InvalidRefreshToken):
        await use_case.execute(UNKNOWN_REFRESH_TOKEN)

    mock_users_repo.get_user_privileges.assert_not_called()


async def test_refresh_tokens_without_user_privileges(
    mock_session_maker,
    mock_users_repo,
    mock_sessions_repo,
    uuid_generator,
):
    mock_sessions_repo.rotate_session.return_value = UserSession(id=SESSION_ID, user_id=next(uuid_generator))
    mock_users_repo.get_user_privileges.return_value = None

    use_case = RefreshTokens(
        session_maker=mock_session_maker, users_repo=mock_users_repo, sessions_repo=mock_sessions_repo
    )

    with pytest.raises(InvalidRefreshToken):
        await use_case.execute(REFRESH_TOKEN)


async def test_logout_user_by_session_id(mock_opened_session, mock_session_maker, mock_sessions_repo):
    use_case = LogoutUser(session_maker=mock_session_maker, sessions_repo=mock_sessions_repo)

    await use_case.execute(SESSION_ID, REFRESH_TOKEN)

    mock_sessions_repo.delete_session.assert_called_once_with(mock_opened_session, SESSION_ID)
    mock_sessions_repo.delete_session_by_refresh_token_hash.assert_not_called()


async def test_logout_user_by_refresh_token(mock_opened_session, mock_session_maker, mock_sessions_repo):
    use_case = LogoutUser(session_maker=mock_session_maker, sessions_repo=mock_sessions_repo)

    await use_case.execute(None, REFRESH_TOKEN)

    mock_sessions_repo.delete_session_by_refresh_token_hash.assert_called_once_with(
        mock_opened_session, hash_refresh_token(REFRESH_TOKEN)
    )
    mock_sessions_repo.delete_session.assert_not_called()


async def test_logout_user_without_credentials(mock_session_maker, mock_sessions_repo):
    use_case = LogoutUser(session_maker=mock_session_maker, sessions_repo=mock_sessions_repo)

    await use_case.execute(None, None)

    mock_sessions_repo.delete_session.assert_not_called()
    mock_sessions_repo.delete_session_by_refresh_token_hash.assert_not_called()
