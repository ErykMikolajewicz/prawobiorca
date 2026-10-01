import asyncio
import logging
from contextlib import suppress
from datetime import timedelta
from functools import partial
from typing import Any, AsyncGenerator

import asyncpg
from sqlalchemy import delete, func, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import AckableMessage, AsyncBroker, BrokerMessage

from src.infrastructure.relational_db.connection import DatabaseSessionMaker
from src.infrastructure.relational_db.schemas.tasks import task_messages_table
from src.shared.consts import (
    DELIVERY_ATTEMPT_LABEL,
    TASK_HEARTBEAT_SECONDS,
    TASK_LEASE_SECONDS,
    TASK_NOTIFY_CHANNEL,
    TASK_POLL_INTERVAL_SECONDS,
)
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


async def insert_task_message(session: AsyncSession, message: BrokerMessage) -> None:
    statement = insert(task_messages_table).values(message=message.message.decode()).returning(task_messages_table.c.id)
    result = await session.execute(statement)
    message_id = result.scalar_one()

    await session.execute(select(func.pg_notify(TASK_NOTIFY_CHANNEL, str(message_id))))


class PostgresBroker(AsyncBroker):
    def __init__(self, session_maker: DatabaseSessionMaker, listen_dsn: str):
        super().__init__()
        self.session_maker = session_maker
        self.listen_dsn = listen_dsn
        self._listen_connection: asyncpg.Connection | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._new_message_event = asyncio.Event()
        self._in_progress_ids: set[int] = set()

    async def startup(self) -> None:
        await super().startup()
        if self.is_worker_process:
            await self._connect_listener()
            self._heartbeat_task = asyncio.create_task(self._extend_leases())

    async def shutdown(self) -> None:
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._heartbeat_task
        if self._listen_connection is not None:
            await self._listen_connection.close()
        await super().shutdown()

    async def kick(self, message: BrokerMessage) -> None:
        async with self.session_maker.begin() as session:
            await insert_task_message(session, message)

    async def listen(self) -> AsyncGenerator[AckableMessage, None]:
        while True:
            if self._listen_connection.is_closed():
                try:
                    await self._connect_listener()
                except OSError, TimeoutError, asyncpg.PostgresError:
                    logger.error("Database unavailable, can not listen for task messages notifications!")

            self._new_message_event.clear()
            try:
                claimed_message = await self._claim_message()
            except ServiceUnavailable:
                logger.error("Database unavailable, can not claim task message!")
                claimed_message = None

            if claimed_message is None:
                with suppress(TimeoutError):
                    await asyncio.wait_for(self._new_message_event.wait(), TASK_POLL_INTERVAL_SECONDS)
                continue

            taskiq_message = self.formatter.loads(claimed_message.message.encode())
            taskiq_message.labels[DELIVERY_ATTEMPT_LABEL] = claimed_message.attempts

            self._in_progress_ids.add(claimed_message.id)
            yield AckableMessage(
                data=self.formatter.dumps(taskiq_message).message, ack=partial(self._ack, claimed_message.id)
            )

    async def _connect_listener(self) -> None:
        self._listen_connection = await asyncpg.connect(self.listen_dsn)
        await self._listen_connection.add_listener(TASK_NOTIFY_CHANNEL, self._on_notification)

    def _on_notification(self, *_: Any) -> None:
        self._new_message_event.set()

    async def _claim_message(self) -> Any:
        claimable_id = (
            select(task_messages_table.c.id)
            .where(
                or_(
                    task_messages_table.c.locked_until.is_(None),
                    task_messages_table.c.locked_until < func.now(),
                )
            )
            .order_by(task_messages_table.c.id)
            .limit(1)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )
        statement = (
            update(task_messages_table)
            .where(task_messages_table.c.id == claimable_id)
            .values(
                locked_until=func.now() + timedelta(seconds=TASK_LEASE_SECONDS),
                attempts=task_messages_table.c.attempts + 1,
            )
            .returning(task_messages_table.c.id, task_messages_table.c.message, task_messages_table.c.attempts)
        )
        async with self.session_maker.begin() as session:
            result = await session.execute(statement)
            return result.one_or_none()

    async def _extend_leases(self) -> None:
        while True:
            await asyncio.sleep(TASK_HEARTBEAT_SECONDS)
            if not self._in_progress_ids:
                continue

            statement = (
                update(task_messages_table)
                .where(task_messages_table.c.id.in_(list(self._in_progress_ids)))
                .values(locked_until=func.now() + timedelta(seconds=TASK_LEASE_SECONDS))
            )
            try:
                async with self.session_maker.begin() as session:
                    await session.execute(statement)
            except ServiceUnavailable:
                logger.error("Database unavailable, can not extend task messages leases!")

    async def _ack(self, message_id: int) -> None:
        statement = delete(task_messages_table).where(task_messages_table.c.id == message_id)
        try:
            async with self.session_maker.begin() as session:
                await session.execute(statement)
        finally:
            self._in_progress_ids.discard(message_id)
