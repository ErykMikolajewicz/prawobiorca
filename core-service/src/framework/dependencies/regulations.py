from typing import Annotated, Any

from fastapi import Depends, Request

from src.app.interfaces.regulations import RegulationsRepository, RegulationsStorage
from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.sections import SectionsRepository
from src.app.ports.tasks import RegulationPreparationScheduler
from src.app.ports.texts import TextsEmbedder
from src.app.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    GetRegulation,
    GetRegulationDownloadUrl,
    ListRegulations,
    RetryRegulationPreparation,
    SearchRegulation,
    UpdateRegulation,
)
from src.framework.dependencies.ai_services import get_texts_embedder
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.object_storage.repository import S3RegulationsStorage
from src.infrastructure.relational_db.repositories.regulations import RegulationsManagerRepository
from src.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository
from src.infrastructure.tasks.regulations import TaskiqRegulationPreparationScheduler


def get_sections_repository() -> SectionsRepository:
    return RegulationsSectionsRepository()


def get_file_storage_client(request: Request) -> Any:
    return request.app.state.file_storage_client


def get_file_storage_presign_client(request: Request) -> Any:
    return request.app.state.file_storage_presign_client


def get_regulations_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> RegulationsStorage:
    return S3RegulationsStorage(client, presign_client)


def get_regulation_repository() -> RegulationsRepository:
    return RegulationsManagerRepository()


def get_broker(request: Request) -> Any:
    return request.app.state.broker


def get_regulations_preparation_scheduler(
    broker: Annotated[Any, Depends(get_broker)],
) -> RegulationPreparationScheduler:
    return TaskiqRegulationPreparationScheduler(broker)


def get_list_regulations(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulation_manager: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> ListRegulations:

    return ListRegulations(session_maker, regulation_manager)


def get_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> GetRegulation:
    return GetRegulation(session_maker, regulations_repository)


def get_retry_regulation_preparation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    regulation_preparation_scheduler: Annotated[
        RegulationPreparationScheduler, Depends(get_regulations_preparation_scheduler)
    ],
) -> RetryRegulationPreparation:
    return RetryRegulationPreparation(session_maker, regulations_repository, regulation_preparation_scheduler)


def get_update_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> UpdateRegulation:
    return UpdateRegulation(session_maker, regulations_repository)


def get_delete_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    sections_repository: Annotated[SectionsRepository, Depends(get_sections_repository)],
    regulations_storage: Annotated[RegulationsStorage, Depends(get_regulations_storage)],
) -> DeleteRegulation:
    return DeleteRegulation(session_maker, regulations_repository, sections_repository, regulations_storage)


def get_search_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
    sections_repository: Annotated[SectionsRepository, Depends(get_sections_repository)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> SearchRegulation:
    return SearchRegulation(session_maker, texts_embedder, sections_repository, regulations_repository)


def get_add_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    regulations_storage: Annotated[RegulationsStorage, Depends(get_regulations_storage)],
) -> AddRegulation:
    return AddRegulation(session_maker, regulations_repository, regulations_storage)


def get_confirm_regulation_upload(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    regulations_storage: Annotated[RegulationsStorage, Depends(get_regulations_storage)],
    regulation_preparation_scheduler: Annotated[
        RegulationPreparationScheduler, Depends(get_regulations_preparation_scheduler)
    ],
) -> ConfirmRegulationUpload:
    return ConfirmRegulationUpload(
        session_maker, regulations_repository, regulations_storage, regulation_preparation_scheduler
    )


def get_regulation_download_url(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    regulations_storage: Annotated[RegulationsStorage, Depends(get_regulations_storage)],
) -> GetRegulationDownloadUrl:
    return GetRegulationDownloadUrl(session_maker, regulations_repository, regulations_storage)
