from unittest.mock import create_autospec

import pytest

from core_service.application.interfaces.application_templates import ApplicationTemplatesStorage
from core_service.application.interfaces.applications import ApplicationsStorage
from core_service.application.interfaces.regulations import RegulationsStorage
from core_service.application.ports.application_templates import ApplicationTemplateDescriptionWriter
from core_service.application.ports.applications import ApplicationWriter
from core_service.application.ports.regulations import RegulationDescriptionWriter, RegulationSplitter
from core_service.application.ports.tasks import (
    ApplicationGenerationScheduler,
    ApplicationTemplateDescriptionGenerationScheduler,
    RegulationDescriptionGenerationScheduler,
    RegulationPreparationScheduler,
)
from core_service.framework.dependencies.regulations import get_regulations_storage
from core_service.main import prawobiorca


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


@pytest.fixture
def mock_regulation_splitter():
    return create_autospec(RegulationSplitter)


@pytest.fixture
def mock_regulation_description_writer():
    return create_autospec(RegulationDescriptionWriter)


@pytest.fixture
def mock_application_writer():
    return create_autospec(ApplicationWriter)


@pytest.fixture
def mock_application_template_description_writer():
    return create_autospec(ApplicationTemplateDescriptionWriter)
