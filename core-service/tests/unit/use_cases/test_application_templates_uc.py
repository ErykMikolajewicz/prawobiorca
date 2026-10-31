from unittest.mock import AsyncMock, MagicMock

import pytest

from src.app.dtos.application_templates import (
    ApplicationTemplateData,
    ApplicationTemplateDetailsData,
    PublishedApplicationField,
    PublishedApplicationTemplate,
    PublishedApplicationTemplateSearchResult,
)
from src.app.use_cases.application_templates import (
    AddApplicationTemplate,
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    FailApplicationTemplateDescriptionGeneration,
    GenerateApplicationTemplateDescription,
    GetApplicationTemplate,
    GetApplicationTemplateDownloadUrl,
    ListPublishedApplicationTemplates,
    PublishApplicationTemplate,
    RegenerateApplicationTemplateDescription,
    SearchPublishedApplicationTemplates,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateDescriptionGenerationInProgress,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationFieldsConfig,
    InvalidApplicationTemplate,
)
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.users import Caller
from src.shared.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES
from src.shared.exceptions import ServiceUnavailable
from tests.consts import ADMIN_ID, USER_ID

ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)
USER = Caller(user_id=USER_ID)


def create_template(
    status: ApplicationTemplateStatus,
    fields: list[ApplicationTemplateField] | None = None,
    instructions: str | None = None,
):
    template = MagicMock()
    template.status = status
    template.fields = fields or []
    template.instructions = instructions
    template.description = None
    template.description_status = ApplicationTemplateDescriptionStatus.NOT_REQUESTED
    return template


def get_set_description_statuses(mock_application_templates_repo):
    return [call.args[2] for call in mock_application_templates_repo.set_description_status.await_args_list]


async def test_list_published_application_templates_hides_ai_settings(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    template = create_template(
        ApplicationTemplateStatus.PUBLISHED,
        [
            ApplicationTemplateField(
                name="department", label="Wydział", field_type=ApplicationFieldType.SELECT, options=["W4"]
            )
        ],
        "Instrukcje",
    )
    template.id = template_id
    template.name = "Wniosek"
    mock_application_templates_repo.list_templates.return_value = [template]

    use_case = ListPublishedApplicationTemplates(mock_session_maker, mock_application_templates_repo)

    templates = await use_case.execute(USER, None)

    mock_application_templates_repo.list_templates.assert_awaited_once_with(
        mock_opened_session, ApplicationTemplateStatus.PUBLISHED, None
    )
    assert templates == [
        PublishedApplicationTemplate(
            id=template_id,
            name="Wniosek",
            fields=[
                PublishedApplicationField(
                    name="department",
                    label="Wydział",
                    field_type=ApplicationFieldType.SELECT,
                    required=True,
                    options=["W4"],
                )
            ],
        )
    ]


async def test_list_published_application_templates_with_organization_filter(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    organization_filter = OrganizationFilter(next(uuid_generator), next(uuid_generator))
    mock_application_templates_repo.list_templates.return_value = []

    use_case = ListPublishedApplicationTemplates(mock_session_maker, mock_application_templates_repo)

    templates = await use_case.execute(USER, organization_filter)

    mock_application_templates_repo.list_templates.assert_awaited_once_with(
        mock_opened_session, ApplicationTemplateStatus.PUBLISHED, organization_filter
    )
    assert templates == []


async def test_get_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)

    use_case = GetApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    result = await use_case.execute(ADMIN, template_id)

    mock_application_templates_repo.get.assert_awaited_once_with(mock_opened_session, template_id)
    assert result == mock_application_templates_repo.get.return_value


async def test_get_application_template_as_normal_user(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    use_case = GetApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(AccessForbidden):
        await use_case.execute(USER, next(uuid_generator))

    mock_application_templates_repo.get.assert_not_awaited()


async def test_get_application_template_not_found(mock_session_maker, mock_application_templates_repo, uuid_generator):
    mock_application_templates_repo.get.return_value = None

    use_case = GetApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))


