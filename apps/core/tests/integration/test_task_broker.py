import asyncio
from unittest.mock import patch

import pytest
from sqlalchemy import func, select, update
from taskiq import TaskiqMessage

from core_service.infrastructure.relational_db.schemas.tasks import task_messages_table
from core_service.infrastructure.tasks.broker import DELAY_LABEL, DELIVERY_ATTEMPT_LABEL, insert_task_message
from core_service.shared.exceptions import ServiceUnavailable
from tests.integration.fixtures.tasks import start_worker_broker

LISTEN_TIMEOUT = 3

HEARTBEAT_SECONDS = 0.1

POLL_INTERVAL_SECONDS = 0.1


def make_broker_message(broker, *args, labels=None):
    message = TaskiqMessage(task_id="task-id", task_name="task", labels=labels or {}, args=list(args), kwargs={})
    return broker.formatter.dumps(message)


async def count_task_messages(session_maker) -> int:
    async with session_maker() as session:
        return await session.scalar(select(func.count()).select_from(task_messages_table))


async def get_locked_until(session_maker):
    async with session_maker() as session:
        return await session.scalar(select(task_messages_table.c.locked_until))


async def test_kicked_message_is_delivered_and_deleted_on_ack(task_broker, session_maker):
    await task_broker.kick(make_broker_message(task_broker, "argument"))

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)
    taskiq_message = task_broker.formatter.loads(delivered.data)

    assert taskiq_message.args == ["argument"]
    assert taskiq_message.labels[DELIVERY_ATTEMPT_LABEL] == 1

    await delivered.ack()

    assert await count_task_messages(session_maker) == 0


async def test_message_is_not_enqueued_on_rollback(task_broker, session_maker):
    async with session_maker() as session:
        await insert_task_message(session, make_broker_message(task_broker))
        await session.rollback()

    assert await count_task_messages(session_maker) == 0


async def test_locked_message_is_not_delivered(task_broker):
    await task_broker.kick(make_broker_message(task_broker))
    await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(anext(task_broker.listen()), 1)


async def test_message_with_expired_lease_is_delivered_again(task_broker, session_maker):
    await task_broker.kick(make_broker_message(task_broker))
    await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    async with session_maker.begin() as session:
        await session.execute(update(task_messages_table).values(locked_until=func.now()))

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker.formatter.loads(delivered.data).labels[DELIVERY_ATTEMPT_LABEL] == 2


async def test_heartbeat_extends_lease_of_message_in_progress(postgres_container, session_maker):
    async with start_worker_broker(postgres_container, session_maker, HEARTBEAT_SECONDS) as broker:
        await broker.kick(make_broker_message(broker))
        await asyncio.wait_for(anext(broker.listen()), LISTEN_TIMEOUT)
        claimed_until = await get_locked_until(session_maker)

        await asyncio.sleep(3 * HEARTBEAT_SECONDS)

        assert await get_locked_until(session_maker) > claimed_until


async def test_delayed_message_is_not_delivered_before_delay(task_broker):
    await task_broker.kick(make_broker_message(task_broker, labels={DELAY_LABEL: 60}))

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(anext(task_broker.listen()), 1)


async def test_delayed_message_is_delivered_after_delay(task_broker, session_maker):
    await task_broker.kick(make_broker_message(task_broker, labels={DELAY_LABEL: 60}))

    async with session_maker.begin() as session:
        await session.execute(update(task_messages_table).values(locked_until=func.now()))

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker.formatter.loads(delivered.data).labels[DELIVERY_ATTEMPT_LABEL] == 1


async def test_heartbeat_survives_unexpected_error(postgres_container, session_maker):
    async with start_worker_broker(postgres_container, session_maker, HEARTBEAT_SECONDS) as broker:
        await broker.kick(make_broker_message(broker))
        await asyncio.wait_for(anext(broker.listen()), LISTEN_TIMEOUT)
        claimed_until = await get_locked_until(session_maker)

        with patch.object(broker.session_maker, "begin", side_effect=RuntimeError):
            await asyncio.sleep(3 * HEARTBEAT_SECONDS)
        await asyncio.sleep(3 * HEARTBEAT_SECONDS)

        assert await get_locked_until(session_maker) > claimed_until


async def test_closed_listener_is_reconnected(task_broker):
    closed_connection = task_broker._listen_connection
    await closed_connection.close()

    await task_broker.kick(make_broker_message(task_broker))
    await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker._listen_connection is not closed_connection
    assert not task_broker._listen_connection.is_closed()


async def test_message_is_delivered_while_listener_can_not_connect(task_broker):
    await task_broker._listen_connection.close()
    await task_broker.kick(make_broker_message(task_broker, "argument"))

    with patch.object(task_broker, "_connect_listener", side_effect=OSError):
        delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker.formatter.loads(delivered.data).args == ["argument"]


async def test_message_is_claimed_again_after_database_is_unavailable(task_broker):
    await task_broker.kick(make_broker_message(task_broker, "argument"))
    claimed_message = await task_broker._claim_message()

    with (
        patch("core_service.infrastructure.tasks.broker.TASK_POLL_INTERVAL_SECONDS", POLL_INTERVAL_SECONDS),
        patch.object(task_broker, "_claim_message", side_effect=[ServiceUnavailable, claimed_message]),
    ):
        delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)

    assert task_broker.formatter.loads(delivered.data).args == ["argument"]
