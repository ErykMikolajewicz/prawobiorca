from core_service.application.interfaces.relational import SessionMaker
from core_service.infrastructure.relational_db.connection import async_session_maker


def get_session_maker() -> SessionMaker:
    return async_session_maker
