from typing import Any, Awaitable, Callable

from taskiq import SimpleRetryMiddleware

from src.infrastructure.relational_db.connection import async_session_maker, engine
from src.infrastructure.tasks.broker import PostgresBroker
from src.shared.consts import MAX_REGULATION_PREPARATION_ATTEMPTS
from src.shared.exceptions import ServiceUnavailable

broker = PostgresBroker(
    session_maker=async_session_maker,
    listen_dsn=engine.url.set(drivername="postgresql").render_as_string(hide_password=False),
).with_middlewares(
    SimpleRetryMiddleware(
        default_retry_count=MAX_REGULATION_PREPARATION_ATTEMPTS,
        default_retry_label=True,
        types_of_exceptions=[ServiceUnavailable],
    )
)


async def init_broker() -> tuple[Any, Callable[..., Awaitable[None]]]:
    await broker.startup()
    return broker, broker.shutdown
