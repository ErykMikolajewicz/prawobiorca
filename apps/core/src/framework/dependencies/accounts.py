from typing import Annotated

from fastapi import Depends

from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.users import UsersRepository
from src.app.use_cases.account import CreateAccount
from src.framework.dependencies.relational import get_session_maker
from src.framework.dependencies.users import get_users_repository


def get_create_account(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    users_repo: Annotated[UsersRepository, Depends(get_users_repository)],
) -> CreateAccount:
    return CreateAccount(session_maker, users_repo)
