import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.regulations import (
    RegulationData,
    RegulationDetailsData,
    RegulationRepresentation,
    RegulationUploadTarget,
)
from src.app.dtos.search import SearchParams, SearchResult
from src.app.interfaces.regulations import RegulationsRepository, RegulationsStorage
from src.app.interfaces.relational import SessionMaker
from src.app.interfaces.sections import SectionsRepository
from src.app.ports.regulations import RegulationDescriptionWriter
from src.app.ports.tasks import RegulationDescriptionGenerationScheduler, RegulationPreparationScheduler
from src.app.ports.texts import TextsEmbedder
from src.app.services.regulations import RegulationPreparator
from src.domain.exceptions.documents import RegulationDocumentsNotFound
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationDescriptionGenerationInProgress,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationsNotPreparedToSearch,
)
from src.domain.services.regulation_access import (
    check_can_add_regulation,
    check_can_generate_regulation_description,
    check_can_manage_regulation,
    check_can_read_regulation,
    resolve_scope_owner,
)
from src.domain.services.regulation_description import create_description_source
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationDetails,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationScope,
    RegulationType,
)
from src.domain.value_objects.users import Caller
from src.shared.consts import (
    MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES,
    MAX_REGULATION_PREPARATION_DELIVERIES,
)
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


@dataclass
class PrepareRegulation:
    session_maker: SessionMaker
    regulations_storage: RegulationsStorage
    sections_repository: SectionsRepository
    regulations_repository: RegulationsRepository
    regulation_preparator: RegulationPreparator
    description_generation_scheduler: RegulationDescriptionGenerationScheduler

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
        except ServiceUnavailable:
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
            if file_representation.description_status == RegulationDescriptionStatus.IN_PROGRESS:
                await self.description_generation_scheduler.schedule_regulation_description_generation(
                    session, user_id, regulation_id
                )


@dataclass
class FailRegulationPreparation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(self, user_id: UUID | None, regulation_id: UUID, delivery_attempt: int) -> bool:
        if delivery_attempt <= MAX_REGULATION_PREPARATION_DELIVERIES:
            return False

        logger.error("Regulation preparation exceeded deliveries limit! regulation id: %s", regulation_id)
        async with self.session_maker.begin() as session:
            await self.regulations_repository.set_preparation_status(
                session, user_id, regulation_id, RegulationPreparationStatus.FAILED
            )
        return True


@dataclass
class RetryRegulationPreparation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulation_preparation_scheduler: RegulationPreparationScheduler

    async def execute(self, caller: Caller, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_manage_regulation(caller, owner)
            user_id = owner.user_id

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
            await self.regulation_preparation_scheduler.schedule_regulation_preparation(session, user_id, regulation_id)


@dataclass
class GenerateRegulationDescription:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    sections_repository: SectionsRepository
    description_writer: RegulationDescriptionWriter
    texts_embedder: TextsEmbedder

    async def execute(self, user_id: UUID | None, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )
            if regulation_representation is None:
                logger.warning("Regulation to generate description not found! regulation id: %s", regulation_id)
                return

            if regulation_representation.description_status == RegulationDescriptionStatus.GENERATED:
                logger.warning("Regulation description already generated! regulation id: %s", regulation_id)
                return

            await self.regulations_repository.set_description_status(
                session, user_id, regulation_id, RegulationDescriptionStatus.IN_PROGRESS
            )
            sections = await self.sections_repository.list_sections_contents(session, user_id, regulation_id)

        description_source = create_description_source(regulation_representation.presentation_name, sections)

        try:
            description = await self.description_writer.write(description_source)
            vectors = await self.texts_embedder.embed_texts([description])
        except ServiceUnavailable:
            logger.error("Service to generate regulation description not working!")
            await self._set_failed(user_id, regulation_id)
            raise
        except Exception as e:
            logger.error("Unexpected error during regulation description generation! %s", e)
            await self._set_failed(user_id, regulation_id)
            raise

        try:
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_generated_description(
                    session, user_id, regulation_id, description, vectors[0]
                )
        except RegulationNotFound:
            logger.warning("Regulation removed during description generation! regulation id: %s", regulation_id)

    async def _set_failed(self, user_id: UUID | None, regulation_id: UUID) -> None:
        try:
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_description_status(
                    session, user_id, regulation_id, RegulationDescriptionStatus.FAILED
                )
        except RegulationNotFound:
            logger.warning("Regulation removed during description generation! regulation id: %s", regulation_id)


@dataclass
class FailRegulationDescriptionGeneration:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(self, user_id: UUID | None, regulation_id: UUID, delivery_attempt: int) -> bool:
        if delivery_attempt <= MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES:
            return False

        logger.error("Regulation description generation exceeded deliveries limit! regulation id: %s", regulation_id)
        try:
            async with self.session_maker.begin() as session:
                await self.regulations_repository.set_description_status(
                    session, user_id, regulation_id, RegulationDescriptionStatus.FAILED
                )
        except RegulationNotFound:
            logger.warning("Regulation removed during description generation! regulation id: %s", regulation_id)
        return True


@dataclass
class RegenerateRegulationDescription:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    description_generation_scheduler: RegulationDescriptionGenerationScheduler

    async def execute(self, caller: Caller, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_manage_regulation(caller, owner)
            check_can_generate_regulation_description(caller)
            user_id = owner.user_id

            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, user_id, regulation_id
            )
            if regulation_representation is None:
                logger.warning("Regulation to generate description not found! regulation id: %s", regulation_id)
                raise RegulationNotFound

            if regulation_representation.preparation_status != RegulationPreparationStatus.PREPARED:
                logger.warning("Regulation to generate description not prepared! regulation id: %s", regulation_id)
                raise RegulationInInvalidState

            if regulation_representation.description_status == RegulationDescriptionStatus.IN_PROGRESS:
                logger.warning("Regulation description generation in progress! regulation id: %s", regulation_id)
                raise RegulationDescriptionGenerationInProgress

            await self.regulations_repository.set_description_status(
                session, user_id, regulation_id, RegulationDescriptionStatus.IN_PROGRESS
            )
            await self.description_generation_scheduler.schedule_regulation_description_generation(
                session, user_id, regulation_id
            )


@dataclass
class AddRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, caller: Caller, regulation_data: RegulationData) -> RegulationUploadTarget:
        check_can_add_regulation(caller, regulation_data.scope)
        if regulation_data.generate_description:
            check_can_generate_regulation_description(caller)
        user_id = resolve_scope_owner(caller, regulation_data.scope)

        regulation_registration_data = RegulationRegistrationData(
            presentation_name=regulation_data.name,
            regulation_type=regulation_data.regulation_type,
            organization_id=regulation_data.organization_id,
            suborganization_id=regulation_data.suborganization_id,
            description_status=(
                RegulationDescriptionStatus.IN_PROGRESS
                if regulation_data.generate_description
                else RegulationDescriptionStatus.NOT_REQUESTED
            ),
        )

        async with self.session_maker.begin() as session:
            try:
                regulation_id = await self.regulations_repository.register_regulation(
                    session, user_id, regulation_registration_data
                )
            except OrganizationNotFound:
                logger.warning("Organization for regulation not found!")
                raise

        return await self.regulations_storage.get_upload_target(regulation_id)


