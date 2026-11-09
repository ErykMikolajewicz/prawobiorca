from typing import Annotated, Any

from fastapi import Depends

from core_service.application.ports.applications import ApplicationsRepository, ApplicationsStorage
from core_service.application.ports.cases import CaseDocumentsRepository, CasesRepository
from core_service.application.ports.relational import SessionMaker
from core_service.application.use_cases.cases import (
    AddCase,
    AddCaseDocument,
    DeleteCase,
    DeleteCaseDocument,
    ListCaseDocuments,
    ListCases,
)
from core_service.framework.dependencies.regulations import get_file_storage_client, get_file_storage_presign_client
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.object_storage.repository import S3ApplicationsStorage
from core_service.infrastructure.relational_db.repositories.applications import SqlaApplicationsRepository
from core_service.infrastructure.relational_db.repositories.cases import (
    SqlaCaseDocumentsRepository,
    SqlaCasesRepository,
)
from core_service.shared.settings.object_storage import object_storage_settings


def get_cases_repo() -> CasesRepository:
    return SqlaCasesRepository()


def get_case_documents_repo() -> CaseDocumentsRepository:
    return SqlaCaseDocumentsRepository()


def get_applications_repo() -> ApplicationsRepository:
    return SqlaApplicationsRepository()


def get_applications_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> ApplicationsStorage:
    return S3ApplicationsStorage(
        client,
        presign_client,
        bucket=object_storage_settings.BUCKET,
        signed_url_expiration_seconds=object_storage_settings.SIGNED_URL_EXPIRATION_SECONDS,
    )


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
