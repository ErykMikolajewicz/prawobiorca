import inspect
from typing import Any
from unittest.mock import DEFAULT, AsyncMock


def get_awaited_arguments(method: AsyncMock, name: str) -> list[Any]:
    signature = inspect.signature(method)
    return [signature.bind(*call.args, **call.kwargs).arguments[name] for call in method.await_args_list]


def get_awaited_argument(method: AsyncMock, name: str) -> Any:
    return get_awaited_arguments(method, name)[-1]


def record_saved_states(save: AsyncMock, name: str, attribute: str) -> list[Any]:
    signature = inspect.signature(save)
    states = []

    def record(*args, **kwargs) -> Any:
        entity = signature.bind(*args, **kwargs).arguments[name]
        states.append(getattr(entity, attribute))
        return DEFAULT

    save.side_effect = record
    return states
