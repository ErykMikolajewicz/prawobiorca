from typing import Annotated, Any

from fastapi import Depends, Request
from taskiq import AsyncBroker

from core_service.application.ports.regulations import RegulationsRepository, RegulationsStorage
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.sections import SectionsRepository
from core_service.application.ports.tasks import (
    RegulationDescriptionGenerationScheduler,
    RegulationPreparationScheduler,
)
from core_service.application.ports.texts import TextsEmbedder
from core_service.application.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    GetRegulation,
    GetRegulationDownloadUrl,
    ListRegulations,
    RegenerateRegulationDescription,
    RetryRegulationPreparation,
    SearchRegulation,
    SearchRegulations,
    UpdateRegulation,
)
from core_service.framework.dependencies.ai_services import get_texts_embedder
from core_service.framework.dependencies.file_storage import (
    create_regulations_storage,
    get_file_storage_client,
    get_file_storage_presign_client,
)
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.relational_db.repositories.regulations import SqlaRegulationsRepository
from core_service.infrastructure.relational_db.repositories.sections import SqlaSectionsRepository
from core_service.infrastructure.tasks.regulations import (
    PostgresRegulationDescriptionGenerationScheduler,
    PostgresRegulationPreparationScheduler,
)


def get_sections_repository() -> SectionsRepository:
    return SqlaSectionsRepository()


def get_regulations_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> RegulationsStorage:
    return create_regulations_storage(client, presign_client)


def get_regulation_repository() -> RegulationsRepository:
    return SqlaRegulationsRepository()


def get_broker(request: Request) -> AsyncBroker:
    return request.app.state.broker


def get_regulations_preparation_scheduler(
    broker: Annotated[AsyncBroker, Depends(get_broker)],
) -> RegulationPreparationScheduler:
    return PostgresRegulationPreparationScheduler(broker)


def get_regulation_description_generation_scheduler(
    broker: Annotated[AsyncBroker, Depends(get_broker)],
) -> RegulationDescriptionGenerationScheduler:
    return PostgresRegulationDescriptionGenerationScheduler(broker)


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
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
) -> UpdateRegulation:
    return UpdateRegulation(session_maker, regulations_repository, texts_embedder)


def get_delete_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    regulations_storage: Annotated[RegulationsStorage, Depends(get_regulations_storage)],
) -> DeleteRegulation:
    return DeleteRegulation(session_maker, regulations_repository, regulations_storage)


def get_search_regulation(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
    sections_repository: Annotated[SectionsRepository, Depends(get_sections_repository)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> SearchRegulation:
    return SearchRegulation(session_maker, texts_embedder, sections_repository, regulations_repository)


def get_search_regulations(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
) -> SearchRegulations:
    return SearchRegulations(session_maker, texts_embedder, regulations_repository)


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


def get_regenerate_regulation_description(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    regulations_repository: Annotated[RegulationsRepository, Depends(get_regulation_repository)],
    description_generation_scheduler: Annotated[
        RegulationDescriptionGenerationScheduler, Depends(get_regulation_description_generation_scheduler)
    ],
) -> RegenerateRegulationDescription:
    return RegenerateRegulationDescription(session_maker, regulations_repository, description_generation_scheduler)
