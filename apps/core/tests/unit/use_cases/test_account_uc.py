import pytest
from pydantic import SecretStr

from src.app.dtos.account import LoginData
from src.app.use_cases.account import CreateAccount
from src.domain.exceptions.users import UserExists
from src.domain.services.security import verify_password
from src.shared.exceptions import ObjectExists
from tests.consts import STRONG_PASSWORD, VALID_USERNAME
from tests.mocks import get_awaited_argument

LOGIN_DATA = LoginData(username=VALID_USERNAME, password=SecretStr(STRONG_PASSWORD))


@pytest.fixture
def create_account(mock_session_maker, mock_users_repo):
    return CreateAccount(session_maker=mock_session_maker, users_repo=mock_users_repo)


async def test_create_account_stores_hashed_password(create_account, mock_users_repo):
    await create_account.execute(LOGIN_DATA)

    user_data = get_awaited_argument(mock_users_repo.add, "create_data")
    assert user_data.username == VALID_USERNAME
    assert verify_password(SecretStr(STRONG_PASSWORD), user_data.hashed_password)


async def test_create_account_with_taken_username(create_account, mock_users_repo):
    mock_users_repo.add.side_effect = ObjectExists("User exists")

    with pytest.raises(UserExists):
        await create_account.execute(LOGIN_DATA)
