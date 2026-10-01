from pytest import fixture
from sqlalchemy import delete
from sqlalchemy.engine import make_url

from src.infrastructure.relational_db.connection import DatabaseSessionMaker
from src.infrastructure.relational_db.schemas.tasks import task_messages_table
from src.infrastructure.tasks.broker import PostgresBroker


@fixture(scope="function")
async def task_broker(postgres_container, session_maker):
    listen_dsn = make_url(postgres_container.get_connection_url()).set(drivername="postgresql")
    broker = PostgresBroker(
        session_maker=DatabaseSessionMaker(session_maker),
        listen_dsn=listen_dsn.render_as_string(hide_password=False),
    )
    broker.is_worker_process = True
    await broker.startup()

    yield broker

    await broker.shutdown()


@fixture(scope="function")
async def clean_task_messages(session_maker):
    yield
    async with session_maker.begin() as session:
        await session.execute(delete(task_messages_table))
