import pytest

from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.services.application_template_access import (
    check_can_manage_application_templates,
    check_can_read_published_application_templates,
)
from src.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, USER_ID

ANONYMOUS = Caller(user_id=None)
USER = Caller(user_id=USER_ID)
ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)


@pytest.mark.parametrize("caller", [USER, ADMIN])
def test_can_read_published_application_templates(caller):
    check_can_read_published_application_templates(caller)


def test_read_published_application_templates_unlogged():
    with pytest.raises(LoginRequired):
        check_can_read_published_application_templates(ANONYMOUS)


def test_can_manage_application_templates_as_admin():
    check_can_manage_application_templates(ADMIN)


def test_manage_application_templates_as_normal_user():
    with pytest.raises(AccessForbidden):
        check_can_manage_application_templates(USER)


def test_manage_application_templates_unlogged():
    with pytest.raises(LoginRequired):
        check_can_manage_application_templates(ANONYMOUS)
