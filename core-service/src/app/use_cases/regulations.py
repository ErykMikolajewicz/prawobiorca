import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.regulations import RegulationData, RegulationRepresentation, RegulationUploadTarget
from src.app.dtos.search import SearchParams, SearchResult
from src.app.interfaces.regulations import RegulationsRepository, RegulationsStorage
from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.sections import SectionsRepository
from src.app.ports.tasks import RegulationPreparationScheduler
from src.app.ports.texts import TextsEmbedder
from src.app.services.regulations import RegulationPreparator
from src.domain.exceptions.documents import RegulationDocumentsNotFound
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationServiceUnavailable,
    RegulationsNotPreparedToSearch,
)
from src.domain.value_objects.regulations import (
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationType,
)

logger = logging.getLogger(__name__)


@dataclass
class PrepareRegulation:
    session_maker: SessionMaker
    regulations_storage: RegulationsStorage
    sections_repository: SectionsRepository
    regulations_repository: RegulationsRepository
    regulation_preparator: RegulationPreparator

    async def execute(self, user_id: UUID | None, regulation_id: UUID):
        async with self.session_maker.begin() as session:
            file_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )
            if file_representation is None:
                logger.warning("Regulation to prepare not found!")
                raise RegulationNotFound

            if file_representation.preparation_status == RegulationPreparationStatus.PREPARED:
                logger.warning("Tried prepare already prepared regulation!")
                raise RegulationAlreadyInitialized

            await self.regulations_repository.set_preparation_status(
                session, user_id, regulation_id, RegulationPreparationStatus.IN_PROGRESS
            )

        try:
            regulation_content = await self.regulations_storage.get_regulation(regulation_id)
        except RegulationContentNotFound:
            logger.error("Regulation content not found! regulation id: %s", regulation_id)
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_preparation_status(
                    session, user_id, regulation_id, RegulationPreparationStatus.FAILED
                )
            raise

        try:
            sections_collection = await self.regulation_preparator.prepare_regulation(regulation_content)
        except RegulationServiceUnavailable:
            logger.error("Service to prepare regulation not working!")
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_preparation_status(
                    session, user_id, regulation_id, RegulationPreparationStatus.FAILED
                )
            raise
        except Exception as e:
            logger.error("Unexpected error during regulation preparation! %s", e)
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_preparation_status(
                    session, user_id, regulation_id, RegulationPreparationStatus.FAILED
                )
            raise

        async with self.session_maker.begin() as session:
            await self.sections_repository.add_sections(session, user_id, regulation_id, sections_collection)
            await self.regulations_repository.set_preparation_status(
                session, user_id, regulation_id, RegulationPreparationStatus.PREPARED
            )


@dataclass
class RetryRegulationPreparation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulation_preparation_scheduler: RegulationPreparationScheduler

    async def execute(self, user_id: UUID | None, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )
            if regulation_representation is None:
                logger.warning("Regulation to retry preparation for not found!")
                raise RegulationNotFound

            match regulation_representation.preparation_status:
                case RegulationPreparationStatus.PREPARED:
                    logger.warning("Regulation already prepared! regulation id: %s", regulation_id)
                    raise RegulationAlreadyInitialized
                case RegulationPreparationStatus.IN_PROGRESS:
                    logger.warning("Regulation preparation already in progress! regulation id: %s", regulation_id)
                    raise RegulationPreparationInProgress
                case RegulationPreparationStatus.NOT_STARTED:
                    logger.warning("Regulation content not uploaded yet! regulation id: %s", regulation_id)
                    raise RegulationInInvalidState

            await self.regulations_repository.set_preparation_status(
                session, user_id, regulation_id, RegulationPreparationStatus.IN_PROGRESS
            )

        try:
            await self.regulation_preparation_scheduler.schedule_regulation_preparation(user_id, regulation_id)
        except Exception as e:
            logger.error("Failed to schedule regulation preparation! %s", e)
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_preparation_status(
                    session, user_id, regulation_id, RegulationPreparationStatus.FAILED
                )
            raise RegulationServiceUnavailable()


@dataclass
class AddRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, user_id: UUID | None, regulation_data: RegulationData) -> RegulationUploadTarget:
        regulation_registration_data = RegulationRegistrationData(
            presentation_name=regulation_data.name, regulation_type=regulation_data.regulation_type
        )
        async with self.session_maker.begin() as session:
            regulation_id = await self.regulations_repository.register_regulation(
                session, user_id, regulation_registration_data
            )

        return await self.regulations_storage.get_upload_target(regulation_id)


