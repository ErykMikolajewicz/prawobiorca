from enum import StrEnum
from typing import Callable
from unittest.mock import create_autospec

import pytest
from fastapi.requests import Request

from src.app.interfaces.application_templates import ApplicationTemplatesStorage
from src.app.interfaces.applications import ApplicationsStorage
from src.app.interfaces.regulations import RegulationsStorage
from src.app.ports.tasks import ApplicationGenerationScheduler, RegulationPreparationScheduler
from src.domain.value_objects.users import UserPrivileges
from src.framework.dependencies.application_templates import get_application_templates_storage
from src.framework.dependencies.applications import get_application_generation_scheduler
from src.framework.dependencies.authentication import authorize_user
from src.framework.dependencies.cases import get_applications_storage
from src.framework.dependencies.regulations import get_regulations_preparation_scheduler, get_regulations_storage
from src.main import prawobiorca
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, SESSION_ID, USER_ID


@pytest.fixture
def mock_regulations_storage():
    return create_autospec(RegulationsStorage)


@pytest.fixture
def override_get_regulations_storage(mock_regulations_storage):
    prawobiorca.dependency_overrides[get_regulations_storage] = lambda: mock_regulations_storage
    yield
    prawobiorca.dependency_overrides.pop(get_regulations_storage, None)


@pytest.fixture
def mock_applications_storage():
    return create_autospec(ApplicationsStorage)


@pytest.fixture
def override_get_applications_storage(mock_applications_storage):
    prawobiorca.dependency_overrides[get_applications_storage] = lambda: mock_applications_storage
    yield
    prawobiorca.dependency_overrides.pop(get_applications_storage, None)


@pytest.fixture
def mock_application_templates_storage():
    return create_autospec(ApplicationTemplatesStorage)


@pytest.fixture
def override_get_application_templates_storage(mock_application_templates_storage):
    prawobiorca.dependency_overrides[get_application_templates_storage] = lambda: mock_application_templates_storage
    yield
    prawobiorca.dependency_overrides.pop(get_application_templates_storage, None)


@pytest.fixture
def mock_regulation_preparation_scheduler():
    return create_autospec(RegulationPreparationScheduler)


@pytest.fixture
def override_get_regulations_preparation_scheduler(mock_regulation_preparation_scheduler):
    prawobiorca.dependency_overrides[get_regulations_preparation_scheduler] = lambda: (
        mock_regulation_preparation_scheduler
    )
    yield
    prawobiorca.dependency_overrides.pop(get_regulations_preparation_scheduler, None)


@pytest.fixture
def mock_application_generation_scheduler():
    return create_autospec(ApplicationGenerationScheduler)


@pytest.fixture
def override_get_application_generation_scheduler(mock_application_generation_scheduler):
    prawobiorca.dependency_overrides[get_application_generation_scheduler] = lambda: (
        mock_application_generation_scheduler
    )
    yield
    prawobiorca.dependency_overrides.pop(get_application_generation_scheduler, None)


class UserType(StrEnum):
    NORMAL = "NORMAL"
    ADMIN = "ADMIN"


@pytest.fixture
def get_set_mock_auth_dependency() -> Callable:

    def set_mock_auth_dependency(user_type: UserType):
        async def mock_authorize_user(request: Request):
            user_id = None
            user_privileges = None
            if request.cookies.get(ACCESS_COOKIE_NAME) == ACCESS_TOKEN:
                user_id = USER_ID
                match user_type:
                    case UserType.NORMAL:
                        user_privileges = UserPrivileges(is_admin=False)
                    case UserType.ADMIN:
                        user_privileges = UserPrivileges(is_admin=True)
                    case _:
                        raise Exception("Invalid user type!")

            request.state.session_id = SESSION_ID if user_id else None
            request.state.user_id = user_id
            request.state.user_privileges = user_privileges

        return mock_authorize_user

    return set_mock_auth_dependency


@pytest.fixture
def override_authorize_normal_user(get_set_mock_auth_dependency):
    override_function = get_set_mock_auth_dependency(UserType.NORMAL)
    prawobiorca.dependency_overrides[authorize_user] = override_function
    yield
    prawobiorca.dependency_overrides.pop(authorize_user, None)


@pytest.fixture
def override_authorize_admin_user(get_set_mock_auth_dependency):
    override_function = get_set_mock_auth_dependency(UserType.ADMIN)
    prawobiorca.dependency_overrides[authorize_user] = override_function
    yield
    prawobiorca.dependency_overrides.pop(authorize_user, None)
