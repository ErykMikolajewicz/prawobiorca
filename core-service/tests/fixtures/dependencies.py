from unittest.mock import create_autospec

import pytest

from src.app.interfaces.application_templates import ApplicationTemplatesStorage
from src.app.interfaces.applications import ApplicationsStorage
from src.app.interfaces.regulations import RegulationsStorage
from src.app.ports.tasks import (
    ApplicationGenerationScheduler,
    ApplicationTemplateDescriptionGenerationScheduler,
    RegulationDescriptionGenerationScheduler,
    RegulationPreparationScheduler,
)
from src.framework.dependencies.regulations import get_regulations_storage
from src.main import prawobiorca


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
def mock_application_templates_storage():
    return create_autospec(ApplicationTemplatesStorage)


@pytest.fixture
def mock_regulation_preparation_scheduler():
    return create_autospec(RegulationPreparationScheduler)


@pytest.fixture
def mock_regulation_description_generation_scheduler():
    return create_autospec(RegulationDescriptionGenerationScheduler)


@pytest.fixture
def mock_application_generation_scheduler():
    return create_autospec(ApplicationGenerationScheduler)


@pytest.fixture
def mock_application_template_description_generation_scheduler():
    return create_autospec(ApplicationTemplateDescriptionGenerationScheduler)
