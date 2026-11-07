import pytest
from pydantic import SecretStr
from sqlalchemy import delete, insert

from src.domain.services.security import hash_password
from src.infrastructure.relational_db.schemas.users import users_table
from tests.consts import ADMIN_ID, ADMIN_USERNAME, STRONG_PASSWORD, USER_ID, VALID_USERNAME


@pytest.fixture
async def set_user(session_maker):
    password = SecretStr(STRONG_PASSWORD)
    hashed_password = hash_password(password)

    async with session_maker.begin() as session:
        statement = insert(users_table).values(id=USER_ID, username=VALID_USERNAME, hashed_password=hashed_password)
        await session.execute(statement)


@pytest.fixture
async def clean_user(session_maker):
    yield
    async with session_maker.begin() as session:
        statement = delete(users_table).where(users_table.c.username == VALID_USERNAME)
        await session.execute(statement)


@pytest.fixture
async def set_admin_user(session_maker):
    password = SecretStr(STRONG_PASSWORD)
    hashed_password = hash_password(password)

    async with session_maker.begin() as session:
        statement = insert(users_table).values(
            id=ADMIN_ID, username=ADMIN_USERNAME, hashed_password=hashed_password, is_admin=True
        )
        await session.execute(statement)


@pytest.fixture
async def clean_admin_user(session_maker):
    yield
    async with session_maker.begin() as session:
        statement = delete(users_table).where(users_table.c.username == ADMIN_USERNAME)
        await session.execute(statement)
