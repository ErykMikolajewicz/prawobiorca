import pytest

from core_service.infrastructure.service_errors import get_status_error
from core_service.shared.exceptions import ServiceRequestRejected, ServiceUnavailable


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (400, ServiceRequestRejected),
        (403, ServiceRequestRejected),
        (404, ServiceRequestRejected),
        (408, ServiceUnavailable),
        (422, ServiceRequestRejected),
        (429, ServiceUnavailable),
        (499, ServiceRequestRejected),
        (500, ServiceUnavailable),
        (502, ServiceUnavailable),
        (503, ServiceUnavailable),
        (599, ServiceUnavailable),
    ],
)
def test_status_error_distinguishes_retryable_failures(status_code, expected_error):
    assert isinstance(get_status_error(status_code), expected_error)
