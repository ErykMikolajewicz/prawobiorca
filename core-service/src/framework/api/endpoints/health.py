import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status

logger = logging.getLogger(__name__)

health_router = APIRouter(
    prefix="/health",
    tags=["health check"],
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service unavailable."}},
)


@health_router.get("/liveness")
async def get_health_status() -> Literal["OK"]:
    logger.info("Checking liveness.")

    return "OK"


@health_router.get("/ready", summary="Check is application ready to response for requests.")
async def check_readiness(request: Request) -> Literal[True]:
    try:
        is_ready = request.app.state.ready
    except AttributeError:
        logger.warning("Application is not ready to serve yet.", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application not ready yet")
    if is_ready:
        return is_ready
    logger.critical("Application is in invalid readiness state!.")
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application is in invalid state!")