async def test_add_application_template(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_instructions_provider,
    uuid_generator,
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.add.return_value = template_id
    mock_application_template_instructions_provider.get_default_instructions.return_value = "Instrukcje"

    use_case = AddApplicationTemplate(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_instructions_provider,
    )

    upload_target = await use_case.execute(ADMIN, ApplicationTemplateData(name="Wniosek"))

    mock_application_templates_repo.add.assert_awaited_once_with(mock_opened_session, "Wniosek", "Instrukcje")
    mock_application_templates_storage.get_upload_target.assert_awaited_once_with(template_id)
    assert upload_target == mock_application_templates_storage.get_upload_target.return_value


async def test_confirm_application_template_upload(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.return_value = b"docx"
    mock_application_template_inspector.get_variables.return_value = {"paragraphs", "current_date", "student_id"}

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    result = await use_case.execute(ADMIN, template_id)

    mock_application_template_inspector.get_variables.assert_awaited_once_with(b"docx")
    mock_application_templates_repo.confirm_upload.assert_awaited_once_with(
        mock_opened_session, template_id, [ApplicationTemplateField(name="student_id", label="student_id")]
    )
    assert result == mock_application_templates_repo.confirm_upload.return_value


async def test_confirm_application_template_upload_changed_during_confirmation(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_template_inspector.get_variables.return_value = {"paragraphs"}
    mock_application_templates_repo.confirm_upload.return_value = None

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))


async def test_confirm_application_template_upload_not_found(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = None

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))


