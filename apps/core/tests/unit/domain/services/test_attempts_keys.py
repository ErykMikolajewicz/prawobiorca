from core_service.domain.services.attempts import get_login_attempts_key, get_registration_attempts_key
from tests.consts import IP_ADDRESS, VALID_USERNAME

OTHER_IP_ADDRESS = "198.51.100.4"


def test_login_attempts_key_is_stable():
    assert get_login_attempts_key(VALID_USERNAME, IP_ADDRESS) == get_login_attempts_key(VALID_USERNAME, IP_ADDRESS)


def test_login_attempts_key_depends_on_username_and_address():
    key = get_login_attempts_key(VALID_USERNAME, IP_ADDRESS)

    assert key != get_login_attempts_key("other-user", IP_ADDRESS)
    assert key != get_login_attempts_key(VALID_USERNAME, OTHER_IP_ADDRESS)


def test_login_attempts_key_has_bounded_length():
    assert len(get_login_attempts_key("a" * 10_000, IP_ADDRESS)) == len(get_login_attempts_key("a", IP_ADDRESS))


def test_registration_attempts_key_depends_on_address():
    assert get_registration_attempts_key(IP_ADDRESS) != get_registration_attempts_key(OTHER_IP_ADDRESS)
    assert get_registration_attempts_key(IP_ADDRESS) != get_login_attempts_key(VALID_USERNAME, IP_ADDRESS)
