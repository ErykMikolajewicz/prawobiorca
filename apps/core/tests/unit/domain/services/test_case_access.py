import pytest

from core_service.domain.exceptions.access import LoginRequired
from core_service.domain.services.case_access import resolve_case_owner
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, USER_ID


@pytest.mark.parametrize(
    "caller",
    [Caller(user_id=USER_ID), Caller(user_id=ADMIN_ID, is_admin=True)],
)
def test_resolve_case_owner(caller):
    assert resolve_case_owner(caller) == caller.user_id


def test_resolve_case_owner_unlogged():
    with pytest.raises(LoginRequired):
        resolve_case_owner(Caller(user_id=None))