async def test_confirm_application_template_upload_already_confirmed(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_storage.get_template.assert_not_awaited()


async def test_confirm_application_template_upload_content_not_found(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.side_effect = ApplicationTemplateContentNotFound

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    with pytest.raises(ApplicationTemplateContentNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_repo.confirm_upload.assert_not_awaited()


async def test_confirm_application_template_upload_without_content_variable(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_template_inspector,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_template_inspector.get_variables.return_value = {"student_id"}

    use_case = ConfirmApplicationTemplateUpload(
        mock_session_maker,
        mock_application_templates_repo,
        mock_application_templates_storage,
        mock_application_template_inspector,
    )

    with pytest.raises(InvalidApplicationTemplate):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_repo.confirm_upload.assert_not_awaited()


async def test_update_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(
        ApplicationTemplateStatus.DRAFT, [ApplicationTemplateField(name="student_id", label="student_id")]
    )
    fields = [ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}")]

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    result = await use_case.execute(
        ADMIN, template_id, ApplicationTemplateDetailsData(name="Wniosek", instructions="Instrukcje", fields=fields)
    )

    mock_application_templates_repo.update_details.assert_awaited_once_with(
        mock_opened_session,
        template_id,
        ApplicationTemplateDetails(name="Wniosek", instructions="Instrukcje", fields=fields),
    )
    assert result == mock_application_templates_repo.update_details.return_value


async def test_update_application_template_with_invalid_fields(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(
        ApplicationTemplateStatus.DRAFT, [ApplicationTemplateField(name="student_id", label="student_id")]
    )

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(InvalidApplicationFieldsConfig):
        await use_case.execute(
            ADMIN,
            next(uuid_generator),
            ApplicationTemplateDetailsData(
                name="Wniosek", fields=[ApplicationTemplateField(name="other", label="Inne")]
            ),
        )

    mock_application_templates_repo.update_details.assert_not_awaited()


async def test_update_application_template_with_organization(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    organization_id = next(uuid_generator)
    suborganization_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    await use_case.execute(
        ADMIN,
        template_id,
        ApplicationTemplateDetailsData(
            name="Wniosek", fields=[], organizationId=organization_id, suborganizationId=suborganization_id
        ),
    )

    mock_application_templates_repo.update_details.assert_awaited_once_with(
        mock_opened_session,
        template_id,
        ApplicationTemplateDetails(
            name="Wniosek",
            instructions=None,
            fields=[],
            organization_id=organization_id,
            suborganization_id=suborganization_id,
        ),
    )


async def test_update_application_template_organization_not_found(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)
    mock_application_templates_repo.update_details.side_effect = OrganizationNotFound

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(OrganizationNotFound):
        await use_case.execute(
            ADMIN,
            next(uuid_generator),
            ApplicationTemplateDetailsData(name="Wniosek", fields=[], organizationId=next(uuid_generator)),
        )


@pytest.mark.parametrize("status", [ApplicationTemplateStatus.NOT_UPLOADED, ApplicationTemplateStatus.PUBLISHED])
async def test_update_application_template_not_draft(
    mock_session_maker, mock_application_templates_repo, uuid_generator, status
):
    mock_application_templates_repo.get.return_value = create_template(status)

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator), ApplicationTemplateDetailsData(name="Wniosek", fields=[]))


async def test_publish_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(
        ApplicationTemplateStatus.DRAFT, instructions="Instrukcje"
    )

    use_case = PublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    await use_case.execute(ADMIN, template_id)

    mock_application_templates_repo.set_status.assert_awaited_once_with(
        mock_opened_session, template_id, ApplicationTemplateStatus.PUBLISHED
    )


@pytest.mark.parametrize(
    ("status", "instructions"),
    [
        (ApplicationTemplateStatus.DRAFT, None),
        (ApplicationTemplateStatus.DRAFT, " "),
        (ApplicationTemplateStatus.NOT_UPLOADED, "Instrukcje"),
        (ApplicationTemplateStatus.PUBLISHED, "Instrukcje"),
    ],
)
async def test_publish_application_template_not_ready(
    mock_session_maker, mock_application_templates_repo, uuid_generator, status, instructions
):
    mock_application_templates_repo.get.return_value = create_template(status, instructions=instructions)

    use_case = PublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_repo.set_status.assert_not_awaited()


async def test_unpublish_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.PUBLISHED)

    use_case = UnpublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    await use_case.execute(ADMIN, template_id)

    mock_application_templates_repo.set_status.assert_awaited_once_with(
        mock_opened_session, template_id, ApplicationTemplateStatus.DRAFT
    )


async def test_unpublish_application_template_not_published(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)

    use_case = UnpublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))


async def test_delete_application_template(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    uuid_generator,
):
    template_id = next(uuid_generator)

    use_case = DeleteApplicationTemplate(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    await use_case.execute(ADMIN, template_id)

    mock_application_templates_repo.delete.assert_awaited_once_with(mock_opened_session, template_id)
    mock_application_templates_storage.delete_template.assert_awaited_once_with(template_id)


async def test_delete_application_template_not_found(
    mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, uuid_generator
):
    mock_application_templates_repo.delete.side_effect = ApplicationTemplateNotFound

    use_case = DeleteApplicationTemplate(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_storage.delete_template.assert_not_awaited()


async def test_get_application_template_download_url(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    uuid_generator,
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)
    mock_application_templates_storage.get_download_url.return_value = "http://storage.local/bucket/template"

    use_case = GetApplicationTemplateDownloadUrl(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    result = await use_case.execute(ADMIN, template_id)

    assert result == "http://storage.local/bucket/template"
    mock_application_templates_repo.get.assert_awaited_once_with(mock_opened_session, template_id)
    mock_application_templates_storage.get_download_url.assert_awaited_once_with(template_id)


async def test_get_application_template_download_url_not_found(
    mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, uuid_generator
):
    mock_application_templates_repo.get.return_value = None

    use_case = GetApplicationTemplateDownloadUrl(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_storage.get_download_url.assert_not_awaited()


async def test_get_application_template_download_url_not_uploaded(
    mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)

    use_case = GetApplicationTemplateDownloadUrl(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_storage.get_download_url.assert_not_awaited()


async def test_search_published_application_templates(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, mock_embedding_port, uuid_generator
):
    template_id = next(uuid_generator)
    template = create_template(ApplicationTemplateStatus.PUBLISHED, instructions="Instrukcje")
    template.id = template_id
    template.name = "Wniosek o urlop"
    template.description = "Wniosek o urlop dziekański."
    organization_filter = OrganizationFilter(next(uuid_generator))
    mock_embedding_port.embed_queries.return_value = [[0.1, 0.2]]
    mock_application_templates_repo.search_templates.return_value = [(template, 0.8)]

    use_case = SearchPublishedApplicationTemplates(
        mock_session_maker, mock_embedding_port, mock_application_templates_repo
    )

    results = await use_case.execute(USER, organization_filter, "urlop", 0.5)

    mock_embedding_port.embed_queries.assert_awaited_once_with(["urlop"])
    mock_application_templates_repo.search_templates.assert_awaited_once_with(
        mock_opened_session, ApplicationTemplateStatus.PUBLISHED, organization_filter, [0.1, 0.2], 0.5
    )
    assert results == [
        PublishedApplicationTemplateSearchResult(
            template=PublishedApplicationTemplate(
                id=template_id, name="Wniosek o urlop", description="Wniosek o urlop dziekański.", fields=[]
            ),
            score=0.8,
        )
    ]


async def test_search_published_application_templates_without_login(
    mock_session_maker, mock_application_templates_repo, mock_embedding_port
):
    use_case = SearchPublishedApplicationTemplates(
        mock_session_maker, mock_embedding_port, mock_application_templates_repo
    )

    with pytest.raises(LoginRequired):
        await use_case.execute(Caller(None), None, "urlop", 0.5)

    mock_embedding_port.embed_queries.assert_not_awaited()


def create_regenerate_application_template_description(mock_session_maker, mock_application_templates_repo):
    mock_scheduler = AsyncMock()
    use_case = RegenerateApplicationTemplateDescription(
        session_maker=mock_session_maker,
        application_templates_repo=mock_application_templates_repo,
        description_generation_scheduler=mock_scheduler,
    )
    return use_case, mock_scheduler


async def test_regenerate_application_template_description_success(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)

    use_case, mock_scheduler = create_regenerate_application_template_description(
        mock_session_maker, mock_application_templates_repo
    )

    await use_case.execute(ADMIN, template_id)

    assert get_set_description_statuses(mock_application_templates_repo) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS
    ]
    mock_scheduler.schedule_application_template_description_generation.assert_awaited_once_with(
        mock_opened_session, template_id
    )


async def test_regenerate_application_template_description_as_normal_user(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    use_case, mock_scheduler = create_regenerate_application_template_description(
        mock_session_maker, mock_application_templates_repo
    )

    with pytest.raises(AccessForbidden):
        await use_case.execute(USER, next(uuid_generator))

    mock_scheduler.schedule_application_template_description_generation.assert_not_awaited()


async def test_regenerate_application_template_description_not_found(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = None

    use_case, mock_scheduler = create_regenerate_application_template_description(
        mock_session_maker, mock_application_templates_repo
    )

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_scheduler.schedule_application_template_description_generation.assert_not_awaited()


async def test_regenerate_application_template_description_not_draft(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.PUBLISHED)

    use_case, mock_scheduler = create_regenerate_application_template_description(
        mock_session_maker, mock_application_templates_repo
    )

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_scheduler.schedule_application_template_description_generation.assert_not_awaited()


async def test_regenerate_application_template_description_already_in_progress(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    template = create_template(ApplicationTemplateStatus.DRAFT)
    template.description_status = ApplicationTemplateDescriptionStatus.IN_PROGRESS
    mock_application_templates_repo.get.return_value = template

    use_case, mock_scheduler = create_regenerate_application_template_description(
        mock_session_maker, mock_application_templates_repo
    )

    with pytest.raises(ApplicationTemplateDescriptionGenerationInProgress):
        await use_case.execute(ADMIN, next(uuid_generator))

    mock_application_templates_repo.set_description_status.assert_not_awaited()
    mock_scheduler.schedule_application_template_description_generation.assert_not_awaited()


def create_generate_application_template_description(
    mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
):
    mock_inspector = AsyncMock()
    mock_inspector.get_text.return_value = "Dziekan Wydziału\n{{ student_name }}"
    mock_description_writer = AsyncMock()
    mock_description_writer.write.return_value = "Wniosek o urlop dziekański."

    use_case = GenerateApplicationTemplateDescription(
        session_maker=mock_session_maker,
        application_templates_repo=mock_application_templates_repo,
        application_templates_storage=mock_application_templates_storage,
        application_template_inspector=mock_inspector,
        description_writer=mock_description_writer,
        texts_embedder=mock_embedding_port,
    )
    return use_case, mock_description_writer


def create_template_to_describe():
    template = create_template(
        ApplicationTemplateStatus.DRAFT,
        [ApplicationTemplateField(name="student_name", label="Imię i nazwisko")],
        "Sporządź wniosek o urlop dziekański.",
    )
    template.name = "Wniosek o urlop"
    template.description_status = ApplicationTemplateDescriptionStatus.IN_PROGRESS
    return template


async def test_generate_application_template_description_success(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template_to_describe()
    mock_application_templates_storage.get_template.return_value = b"docx"
    mock_embedding_port.embed_texts.return_value = [[0.1, 0.2]]

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )

    await use_case.execute(template_id)

    mock_application_templates_storage.get_template.assert_awaited_once_with(template_id)
    description_source = mock_description_writer.write.await_args.args[0]
    assert description_source.name == "Wniosek o urlop"
    assert description_source.instructions == "Sporządź wniosek o urlop dziekański."
    assert description_source.field_labels == ["Imię i nazwisko"]
    assert description_source.content == "Dziekan Wydziału\n{{ student_name }}"
    mock_embedding_port.embed_texts.assert_awaited_once_with(["Wniosek o urlop dziekański."])
    mock_application_templates_repo.set_generated_description.assert_awaited_once_with(
        mock_opened_session, template_id, "Wniosek o urlop dziekański.", [0.1, 0.2]
    )


async def test_generate_application_template_description_template_not_found(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = None

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )

    await use_case.execute(next(uuid_generator))

    mock_description_writer.write.assert_not_awaited()


async def test_generate_application_template_description_already_generated(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    template = create_template_to_describe()
    template.description_status = ApplicationTemplateDescriptionStatus.GENERATED
    mock_application_templates_repo.get.return_value = template

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )

    await use_case.execute(next(uuid_generator))

    mock_description_writer.write.assert_not_awaited()
    mock_application_templates_repo.set_description_status.assert_not_awaited()


async def test_generate_application_template_description_service_unavailable(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template_to_describe()

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )
    mock_description_writer.write.side_effect = ServiceUnavailable()

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(next(uuid_generator))

    assert get_set_description_statuses(mock_application_templates_repo) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS,
        ApplicationTemplateDescriptionStatus.FAILED,
    ]
    mock_application_templates_repo.set_generated_description.assert_not_awaited()


async def test_generate_application_template_description_content_not_found(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template_to_describe()
    mock_application_templates_storage.get_template.side_effect = ApplicationTemplateContentNotFound()

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )

    with pytest.raises(ApplicationTemplateContentNotFound):
        await use_case.execute(next(uuid_generator))

    assert get_set_description_statuses(mock_application_templates_repo) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS,
        ApplicationTemplateDescriptionStatus.FAILED,
    ]
    mock_description_writer.write.assert_not_awaited()


async def test_generate_application_template_description_template_removed(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template_to_describe()
    mock_embedding_port.embed_texts.return_value = [[0.1, 0.2]]
    mock_application_templates_repo.set_generated_description.side_effect = ApplicationTemplateNotFound()

    use_case, _ = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )

    await use_case.execute(next(uuid_generator))


async def test_generate_application_template_description_template_removed_before_failure(
    mock_session_maker,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_embedding_port,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template_to_describe()
    mock_application_templates_repo.set_description_status.side_effect = [None, ApplicationTemplateNotFound()]

    use_case, mock_description_writer = create_generate_application_template_description(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, mock_embedding_port
    )
    mock_description_writer.write.side_effect = ServiceUnavailable()

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(next(uuid_generator))


async def test_fail_application_template_description_generation_deliveries_limit_exceeded(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    use_case = FailApplicationTemplateDescriptionGeneration(
        session_maker=mock_session_maker, application_templates_repo=mock_application_templates_repo
    )

    is_failed = await use_case.execute(
        next(uuid_generator), MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES + 1
    )

    assert is_failed
    assert get_set_description_statuses(mock_application_templates_repo) == [
        ApplicationTemplateDescriptionStatus.FAILED
    ]


async def test_fail_application_template_description_generation_template_removed(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.set_description_status.side_effect = ApplicationTemplateNotFound()
    use_case = FailApplicationTemplateDescriptionGeneration(
        session_maker=mock_session_maker, application_templates_repo=mock_application_templates_repo
    )

    is_failed = await use_case.execute(
        next(uuid_generator), MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES + 1
    )

    assert is_failed


async def test_fail_application_template_description_generation_deliveries_limit_not_exceeded(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    use_case = FailApplicationTemplateDescriptionGeneration(
        session_maker=mock_session_maker, application_templates_repo=mock_application_templates_repo
    )

    is_failed = await use_case.execute(next(uuid_generator), MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES)

    assert not is_failed
    mock_application_templates_repo.set_description_status.assert_not_awaited()
