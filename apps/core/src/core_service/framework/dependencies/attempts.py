from datetime import timedelta
from typing import Annotated

from fastapi import Depends

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.services.attempts import AttemptLimiter
from core_service.domain.value_objects.attempts import AttemptLimit
from core_service.infrastructure.relational_db.repositories.attempts import SqlaAttemptsRepository
from core_service.shared.settings.application import app_settings


def get_attempts_repo() -> AttemptsRepository:
    return SqlaAttemptsRepository()


def get_login_attempt_limit() -> AttemptLimit:
    return AttemptLimit(
        max_attempts=app_settings.LOGIN_MAX_FAILED_ATTEMPTS,
        window=timedelta(seconds=app_settings.LOGIN_ATTEMPTS_WINDOW_SECONDS),
    )


def get_registration_attempt_limit() -> AttemptLimit:
    return AttemptLimit(
        max_attempts=app_settings.REGISTRATION_MAX_ATTEMPTS,
        window=timedelta(seconds=app_settings.REGISTRATION_ATTEMPTS_WINDOW_SECONDS),
    )


def get_login_attempt_limiter(
    attempts_repo: Annotated[AttemptsRepository, Depends(get_attempts_repo)],
    limit: Annotated[AttemptLimit, Depends(get_login_attempt_limit)],
) -> AttemptLimiter:
    return AttemptLimiter(attempts_repo, limit)


def get_registration_attempt_limiter(
    attempts_repo: Annotated[AttemptsRepository, Depends(get_attempts_repo)],
    limit: Annotated[AttemptLimit, Depends(get_registration_attempt_limit)],
) -> AttemptLimiter:
    return AttemptLimiter(attempts_repo, limit)
