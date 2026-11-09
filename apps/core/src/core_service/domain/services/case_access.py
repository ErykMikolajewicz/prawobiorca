from uuid import UUID

from core_service.domain.exceptions.access import LoginRequired
from core_service.domain.value_objects.users import Caller


def resolve_case_owner(caller: Caller) -> UUID:
    if caller.user_id is None:
        raise LoginRequired
    return caller.user_id
