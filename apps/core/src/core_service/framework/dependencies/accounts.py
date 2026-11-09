from typing import Annotated

from fastapi import Depends

from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.users import UsersRepository
from core_service.application.use_cases.account import CreateAccount
from core_service.framework.dependencies.relational import get_session_maker
from core_service.framework.dependencies.users import get_users_repository


def get_create_account(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
) -> CreateAccount:
    return CreateAccount(session_maker, users_repo)
