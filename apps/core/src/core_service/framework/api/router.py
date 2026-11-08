from fastapi import FastAPI

from core_service.framework.api.endpoints.accounts import account_router
from core_service.framework.api.endpoints.application_templates import application_templates_router
from core_service.framework.api.endpoints.auth import auth_router
from core_service.framework.api.endpoints.cases import cases_router
from core_service.framework.api.endpoints.health import health_router
from core_service.framework.api.endpoints.organizations import organizations_router
from core_service.framework.api.endpoints.regulations import regulations_router


def include_all_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(regulations_router)
    app.include_router(account_router)
    app.include_router(cases_router)
    app.include_router(application_templates_router)
    app.include_router(organizations_router)
    app.include_router(health_router)
