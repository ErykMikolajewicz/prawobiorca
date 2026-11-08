from contextlib import AbstractAsyncContextManager
from typing import Protocol


class AsyncSession(Protocol):
    """Object of database session. Use to share session between repositories.
    Otherwise, use only when you want rollback session, without raising exception."""

    async def rollback(self) -> None: ...

    """Rollback current transaction.
    After rollback you can only make selects. To make other queries start new transaction with SessionMaker."""


class SessionMaker(Protocol):
    def begin(self) -> AbstractAsyncContextManager[AsyncSession]: ...

    """Start transaction, user for insert, update, delete."""

    def __call__(self) -> AbstractAsyncContextManager[AsyncSession]: ...

    """Start connection, use when do not want to make transaction - practically for selects."""