@dataclass
class ConfirmRegulationUpload:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage
    regulation_preparation_scheduler: RegulationPreparationScheduler

    async def execute(self, user_id: UUID | None, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )

            if regulation_representation is None:
                logger.warning("Regulation to confirm upload not found! regulation id: %s", regulation_id)
                raise RegulationNotFound

            match regulation_representation.preparation_status:
                case RegulationPreparationStatus.PREPARED:
                    logger.warning(
                        "Tried to confirm upload for already prepared regulation! regulation id: %s", regulation_id
                    )
                    raise RegulationAlreadyInitialized
                case RegulationPreparationStatus.IN_PROGRESS:
                    logger.warning("Regulation preparation already in progress! regulation id: %s", regulation_id)
                    raise RegulationPreparationInProgress
                case RegulationPreparationStatus.FAILED:
                    logger.warning("Upload for failed regulation already confirmed! regulation id: %s", regulation_id)
                    raise RegulationInInvalidState

            is_in_storage = await self.regulations_storage.check_regulation_exists(regulation_id)
            if not is_in_storage:
                logger.error(
                    "Cannot confirm upload: Regulation content not found in storage! regulation id: %s", regulation_id
                )
                raise RegulationContentNotFound

            await self.regulations_repository.set_preparation_status(
                session, user_id, regulation_id, RegulationPreparationStatus.IN_PROGRESS
            )

        try:
            await self.regulation_preparation_scheduler.schedule_regulation_preparation(user_id, regulation_id)
        except Exception as e:
            logger.error("Failed to schedule regulation preparation! %s", e)
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_preparation_status(
                    session, user_id, regulation_id, RegulationPreparationStatus.FAILED
                )
            raise RegulationServiceUnavailable()


@dataclass
class GetRegulationDownloadUrl:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, user_id: UUID | None, regulation_id: UUID) -> str:
        async with self.session_maker() as session:
            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )

        if regulation_representation is None:
            logger.warning("Regulation to download not found! regulation id: %s", regulation_id)
            raise RegulationNotFound

        return await self.regulations_storage.get_download_url(regulation_id)


@dataclass
class ListRegulations:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(
        self, user_id: UUID | None, regulation_type: RegulationType | None
    ) -> list[RegulationRepresentation]:
        async with self.session_maker() as session:
            files = await self.regulations_repository.list_regulations(session, user_id, regulation_type)
        return files


@dataclass
class DeleteRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    sections_repository: SectionsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, user_id: UUID | None, regulation_id: UUID):
        async with self.session_maker.begin() as session:
            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )
            if regulation_representation is None:
                logger.warning("Regulation not found! regulation id: %s", regulation_id)
                raise RegulationNotFound

            if regulation_representation.preparation_status == RegulationPreparationStatus.PREPARED:
                await self.sections_repository.remove_sections(session, user_id, regulation_id)
            await self.regulations_repository.unregister_regulation(session, user_id, regulation_id)

        try:
            # Orphaned files are tolerable, too much hassle with eventual consistency
            await self.regulations_storage.delete_regulation(regulation_id)
        except Exception:
            logger.error("Failed to remove from storage regulation: %s", regulation_id)


@dataclass
class SearchRegulation:
    session_maker: SessionMaker
    embedding_port: TextsEmbedder
    sections_repository: SectionsRepository
    regulations_repository: RegulationsRepository

    async def execute(self, user_id: UUID | None, regulation_id, search_params: SearchParams) -> list[SearchResult]:

        embeddings = await self.embedding_port.embed_queries([search_params.query])
        query_vector = embeddings[0]

        async with self.session_maker() as session:
            try:
                results = await self.sections_repository.search(
                    session, user_id, regulation_id, query_vector, search_params
                )
            except RegulationDocumentsNotFound:
                logger.warning("Regulation to search has no prepared documents! regulation id: %s", regulation_id)

                regulation_representation = await self.regulations_repository.get_regulation_representation(
                    session, user_id, regulation_id
                )

                if regulation_representation is None:
                    logger.warning("Regulation not found! regulation id: %s", regulation_id)
                    raise RegulationNotFound

                if regulation_representation.preparation_status != RegulationPreparationStatus.PREPARED:
                    logger.warning("Regulation to search not prepared! regulation id: %s", regulation_id)
                    raise RegulationsNotPreparedToSearch(regulations_name=regulation_representation.presentation_name)

                logger.error("Regulation prepared, but documents not found!")
                raise RegulationInInvalidState
        return results
