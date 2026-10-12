import pytest

from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.exceptions.regulations import RegulationNotFound
from src.domain.services.regulation_access import (
    check_can_add_regulation,
    check_can_manage_regulation,
    check_can_read_regulation,
    resolve_scope_owner,
)
from src.domain.value_objects.regulations import RegulationOwner, RegulationScope
from src.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, USER_ID

ANONYMOUS = Caller(user_id=None)
USER = Caller(user_id=USER_ID)
ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)

PUBLIC_REGULATION = RegulationOwner(user_id=None)
USER_REGULATION = RegulationOwner(user_id=USER_ID)


def test_resolve_public_scope_owner():
    assert resolve_scope_owner(ANONYMOUS, RegulationScope.PUBLIC) is None


def test_resolve_private_scope_owner():
    assert resolve_scope_owner(USER, RegulationScope.PRIVATE) == USER_ID


def test_resolve_private_scope_owner_unlogged():
    with pytest.raises(LoginRequired):
        resolve_scope_owner(ANONYMOUS, RegulationScope.PRIVATE)


@pytest.mark.parametrize(
    "caller, scope",
    [
        (USER, RegulationScope.PRIVATE),
        (ADMIN, RegulationScope.PRIVATE),
        (ADMIN, RegulationScope.PUBLIC),
    ],
    ids=("user private", "admin private", "admin public"),
)
def test_can_add_regulation(caller, scope):
    check_can_add_regulation(caller, scope)


@pytest.mark.parametrize(
    "caller, scope, error",
    [
        (ANONYMOUS, RegulationScope.PRIVATE, LoginRequired),
        (ANONYMOUS, RegulationScope.PUBLIC, LoginRequired),
        (USER, RegulationScope.PUBLIC, AccessForbidden),
    ],
    ids=("anonymous private", "anonymous public", "user public"),
)
def test_cannot_add_regulation(caller, scope, error):
    with pytest.raises(error):
        check_can_add_regulation(caller, scope)


@pytest.mark.parametrize(
    "caller, owner",
    [
        (ANONYMOUS, PUBLIC_REGULATION),
        (USER, PUBLIC_REGULATION),
        (USER, USER_REGULATION),
    ],
    ids=("anonymous public", "user public", "owner private"),
)
def test_can_read_regulation(caller, owner):
    check_can_read_regulation(caller, owner)


@pytest.mark.parametrize("caller", [ANONYMOUS, ADMIN], ids=("anonymous", "admin"))
def test_cannot_read_other_user_regulation(caller):
    with pytest.raises(RegulationNotFound):
        check_can_read_regulation(caller, USER_REGULATION)


@pytest.mark.parametrize(
    "caller, owner",
    [
        (USER, USER_REGULATION),
        (ADMIN, PUBLIC_REGULATION),
    ],
    ids=("owner private", "admin public"),
)
def test_can_manage_regulation(caller, owner):
    check_can_manage_regulation(caller, owner)


@pytest.mark.parametrize(
    "caller, owner, error",
    [
        (ANONYMOUS, PUBLIC_REGULATION, LoginRequired),
        (USER, PUBLIC_REGULATION, AccessForbidden),
        (ANONYMOUS, USER_REGULATION, RegulationNotFound),
        (ADMIN, USER_REGULATION, RegulationNotFound),
    ],
    ids=("anonymous public", "user public", "anonymous private", "admin other user private"),
)
def test_cannot_manage_regulation(caller, owner, error):
    with pytest.raises(error):
        check_can_manage_regulation(caller, owner)
