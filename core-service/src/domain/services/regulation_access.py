from uuid import UUID

from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.exceptions.regulations import RegulationNotFound
from src.domain.value_objects.regulations import RegulationOwner, RegulationScope
from src.domain.value_objects.users import Caller


def resolve_scope_owner(caller: Caller, scope: RegulationScope) -> UUID | None:
    if scope == RegulationScope.PUBLIC:
        return None
    if caller.user_id is None:
        raise LoginRequired
    return caller.user_id


def check_can_add_regulation(caller: Caller, scope: RegulationScope) -> None:
    if caller.user_id is None:
        raise LoginRequired
    if scope == RegulationScope.PUBLIC and not caller.is_admin:
        raise AccessForbidden


def check_can_read_regulation(caller: Caller, owner: RegulationOwner) -> None:
    if owner.user_id is not None and owner.user_id != caller.user_id:
        raise RegulationNotFound


def check_can_manage_regulation(caller: Caller, owner: RegulationOwner) -> None:
    check_can_read_regulation(caller, owner)
    if caller.user_id is None:
        raise LoginRequired
    if owner.user_id is None and not caller.is_admin:
        raise AccessForbidden
