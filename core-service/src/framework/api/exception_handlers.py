import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


async def handle_service_unavailable(request: Request, exc: ServiceUnavailable) -> JSONResponse:
    logger.error("Service unavailable during %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service unavailable!"},
    )


async def handle_login_required(request: Request, exc: LoginRequired) -> JSONResponse:
    logger.warning("Unlogged user attempt to use endpoint: %s %s!", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Login required!"},
    )


async def handle_access_forbidden(request: Request, exc: AccessForbidden) -> JSONResponse:
    logger.warning("Forbidden access attempt to endpoint: %s %s!", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Permission required!"},
    )


def include_exception_handlers(app: FastAPI):
    app.add_exception_handler(ServiceUnavailable, handle_service_unavailable)
    app.add_exception_handler(LoginRequired, handle_login_required)
    app.add_exception_handler(AccessForbidden, handle_access_forbidden)
