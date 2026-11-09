from core_service.application.ports.users import UsersRepository, UsersSessionsRepository
from core_service.infrastructure.relational_db.repositories.users import (
    SqlaUsersRepository,
    SqlaUsersSessionsRepository,
)


async def get_users_sessions_repository() -> UsersSessionsRepository:
    return SqlaUsersSessionsRepository()


async def get_users_repository() -> UsersRepository:
    return SqlaUsersRepository()
