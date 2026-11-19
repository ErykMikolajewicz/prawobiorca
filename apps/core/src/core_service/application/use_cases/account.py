import logging
from dataclasses import dataclass

from fastapi.concurrency import run_in_threadpool

from core_service.application.dtos.account import RegistrationData
from core_service.application.dtos.user import CreateUserData
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.users import UsersRepository
from core_service.application.services.attempts import AttemptLimiter
from core_service.domain.exceptions.users import UserExists
from core_service.domain.services.attempts import get_registration_attempts_key
from core_service.domain.services.security import hash_password
from core_service.shared.exceptions import ObjectExists

logger = logging.getLogger(__name__)


@dataclass
class CreateAccount:
    session_maker: SessionMaker
    users_repo: UsersRepository
    registration_attempt_limiter: AttemptLimiter

    async def execute(self, registration_data: RegistrationData, ip_address: str) -> None:
        attempts_key = get_registration_attempts_key(ip_address)
        async with self.session_maker.begin() as session:
            await self.registration_attempt_limiter.acquire(session, attempts_key)

        hashed_password = await run_in_threadpool(hash_password, registration_data.password)
        create_user_data = CreateUserData(registration_data.username, hashed_password)

        async with self.session_maker.begin() as session:
            try:
                await self.users_repo.add(session, create_user_data)
            except ObjectExists:
                logger.warning("Can not add user, user with that username already exists!")
                raise UserExists
