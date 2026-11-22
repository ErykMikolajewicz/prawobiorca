from uuid import UUID

from core_service.domain.exceptions.access import AccessForbidden, LoginRequired
from core_service.domain.value_objects.users import Caller


def resolve_mcp_administrator(caller: Caller) -> UUID:
    if caller.user_id is None:
        raise LoginRequired
    if not caller.is_admin:
        raise AccessForbidden
    return caller.user_id
