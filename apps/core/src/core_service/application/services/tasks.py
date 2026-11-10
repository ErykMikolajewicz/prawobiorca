from core_service.shared.exceptions import ServiceUnavailable


def is_retried(error: Exception, is_last_attempt: bool) -> bool:
    return isinstance(error, ServiceUnavailable) and not is_last_attempt
