from collections.abc import Awaitable, Callable
from typing import Any

from taskiq import SmartRetryMiddleware, TaskiqMessage

from core_service.infrastructure.relational_db.connection import async_session_maker, engine
from core_service.infrastructure.tasks.broker import PostgresBroker
from core_service.shared.exceptions import ServiceUnavailable

DEFAULT_TASK_RETRY_COUNT = 3

TASK_RETRY_DELAY_SECONDS = 10

MAX_TASK_RETRY_DELAY_SECONDS = 60

RETRIES_LABEL = "_retries"

MAX_RETRIES_LABEL = "max_retries"

broker = PostgresBroker(
    session_maker=async_session_maker,
    listen_dsn=engine.url.set(drivername="postgresql").render_as_string(hide_password=False),
).with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=DEFAULT_TASK_RETRY_COUNT,
        default_retry_label=True,
        default_delay=TASK_RETRY_DELAY_SECONDS,
        use_jitter=True,
        use_delay_exponent=True,
        max_delay_exponent=MAX_TASK_RETRY_DELAY_SECONDS,
        types_of_exceptions=[ServiceUnavailable],
    )
)


def is_last_attempt(message: TaskiqMessage) -> bool:
    attempt = int(message.labels.get(RETRIES_LABEL, 0)) + 1
    return attempt >= int(message.labels.get(MAX_RETRIES_LABEL, DEFAULT_TASK_RETRY_COUNT))


async def init_broker() -> tuple[Any, Callable[..., Awaitable[None]]]:
    await broker.startup()
    return broker, broker.shutdown
