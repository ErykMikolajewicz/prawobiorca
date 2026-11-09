import pytest

from core_service.domain.exceptions.access import AccessForbidden, LoginRequired
from core_service.domain.services.organization_access import check_can_manage_organizations
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, USER_ID


def test_can_manage_organizations_as_admin():
    check_can_manage_organizations(Caller(user_id=ADMIN_ID, is_admin=True))


def test_manage_organizations_as_normal_user():
    with pytest.raises(AccessForbidden):
        check_can_manage_organizations(Caller(user_id=USER_ID))


def test_manage_organizations_unlogged():
    with pytest.raises(LoginRequired):
        check_can_manage_organizations(Caller(user_id=None))
