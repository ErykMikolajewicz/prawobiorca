from io import BytesIO
from unittest.mock import ANY
from uuid import UUID

from docx import Document
from fastapi import status
from sqlalchemy import delete, insert, select

from src.app.dtos.application_templates import ApplicationTemplateUploadTarget
from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.infrastructure.relational_db.schemas.application_templates import application_templates_table
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN

FIELDS = [
    ApplicationTemplateField(name="department", label="department"),
    ApplicationTemplateField(name="student_id", label="student_id"),
]

FIELDS_JSON = [
    {
        "name": "department",
        "label": "department",
        "fieldType": "TEXT",
        "required": True,
        "passToAi": True,
        "defaultValue": None,
        "pattern": None,
        "options": [],
    },
    {
        "name": "student_id",
        "label": "student_id",
        "fieldType": "TEXT",
        "required": True,
        "passToAi": True,
        "defaultValue": None,
        "pattern": None,
        "options": [],
    },
]


def create_docx_template() -> bytes:
    document = Document()
    document.add_paragraph("{{ student_id }}, {{ department }}, {{ current_date }}")
    document.add_paragraph("{%p for paragraph in paragraphs %}")
    document.add_paragraph("{{ paragraph }}")
    document.add_paragraph("{%p endfor %}")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def insert_template(
    session_maker,
    name: str = "Wniosek",
    template_status: ApplicationTemplateStatus = ApplicationTemplateStatus.DRAFT,
    fields: list[ApplicationTemplateField] | None = None,
    instructions: str | None = None,
):
    async with session_maker.begin() as session:
        statement = (
            insert(application_templates_table)
            .values(name=name, status=template_status, fields=fields or [], instructions=instructions)
            .returning(application_templates_table.c.id)
        )
        return await session.scalar(statement)


async def delete_templates(session_maker, *template_ids):
    async with session_maker.begin() as session:
        await session.execute(
            delete(application_templates_table).where(application_templates_table.c.id.in_(template_ids))
        )


async def test_get_published_application_templates(
    client, override_session_maker, session_maker, override_authorize_normal_user
):
    published_id = await insert_template(
        session_maker, "Published", ApplicationTemplateStatus.PUBLISHED, FIELDS, "Instrukcje"
    )
    draft_id = await insert_template(session_maker, "Draft", ApplicationTemplateStatus.DRAFT, FIELDS)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.get("/api/application-templates")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(published_id),
                "name": "Published",
                "fields": [{key: value for key, value in field.items() if key != "passToAi"} for field in FIELDS_JSON],
            }
        ]
    finally:
        await delete_templates(session_maker, published_id, draft_id)


async def test_get_application_templates_as_admin(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS, instructions="Instrukcje")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.get("/api/admin/application-templates")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(template_id),
                "createDate": ANY,
                "name": "Wniosek",
                "status": "DRAFT",
                "fields": FIELDS_JSON,
                "instructions": "Instrukcje",
            }
        ]
    finally:
        await delete_templates(session_maker, template_id)


