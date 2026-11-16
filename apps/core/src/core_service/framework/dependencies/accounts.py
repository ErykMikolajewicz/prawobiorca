from typing import Annotated

from fastapi import Depends

from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.users import UsersRepository
from core_service.application.services.attempts import AttemptLimiter
from core_service.application.use_cases.account import CreateAccount
from core_service.framework.dependencies.attempts import get_registration_attempt_limiter
from core_service.framework.dependencies.relational import get_session_maker
from core_service.framework.dependencies.users import get_users_repository


def get_create_account(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
    registration_attempt_limiter: Annotated[AttemptLimiter, Depends(get_registration_attempt_limiter)],
) -> CreateAccount:
    return CreateAccount(session_maker, users_repo, registration_attempt_limiter)