@dataclass
class ConfirmRegulationUpload:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage
    regulation_preparation_scheduler: RegulationPreparationScheduler

    async def execute(self, caller: Caller, regulation_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_manage_regulation(caller, owner)
            user_id = owner.user_id

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
            await self.regulation_preparation_scheduler.schedule_regulation_preparation(session, user_id, regulation_id)


@dataclass
class GetRegulationDownloadUrl:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, caller: Caller, regulation_id: UUID) -> str:
        async with self.session_maker() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_read_regulation(caller, owner)

            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, owner.user_id, regulation_id
            )

        if regulation_representation is None:
            logger.warning("Regulation to download not found! regulation id: %s", regulation_id)
            raise RegulationNotFound

        return await self.regulations_storage.get_download_url(regulation_id)


@dataclass
class GetRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(self, caller: Caller, regulation_id: UUID) -> RegulationRepresentation:
        async with self.session_maker() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_read_regulation(caller, owner)

            regulation_representation = await self.regulations_repository.get_regulation_representation(
                session, owner.user_id, regulation_id
            )

        if regulation_representation is None:
            logger.warning("Regulation not found! regulation id: %s", regulation_id)
            raise RegulationNotFound

        return regulation_representation


@dataclass
class ListRegulations:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(
        self,
        caller: Caller,
        scope: RegulationScope,
        regulation_type: RegulationType | None,
        organization_filter: OrganizationFilter | None,
    ) -> list[RegulationRepresentation]:
        user_id = resolve_scope_owner(caller, scope)
        async with self.session_maker() as session:
            files = await self.regulations_repository.list_regulations(
                session, user_id, regulation_type, organization_filter
            )
        return files


@dataclass
class UpdateRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository

    async def execute(
        self, caller: Caller, regulation_id: UUID, regulation_details_data: RegulationDetailsData
    ) -> RegulationRepresentation:
        regulation_details = RegulationDetails(
            presentation_name=regulation_details_data.name, description=regulation_details_data.description
        )
        async with self.session_maker.begin() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_manage_regulation(caller, owner)

            return await self.regulations_repository.update_regulation_details(
                session, owner.user_id, regulation_id, regulation_details
            )


@dataclass
class DeleteRegulation:
    session_maker: SessionMaker
    regulations_repository: RegulationsRepository
    sections_repository: SectionsRepository
    regulations_storage: RegulationsStorage

    async def execute(self, caller: Caller, regulation_id: UUID):
        async with self.session_maker.begin() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
            check_can_manage_regulation(caller, owner)
            user_id = owner.user_id

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

    async def execute(self, caller: Caller, regulation_id: UUID, search_params: SearchParams) -> list[SearchResult]:
        async with self.session_maker() as session:
            owner = await self.regulations_repository.get_regulation_owner(session, regulation_id)
        check_can_read_regulation(caller, owner)
        user_id = owner.user_id

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
