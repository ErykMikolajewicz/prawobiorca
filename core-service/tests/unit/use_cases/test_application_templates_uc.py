from unittest.mock import MagicMock

import pytest

from src.app.dtos.application_templates import (
    ApplicationTemplateData,
    ApplicationTemplateDetailsData,
    PublishedApplicationField,
    PublishedApplicationTemplate,
)
from src.app.use_cases.application_templates import (
    AddApplicationTemplate,
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    GetApplicationTemplate,
    GetApplicationTemplateDownloadUrl,
    ListPublishedApplicationTemplates,
    PublishApplicationTemplate,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from src.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationFieldsConfig,
    InvalidApplicationTemplate,
)
from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)


def create_template(
    status: ApplicationTemplateStatus,
    fields: list[ApplicationTemplateField] | None = None,
    instructions: str | None = None,
):
    template = MagicMock()
    template.status = status
    template.fields = fields or []
    template.instructions = instructions
    return template


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

    templates = await use_case.execute()

    mock_application_templates_repo.list_templates.assert_awaited_once_with(
        mock_opened_session, ApplicationTemplateStatus.PUBLISHED
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


async def test_get_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)

    use_case = GetApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    result = await use_case.execute(template_id)

    mock_application_templates_repo.get.assert_awaited_once_with(mock_opened_session, template_id)
    assert result == mock_application_templates_repo.get.return_value


async def test_get_application_template_not_found(mock_session_maker, mock_application_templates_repo, uuid_generator):
    mock_application_templates_repo.get.return_value = None

    use_case = GetApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateNotFound):
        await use_case.execute(next(uuid_generator))


async def test_add_application_template(
    mock_session_maker,
    mock_opened_session,
    mock_application_templates_repo,
    mock_application_templates_storage,
    uuid_generator,
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.add.return_value = template_id

    use_case = AddApplicationTemplate(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    upload_target = await use_case.execute(ApplicationTemplateData(name="Wniosek"))

    mock_application_templates_repo.add.assert_awaited_once_with(mock_opened_session, "Wniosek")
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

    result = await use_case.execute(template_id)

    mock_application_template_inspector.get_variables.assert_awaited_once_with(b"docx")
    mock_application_templates_repo.set_fields.assert_awaited_once_with(
        mock_opened_session, template_id, [ApplicationTemplateField(name="student_id", label="student_id")]
    )
    mock_application_templates_repo.set_status.assert_awaited_once_with(
        mock_opened_session, template_id, ApplicationTemplateStatus.DRAFT
    )
    assert result == mock_application_templates_repo.set_status.return_value


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
        await use_case.execute(next(uuid_generator))


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
        await use_case.execute(next(uuid_generator))

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
        await use_case.execute(next(uuid_generator))

    mock_application_templates_repo.set_status.assert_not_awaited()


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
        await use_case.execute(next(uuid_generator))

    mock_application_templates_repo.set_fields.assert_not_awaited()
    mock_application_templates_repo.set_status.assert_not_awaited()


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
        template_id, ApplicationTemplateDetailsData(name="Wniosek", instructions="Instrukcje", fields=fields)
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
            next(uuid_generator),
            ApplicationTemplateDetailsData(
                name="Wniosek", fields=[ApplicationTemplateField(name="other", label="Inne")]
            ),
        )

    mock_application_templates_repo.update_details.assert_not_awaited()


@pytest.mark.parametrize("status", [ApplicationTemplateStatus.NOT_UPLOADED, ApplicationTemplateStatus.PUBLISHED])
async def test_update_application_template_not_draft(
    mock_session_maker, mock_application_templates_repo, uuid_generator, status
):
    mock_application_templates_repo.get.return_value = create_template(status)

    use_case = UpdateApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(next(uuid_generator), ApplicationTemplateDetailsData(name="Wniosek", fields=[]))


async def test_publish_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(
        ApplicationTemplateStatus.DRAFT, instructions="Instrukcje"
    )

    use_case = PublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    await use_case.execute(template_id)

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
        await use_case.execute(next(uuid_generator))

    mock_application_templates_repo.set_status.assert_not_awaited()


async def test_unpublish_application_template(
    mock_session_maker, mock_opened_session, mock_application_templates_repo, uuid_generator
):
    template_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.PUBLISHED)

    use_case = UnpublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    await use_case.execute(template_id)

    mock_application_templates_repo.set_status.assert_awaited_once_with(
        mock_opened_session, template_id, ApplicationTemplateStatus.DRAFT
    )


async def test_unpublish_application_template_not_published(
    mock_session_maker, mock_application_templates_repo, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.DRAFT)

    use_case = UnpublishApplicationTemplate(mock_session_maker, mock_application_templates_repo)

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(next(uuid_generator))


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

    await use_case.execute(template_id)

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
        await use_case.execute(next(uuid_generator))

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

    result = await use_case.execute(template_id)

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
        await use_case.execute(next(uuid_generator))

    mock_application_templates_storage.get_download_url.assert_not_awaited()


async def test_get_application_template_download_url_not_uploaded(
    mock_session_maker, mock_application_templates_repo, mock_application_templates_storage, uuid_generator
):
    mock_application_templates_repo.get.return_value = create_template(ApplicationTemplateStatus.NOT_UPLOADED)

    use_case = GetApplicationTemplateDownloadUrl(
        mock_session_maker, mock_application_templates_repo, mock_application_templates_storage
    )

    with pytest.raises(ApplicationTemplateInInvalidState):
        await use_case.execute(next(uuid_generator))

    mock_application_templates_storage.get_download_url.assert_not_awaited()
