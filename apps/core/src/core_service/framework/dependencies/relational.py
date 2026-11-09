from core_service.infrastructure.relational_db.connection import DatabaseSessionMaker, async_session_maker


def get_session_maker() -> DatabaseSessionMaker:
    return async_session_maker
