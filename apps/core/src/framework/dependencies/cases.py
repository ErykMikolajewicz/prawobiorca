from typing import Annotated, Any

from fastapi import Depends

import src.infrastructure.relational_db.repositories.cases as sqla_repos
from src.app.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from src.app.interfaces.cases import CaseDocumentsRepository, CasesRepository
from src.app.interfaces.relational import SessionMaker
from src.app.use_cases.cases import (
    AddCase,
    AddCaseDocument,
    DeleteCase,
    DeleteCaseDocument,
    ListCaseDocuments,
    ListCases,
)
from src.framework.dependencies.regulations import get_file_storage_client, get_file_storage_presign_client
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.object_storage.repository import S3ApplicationsStorage
from src.infrastructure.relational_db.repositories.applications import (
    ApplicationsRepository as SqlaApplicationsRepository,
)


def get_cases_repo() -> CasesRepository:
    return sqla_repos.CasesRepository()


def get_case_documents_repo() -> CaseDocumentsRepository:
    return sqla_repos.CaseDocumentsRepository()


def get_applications_repo() -> ApplicationsRepository:
    return SqlaApplicationsRepository()


def get_applications_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> ApplicationsStorage:
    return S3ApplicationsStorage(client, presign_client)


def get_list_user_cases(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    cases_repository: Annotated[CasesRepository, Depends(get_cases_repo)],
) -> ListCases:
    return ListCases(session_maker, cases_repository)


def get_add_user_case(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    cases_repository: Annotated[CasesRepository, Depends(get_cases_repo)],
) -> AddCase:
    return AddCase(session_maker, cases_repository)


def get_delete_user_case(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    cases_repository: Annotated[CasesRepository, Depends(get_cases_repo)],
    applications_repo: Annotated[ApplicationsRepository, Depends(get_applications_repo)],
    applications_storage: Annotated[ApplicationsStorage, Depends(get_applications_storage)],
) -> DeleteCase:
    return DeleteCase(session_maker, cases_repository, applications_repo, applications_storage)


def get_add_case_document(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    case_documents_repo: Annotated[CaseDocumentsRepository, Depends(get_case_documents_repo)],
) -> AddCaseDocument:
    return AddCaseDocument(session_maker, case_documents_repo)


def get_delete_case_document(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    case_documents_repo: Annotated[CaseDocumentsRepository, Depends(get_case_documents_repo)],
) -> DeleteCaseDocument:
    return DeleteCaseDocument(session_maker, case_documents_repo)


def get_list_case_documents(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    case_documents_repo: Annotated[CaseDocumentsRepository, Depends(get_case_documents_repo)],
) -> ListCaseDocuments:
    return ListCaseDocuments(session_maker, case_documents_repo)
