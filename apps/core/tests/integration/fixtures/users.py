import pytest
from pydantic import SecretStr
from sqlalchemy import insert

from core_service.domain.services.security import hash_password
from core_service.infrastructure.relational_db.schemas.users import users_table
from tests.consts import ADMIN_ID, ADMIN_USERNAME, STRONG_PASSWORD, USER_ID, VALID_USERNAME


@pytest.fixture(scope="session")
def hashed_password() -> bytes:
    return hash_password(SecretStr(STRONG_PASSWORD))


@pytest.fixture
async def user(session_maker, hashed_password) -> None:
    async with session_maker.begin() as session:
        await session.execute(
            insert(users_table).values(id=USER_ID, username=VALID_USERNAME, hashed_password=hashed_password)
        )


@pytest.fixture
async def admin(session_maker, hashed_password) -> None:
    async with session_maker.begin() as session:
        await session.execute(
            insert(users_table).values(
                id=ADMIN_ID, username=ADMIN_USERNAME, hashed_password=hashed_password, is_admin=True
            )
        )
