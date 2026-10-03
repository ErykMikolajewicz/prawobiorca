from fastapi import FastAPI

from src.framework.api.endpoints.accounts import account_router
from src.framework.api.endpoints.auth import auth_router
from src.framework.api.endpoints.cases import cases_router
from src.framework.api.endpoints.health import health_router
from src.framework.api.endpoints.public_regulations import public_regulations_router
from src.framework.api.endpoints.user_regulations import user_regulations_router


def include_all_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(public_regulations_router)
    app.include_router(account_router)
    app.include_router(cases_router)
    app.include_router(user_regulations_router)
    app.include_router(health_router)
