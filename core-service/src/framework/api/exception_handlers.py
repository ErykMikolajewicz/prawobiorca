import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


async def handle_service_unavailable(request: Request, exc: ServiceUnavailable) -> JSONResponse:
    logger.error("Service unavailable during %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service unavailable!"},
    )


def include_exception_handlers(app: FastAPI):
    app.add_exception_handler(ServiceUnavailable, handle_service_unavailable)
