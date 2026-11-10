from core_service.shared.exceptions import ServiceRequestRejected, ServiceUnavailable

RETRYABLE_CLIENT_ERROR_STATUS_CODES = frozenset({408, 429})


def get_status_error(status_code: int) -> ServiceUnavailable | ServiceRequestRejected:
    if status_code >= 500 or status_code in RETRYABLE_CLIENT_ERROR_STATUS_CODES:
        return ServiceUnavailable()
    return ServiceRequestRejected()
