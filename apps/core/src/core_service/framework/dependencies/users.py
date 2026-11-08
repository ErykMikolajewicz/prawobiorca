import core_service.infrastructure.relational_db.repositories.users as sqla_repos
from core_service.application.interfaces.users import UsersRepository, UsersSessionsRepository


async def get_users_sessions_repository() -> UsersSessionsRepository:
    return sqla_repos.UsersSessionsRepository()


async def get_users_repository() -> UsersRepository:
    return sqla_repos.UsersRepository()
