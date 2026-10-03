import asyncio
import logging
import tomllib
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from src.framework.api.exception_handlers import include_exception_handlers
from src.framework.api.router import include_all_routers
from src.framework.dependencies.file_storage import init_file_storage_client
from src.infrastructure.ai_services.initialization import init_ai_services_client
from src.infrastructure.relational_db.connection import check_relational_db_connection
from src.infrastructure.tasks.connection import init_broker
from src.shared.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("src")

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)
version = data["project"]["version"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    closing_callbacks = []

    logger.info("Connecting to external services.")
    try:
        relational_closing_callback = await check_relational_db_connection()
        closing_callbacks.insert(0, relational_closing_callback)

        (
            file_storage_client,
            file_storage_presign_client,
            file_storage_closing_callback,
        ) = await init_file_storage_client()
        app.state.file_storage_client = file_storage_client
        app.state.file_storage_presign_client = file_storage_presign_client
        closing_callbacks.insert(0, file_storage_closing_callback)

        http_client, http_closing_callback = await init_ai_services_client()
        app.state.ai_services_client = http_client
        closing_callbacks.insert(0, http_closing_callback)

        broker, broker_closing_callback = await init_broker()
        app.state.broker = broker
        closing_callbacks.insert(0, broker_closing_callback)

    except Exception as e:
        logger.critical("Can not connect to external service: %s", e)
        raise
    else:
        app.state.ready = True
        logger.info("Application is ready to serve.")
        yield
    finally:
        logger.info("Closing application.")
        app.state.ready = False

        for callback in closing_callbacks:
            try:
                async with asyncio.timeout(30):
                    await callback()
            except Exception as e:
                logger.error("Error during clean up: %s", e)


prawobiorca = FastAPI(
    lifespan=lifespan,
    title="PRAWOBIORCA",
    version=version,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service unavailable!"}},
    generate_unique_id_function=lambda route: route.name,
)

origins = ["http://localhost:5173", "http://localhost:5174"]

prawobiorca.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

include_all_routers(prawobiorca)
include_exception_handlers(prawobiorca)


if __name__ == "__main__":
    from granian.constants import Interfaces
    from granian.server.embed import Server

    async def launch_granian():
        server = Server(prawobiorca, interface=Interfaces.ASGI)
        await server.serve()

    asyncio.run(launch_granian())
