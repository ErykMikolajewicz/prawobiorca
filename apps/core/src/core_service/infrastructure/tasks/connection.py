from collections.abc import Awaitable, Callable
from typing import Any

from taskiq import SimpleRetryMiddleware

from core_service.infrastructure.relational_db.connection import async_session_maker, engine
from core_service.infrastructure.tasks.broker import PostgresBroker
from core_service.shared.consts import MAX_REGULATION_PREPARATION_ATTEMPTS
from core_service.shared.exceptions import ServiceUnavailable

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
