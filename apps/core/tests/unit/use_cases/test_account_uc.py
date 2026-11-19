from unittest.mock import ANY

import pytest
from pydantic import SecretStr

from core_service.application.dtos.account import RegistrationData
from core_service.application.use_cases.account import CreateAccount
from core_service.domain.exceptions.limits import TooManyAttempts
from core_service.domain.exceptions.users import UserExists
from core_service.domain.services.attempts import get_registration_attempts_key
from core_service.domain.services.security import verify_password
from core_service.shared.exceptions import ObjectExists
from tests.consts import IP_ADDRESS, STRONG_PASSWORD, VALID_USERNAME
from tests.mocks import get_awaited_argument

REGISTRATION_DATA = RegistrationData(username=VALID_USERNAME, password=SecretStr(STRONG_PASSWORD))


@pytest.fixture
def create_account(mock_session_maker, mock_users_repo, mock_attempt_limiter):
    return CreateAccount(
        session_maker=mock_session_maker,
        users_repo=mock_users_repo,
        registration_attempt_limiter=mock_attempt_limiter,
    )


async def test_create_account_stores_hashed_password(create_account, mock_users_repo):
    await create_account.execute(REGISTRATION_DATA, IP_ADDRESS)

    user_data = get_awaited_argument(mock_users_repo.add, "create_data")
    assert user_data.username == VALID_USERNAME
    assert verify_password(SecretStr(STRONG_PASSWORD), user_data.hashed_password)


async def test_create_account_with_taken_username(create_account, mock_users_repo):
    mock_users_repo.add.side_effect = ObjectExists("User exists")

    with pytest.raises(UserExists):
        await create_account.execute(REGISTRATION_DATA, IP_ADDRESS)


async def test_create_account_records_attempt(create_account, mock_attempt_limiter):
    await create_account.execute(REGISTRATION_DATA, IP_ADDRESS)

    attempts_key = get_registration_attempts_key(IP_ADDRESS)
    mock_attempt_limiter.acquire.assert_awaited_once_with(ANY, attempts_key)


async def test_create_account_with_too_many_attempts(create_account, mock_users_repo, mock_attempt_limiter):
    mock_attempt_limiter.acquire.side_effect = TooManyAttempts(60)

    with pytest.raises(TooManyAttempts):
        await create_account.execute(REGISTRATION_DATA, IP_ADDRESS)

    mock_users_repo.add.assert_not_awaited()
