import asyncio

import pytest
from sqlalchemy import func, select, update
from taskiq import TaskiqMessage

from src.infrastructure.relational_db.schemas.tasks import task_messages_table
from src.infrastructure.tasks.broker import insert_task_message
from src.shared.consts import DELIVERY_ATTEMPT_LABEL

LISTEN_TIMEOUT = 3


def make_broker_message(broker, *args):
    message = TaskiqMessage(task_id="task-id", task_name="task", labels={}, args=list(args), kwargs={})
    return broker.formatter.dumps(message)


async def count_task_messages(session_maker) -> int:
    async with session_maker() as session:
        return await session.scalar(select(func.count()).select_from(task_messages_table))


async def test_kicked_message_is_delivered_and_deleted_on_ack(task_broker, session_maker, clean_task_messages):
    await task_broker.kick(make_broker_message(task_broker, "argument"))

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)
    taskiq_message = task_broker.formatter.loads(delivered.data)

    assert taskiq_message.args == ["argument"]
    assert taskiq_message.labels[DELIVERY_ATTEMPT_LABEL] == 1

    await delivered.ack()

    assert await count_task_messages(session_maker) == 0


async def test_message_is_not_enqueued_on_rollback(task_broker, session_maker, clean_task_messages):
    async with session_maker() as session:
        await insert_task_message(session, make_broker_message(task_broker))
        await session.rollback()

    assert await count_task_messages(session_maker) == 0


async def test_locked_message_is_not_delivered(task_broker, clean_task_messages):
    await task_broker.kick(make_broker_message(task_broker))
    await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(anext(task_broker.listen()), 1)


async def test_message_with_expired_lease_is_delivered_again(task_broker, session_maker, clean_task_messages):
    await task_broker.kick(make_broker_message(task_broker))
    await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    async with session_maker.begin() as session:
        await session.execute(update(task_messages_table).values(locked_until=func.now()))

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker.formatter.loads(delivered.data).labels[DELIVERY_ATTEMPT_LABEL] == 2
