from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.value_objects.users import Caller


def check_can_read_published_application_templates(caller: Caller) -> None:
    if caller.user_id is None:
        raise LoginRequired


def check_can_manage_application_templates(caller: Caller) -> None:
    check_can_read_published_application_templates(caller)
    if not caller.is_admin:
        raise AccessForbidden
