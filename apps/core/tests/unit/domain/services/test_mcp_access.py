import pytest

from core_service.domain.exceptions.access import AccessForbidden, LoginRequired
from core_service.domain.services.mcp_access import resolve_mcp_administrator
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, USER_ID


def test_resolve_mcp_administrator():
    assert resolve_mcp_administrator(Caller(user_id=ADMIN_ID, is_admin=True)) == ADMIN_ID


def test_resolve_mcp_administrator_as_normal_user():
    with pytest.raises(AccessForbidden):
        resolve_mcp_administrator(Caller(user_id=USER_ID))


def test_resolve_mcp_administrator_unlogged():
    with pytest.raises(LoginRequired):
        resolve_mcp_administrator(Caller(user_id=None))
