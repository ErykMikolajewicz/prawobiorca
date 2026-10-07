from unittest.mock import create_autospec

import pytest

from src.app.interfaces.application_templates import ApplicationTemplatesRepository, ApplicationTemplatesStorage
from src.app.interfaces.applications import ApplicationsRepository
from src.app.interfaces.cases import CaseDocumentsRepository, CasesRepository
from src.app.interfaces.regulations import RegulationsRepository
from src.app.interfaces.relational import AsyncSession, SessionMaker
from src.app.interfaces.sections import SectionsRepository
from src.app.interfaces.users import UsersRepository, UsersSessionsRepository
from src.app.ports.application_templates import ApplicationTemplateInspector, ApplicationTemplateInstructionsProvider
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter
from src.app.ports.texts import TextsEmbedder


@pytest.fixture
async def mock_session():
    session = create_autospec(AsyncSession)
    opened_session = await session.__aenter__()
    return opened_session


@pytest.fixture
async def mock_opened_session(mock_session):
    opened_session = await mock_session.__aenter__()
    return opened_session


@pytest.fixture
def mock_session_maker(mock_session):
    session_maker = create_autospec(SessionMaker)
    session_maker.begin.return_value = mock_session
    session_maker.return_value = mock_session
    return session_maker


@pytest.fixture
def mock_users_repo():
    repo = create_autospec(UsersRepository)
    return repo


@pytest.fixture
def mock_sessions_repo():
    repo = create_autospec(UsersSessionsRepository)
    return repo


@pytest.fixture
def mock_regulations_repository():
    repo = create_autospec(RegulationsRepository)
    return repo


@pytest.fixture
def mock_embedding_port():
    port = create_autospec(TextsEmbedder)
    return port


@pytest.fixture
def mock_sections_repo():
    repo = create_autospec(SectionsRepository)
    return repo


@pytest.fixture
def mock_cases_repo():
    repo = create_autospec(CasesRepository)
    return repo


@pytest.fixture
def mock_case_documents_repo():
    repo = create_autospec(CaseDocumentsRepository)
    return repo


@pytest.fixture
def mock_application_writer():
    port = create_autospec(ApplicationWriter)
    return port


@pytest.fixture
def mock_application_renderer():
    port = create_autospec(ApplicationRenderer)
    return port


@pytest.fixture
def mock_applications_repo():
    repo = create_autospec(ApplicationsRepository)
    return repo


@pytest.fixture
def mock_application_templates_repo():
    repo = create_autospec(ApplicationTemplatesRepository)
    return repo


@pytest.fixture
def mock_application_templates_storage():
    storage = create_autospec(ApplicationTemplatesStorage)
    return storage


@pytest.fixture
def mock_application_template_inspector():
    port = create_autospec(ApplicationTemplateInspector)
    return port


@pytest.fixture
def mock_application_template_instructions_provider():
    port = create_autospec(ApplicationTemplateInstructionsProvider)
    return port
