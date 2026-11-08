import logging
from dataclasses import dataclass

from fastapi.concurrency import run_in_threadpool

from src.app.dtos.account import LoginData
from src.app.dtos.user import CreateUserData
from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.users import UsersRepository
from src.domain.exceptions.users import UserExists
from src.domain.services.security import hash_password
from src.shared.exceptions import ObjectExists

logger = logging.getLogger(__name__)


@dataclass
class CreateAccount:
    session_maker: SessionMaker
    users_repo: UsersRepository

    async def execute(self, login_data: LoginData):
        hashed_password = await run_in_threadpool(hash_password, login_data.password)
        create_user_data = CreateUserData(login_data.username, hashed_password)

        async with self.session_maker.begin() as session:
            try:
                await self.users_repo.add(session, create_user_data)
            except ObjectExists:
                logger.warning("Can not add user, user with that username already exists!")
                raise UserExists
