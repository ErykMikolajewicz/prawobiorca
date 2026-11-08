from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from taskiq import TaskiqMessage
from taskiq.receiver import Receiver

from core_service.framework.workers.applications import (
    generate_application_task,
    generate_application_template_description_task,
)
from core_service.framework.workers.regulations import generate_regulation_description_task, prepare_regulation_task
from core_service.infrastructure.relational_db.connection import DatabaseSessionMaker
from core_service.infrastructure.relational_db.schemas.tasks import task_messages_table
from core_service.infrastructure.tasks.broker import PostgresBroker
from core_service.shared.consts import DELIVERY_ATTEMPT_LABEL, TASK_HEARTBEAT_SECONDS

WORKER_TASKS = {
    task.task_name: task
    for task in (
        prepare_regulation_task,
        generate_regulation_description_task,
        generate_application_task,
        generate_application_template_description_task,
    )
}


def create_broker(postgres_container, session_maker, heartbeat_seconds: float = TASK_HEARTBEAT_SECONDS):
    listen_dsn = make_url(postgres_container.get_connection_url()).set(drivername="postgresql")
    return PostgresBroker(
        session_maker=DatabaseSessionMaker(session_maker),
        listen_dsn=listen_dsn.render_as_string(hide_password=False),
        heartbeat_seconds=heartbeat_seconds,
    )


@asynccontextmanager
async def start_worker_broker(
    postgres_container, session_maker, heartbeat_seconds: float = TASK_HEARTBEAT_SECONDS
) -> AsyncGenerator[PostgresBroker]:
    broker = create_broker(postgres_container, session_maker, heartbeat_seconds)
    broker.is_worker_process = True
    await broker.startup()
    try:
        yield broker
    finally:
        await broker.shutdown()


@pytest.fixture(scope="session")
def broker(postgres_container, session_maker) -> PostgresBroker:
    return create_broker(postgres_container, session_maker)


@pytest.fixture
async def task_broker(postgres_container, session_maker) -> AsyncGenerator[PostgresBroker]:
    async with start_worker_broker(postgres_container, session_maker) as broker:
        yield broker


async def get_scheduled_tasks(session_maker) -> list[TaskiqMessage]:
    async with session_maker() as session:
        messages = await session.scalars(select(task_messages_table.c.message).order_by(task_messages_table.c.id))
    return [TaskiqMessage.model_validate_json(message) for message in messages]


async def get_scheduled_task_names(session_maker) -> list[str]:
    return [task.task_name for task in await get_scheduled_tasks(session_maker)]


async def execute_task(broker: PostgresBroker, task: TaskiqMessage, delivery_attempt: int = 1) -> None:
    """Execute a scheduled task like the worker does, with the dependencies overridden in `broker`."""
    task.labels[DELIVERY_ATTEMPT_LABEL] = delivery_attempt

    result = await Receiver(broker).run_task(WORKER_TASKS[task.task_name].original_func, task)

    if result.error is not None:
        raise result.error
