from core_service.domain.exceptions.access import AccessForbidden, LoginRequired
from core_service.domain.value_objects.users import Caller


def check_can_manage_organizations(caller: Caller) -> None:
    if caller.user_id is None:
        raise LoginRequired
    if not caller.is_admin:
        raise AccessForbidden
