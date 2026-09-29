from typing import Any, Awaitable, Callable

from taskiq import SimpleRetryMiddleware
from taskiq_redis import ListQueueBroker

from src.shared.consts import MAX_REGULATION_PREPARATION_ATTEMPTS
from src.shared.exceptions import ServiceUnavailable
from src.shared.settings.broker import broker_settings

broker = ListQueueBroker(url=broker_settings.URL, socket_timeout=None).with_middlewares(
    SimpleRetryMiddleware(
        default_retry_count=MAX_REGULATION_PREPARATION_ATTEMPTS,
        default_retry_label=True,
        types_of_exceptions=[ServiceUnavailable],
    )
)


async def init_broker() -> tuple[Any, Callable[..., Awaitable[None]]]:
    await broker.startup()
    return broker, broker.shutdown