async def test_get_application_template_as_admin(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS, instructions="Instrukcje")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.get(f"/api/admin/application-templates/{template_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(template_id),
            "createDate": ANY,
            "name": "Wniosek",
            "status": "DRAFT",
            "fields": FIELDS_JSON,
            "instructions": "Instrukcje",
        }
    finally:
        await delete_templates(session_maker, template_id)

    response = await client.get(f"/api/admin/application-templates/{template_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_application_templates_as_normal_user(client, override_session_maker, override_authorize_normal_user):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get("/api/admin/application-templates")

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_add_application_template(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_application_templates_storage,
    mock_application_templates_storage,
):
    mock_application_templates_storage.get_upload_target.side_effect = lambda id_: ApplicationTemplateUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/admin/application-templates", json={"name": "Wniosek"})

    assert response.status_code == status.HTTP_201_CREATED
    template_id = UUID(response.json()["id"])

    try:
        async with session_maker() as session:
            result = await session.execute(
                select(application_templates_table).where(application_templates_table.c.id == template_id)
            )
        template = result.one()

        assert template.name == "Wniosek"
        assert template.status == ApplicationTemplateStatus.NOT_UPLOADED
        assert template.fields == []
    finally:
        await delete_templates(session_maker, template_id)


async def test_confirm_application_template_upload(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_application_templates_storage,
    mock_application_templates_storage,
):
    template_id = await insert_template(session_maker, template_status=ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.return_value = create_docx_template()

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/admin/application-templates/{template_id}/confirm-upload")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "DRAFT"
        assert response.json()["fields"] == FIELDS_JSON
        mock_application_templates_storage.get_template.assert_awaited_once_with(template_id)
    finally:
        await delete_templates(session_maker, template_id)


async def test_confirm_application_template_upload_invalid_file(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_application_templates_storage,
    mock_application_templates_storage,
):
    template_id = await insert_template(session_maker, template_status=ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.return_value = b"not a docx"

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/admin/application-templates/{template_id}/confirm-upload")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    finally:
        await delete_templates(session_maker, template_id)


async def test_get_application_template_download_url(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_application_templates_storage,
    mock_application_templates_storage,
):
    template_id = await insert_template(session_maker, fields=FIELDS)
    not_uploaded_template_id = await insert_template(
        session_maker, template_status=ApplicationTemplateStatus.NOT_UPLOADED
    )
    mock_application_templates_storage.get_download_url.return_value = "http://storage.local/bucket/template"

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.get(f"/api/admin/application-templates/{template_id}/download-url")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == "http://storage.local/bucket/template"
        mock_application_templates_storage.get_download_url.assert_awaited_once_with(template_id)

        response = await client.get(f"/api/admin/application-templates/{not_uploaded_template_id}/download-url")

        assert response.status_code == status.HTTP_409_CONFLICT
    finally:
        await delete_templates(session_maker, template_id, not_uploaded_template_id)


async def test_update_application_template(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS)
    new_fields = [
        {**FIELDS_JSON[0], "label": "Wydział", "fieldType": "SELECT", "options": ["W4", "W8"], "defaultValue": "W4"},
        {**FIELDS_JSON[1], "label": "Numer albumu", "pattern": r"\d{6}", "passToAi": False},
    ]

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.put(
            f"/api/admin/application-templates/{template_id}",
            json={"name": "Nowa nazwa", "instructions": "Instrukcje", "fields": new_fields},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(template_id),
            "createDate": ANY,
            "name": "Nowa nazwa",
            "status": "DRAFT",
            "fields": new_fields,
            "instructions": "Instrukcje",
        }

        async with session_maker() as session:
            fields = await session.scalar(
                select(application_templates_table.c.fields).where(application_templates_table.c.id == template_id)
            )
        assert fields[0].field_type == ApplicationFieldType.SELECT
        assert fields[1].pass_to_ai is False
    finally:
        await delete_templates(session_maker, template_id)


async def test_update_application_template_with_invalid_fields(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.put(
            f"/api/admin/application-templates/{template_id}",
            json={"name": "Wniosek", "fields": [FIELDS_JSON[0]]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    finally:
        await delete_templates(session_maker, template_id)


async def test_publish_and_unpublish_application_template(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS, instructions="Instrukcje")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/admin/application-templates/{template_id}/publish")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "PUBLISHED"

        response = await client.post(f"/api/admin/application-templates/{template_id}/unpublish")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "DRAFT"
    finally:
        await delete_templates(session_maker, template_id)


async def test_publish_application_template_without_instructions(
    client, override_session_maker, session_maker, override_authorize_admin_user
):
    template_id = await insert_template(session_maker, fields=FIELDS)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/admin/application-templates/{template_id}/publish")

        assert response.status_code == status.HTTP_409_CONFLICT
    finally:
        await delete_templates(session_maker, template_id)


async def test_delete_application_template(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_application_templates_storage,
    mock_application_templates_storage,
):
    template_id = await insert_template(session_maker)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/admin/application-templates/{template_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_application_templates_storage.delete_template.assert_awaited_once_with(template_id)

    response = await client.delete(f"/api/admin/application-templates/{template_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
