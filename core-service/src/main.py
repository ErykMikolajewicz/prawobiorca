import asyncio
import logging
import tomllib
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

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
        logger.critical(f"Can not connect to external service: {e}")
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
                logger.error(f"Error during clean up: {e}")


class FixMultipartBoundaryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "")
        if content_type == "multipart/form-data":
            body = await request.body()
            if body:
                try:
                    first_line = body.split(b"\r\n")[0]
                    boundary = first_line.decode("utf-8").lstrip("-")
                    if boundary:
                        new_headers = request.headers.mutablecopy()
                        new_headers["content-type"] = f"multipart/form-data; boundary={boundary}"
                        request.scope["headers"] = new_headers.raw

                        async def receive():
                            return {"type": "http.request", "body": body}

                        request._receive = receive
                except Exception as e:
                    logger.error(f"Failed to fix multipart boundary: {e}")
        return await call_next(request)


app = FastAPI(lifespan=lifespan, title="PRAWOBIORCA", version=version)
prawobiorca = app

origins = ["http://localhost:5173", "http://localhost:5174"]

prawobiorca.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UWAGA: Obejście problemu z brakiem 'boundary' w multipart/form-data wysyłanym z frontendu.
prawobiorca.add_middleware(FixMultipartBoundaryMiddleware)
include_all_routers(prawobiorca)


if __name__ == "__main__":
    from granian.constants import Interfaces
    from granian.server.embed import Server

    async def launch_granian():
        server = Server(prawobiorca, interface=Interfaces.ASGI)
        await server.serve()

    asyncio.run(launch_granian())
