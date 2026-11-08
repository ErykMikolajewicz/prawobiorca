from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from taskiq import TaskiqMessage

from src.infrastructure.relational_db.connection import DatabaseSessionMaker
from src.infrastructure.relational_db.schemas.tasks import task_messages_table
from src.infrastructure.tasks.broker import PostgresBroker


def create_broker(postgres_container, session_maker) -> PostgresBroker:
    listen_dsn = make_url(postgres_container.get_connection_url()).set(drivername="postgresql")
    return PostgresBroker(
        session_maker=DatabaseSessionMaker(session_maker),
        listen_dsn=listen_dsn.render_as_string(hide_password=False),
    )


@pytest.fixture(scope="session")
def broker(postgres_container, session_maker) -> PostgresBroker:
    return create_broker(postgres_container, session_maker)


@pytest.fixture
async def task_broker(postgres_container, session_maker) -> AsyncGenerator[PostgresBroker]:
    broker = create_broker(postgres_container, session_maker)
    broker.is_worker_process = True
    await broker.startup()

    yield broker

    await broker.shutdown()


async def get_scheduled_tasks(session_maker) -> list[TaskiqMessage]:
    async with session_maker() as session:
        messages = await session.scalars(select(task_messages_table.c.message).order_by(task_messages_table.c.id))
    return [TaskiqMessage.model_validate_json(message) for message in messages]


async def get_scheduled_task_names(session_maker) -> list[str]:
    return [task.task_name for task in await get_scheduled_tasks(session_maker)]
