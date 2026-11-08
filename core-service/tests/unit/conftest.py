from unittest.mock import MagicMock, create_autospec

import pytest

from src.app.interfaces.application_templates import ApplicationTemplatesRepository
from src.app.interfaces.applications import ApplicationsRepository
from src.app.interfaces.cases import CaseDocumentsRepository, CasesRepository
from src.app.interfaces.regulations import RegulationsRepository
from src.app.interfaces.relational import AsyncSession, SessionMaker
from src.app.interfaces.sections import SectionsRepository
from src.app.interfaces.users import UsersRepository, UsersSessionsRepository
from src.app.ports.application_templates import ApplicationTemplateInspector
from src.app.ports.applications import ApplicationRenderer
from src.app.ports.texts import TextsEmbedder
from src.app.services.regulations import RegulationPreparator


@pytest.fixture
def mock_opened_session():
    opened_session = create_autospec(AsyncSession)
    return opened_session


@pytest.fixture
def mock_session(mock_opened_session):
    session = MagicMock()
    session.__aenter__.return_value = mock_opened_session
    return session


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
def mock_regulations_repo():
    repo = create_autospec(RegulationsRepository)
    return repo


@pytest.fixture
def mock_texts_embedder():
    port = create_autospec(TextsEmbedder)
    return port


@pytest.fixture
def mock_regulation_preparator():
    preparator = create_autospec(RegulationPreparator)
    return preparator


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
def mock_application_template_inspector():
    port = create_autospec(ApplicationTemplateInspector)
    return port
