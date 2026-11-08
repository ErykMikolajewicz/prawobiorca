from io import BytesIO
from unittest.mock import ANY
from uuid import UUID

from docx import Document
from fastapi import status
from sqlalchemy import delete, select

from src.app.dtos.application_templates import ApplicationTemplateUploadTarget
from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.infrastructure.relational_db.schemas.application_templates import application_templates_table
from src.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table
from src.shared.consts import APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME
from tests.consts import UNKNOWN_ID
from tests.integration.fixtures.ai_services import DESCRIPTION_VECTOR, QUERY_VECTOR, UNRELATED_VECTOR
from tests.integration.fixtures.application_templates import insert_application_template
from tests.integration.fixtures.organizations import insert_organization, insert_suborganization
from tests.integration.fixtures.tasks import get_scheduled_task_names

PUBLISHED = ApplicationTemplateStatus.PUBLISHED

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


async def get_template(session_maker, template_id):
    async with session_maker() as session:
        result = await session.execute(
            select(application_templates_table).where(application_templates_table.c.id == template_id)
        )
    return result.one()


async def test_get_published_application_templates(user_client, session_maker):
    async with session_maker.begin() as session:
        published_id = await insert_application_template(
            session, "Published", PUBLISHED, fields=FIELDS, instructions="Instrukcje"
        )
        await insert_application_template(session, "Draft", fields=FIELDS)

    response = await user_client.get("/api/application-templates/published")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(published_id),
            "name": "Published",
            "description": None,
            "fields": [{key: value for key, value in field.items() if key != "passToAi"} for field in FIELDS_JSON],
        }
    ]


async def test_get_application_templates(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session)

    response = await admin_client.get("/api/application-templates")

    assert response.status_code == status.HTTP_200_OK
    assert [template["id"] for template in response.json()] == [str(template_id)]


async def test_get_application_templates_as_normal_user(user_client):
    response = await user_client.get("/api/application-templates")

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_application_template(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS, instructions="Instrukcje")

    response = await admin_client.get(f"/api/application-templates/{template_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(template_id),
        "createDate": ANY,
        "name": "Wniosek",
        "status": "DRAFT",
        "fields": FIELDS_JSON,
        "instructions": "Instrukcje",
        "description": None,
        "descriptionStatus": "NOT_REQUESTED",
        "organizationId": None,
        "suborganizationId": None,
    }


async def test_get_application_template_not_found(admin_client):
    response = await admin_client.get(f"/api/application-templates/{UNKNOWN_ID}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_add_application_template(admin_client, session_maker, mock_application_templates_storage):
    mock_application_templates_storage.get_upload_target.side_effect = lambda id_: ApplicationTemplateUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    response = await admin_client.post("/api/application-templates", json={"name": "Wniosek"})

    assert response.status_code == status.HTTP_201_CREATED
    template = await get_template(session_maker, UUID(response.json()["id"]))

    assert template.name == "Wniosek"
    assert template.status == ApplicationTemplateStatus.NOT_UPLOADED
    assert template.fields == []
    assert template.instructions


async def test_confirm_application_template_upload(admin_client, session_maker, mock_application_templates_storage):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, status=ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.return_value = create_docx_template()

    response = await admin_client.post(f"/api/application-templates/{template_id}/confirm-upload")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "DRAFT"
    assert response.json()["fields"] == FIELDS_JSON


async def test_confirm_application_template_upload_invalid_file(
    admin_client, session_maker, mock_application_templates_storage
):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, status=ApplicationTemplateStatus.NOT_UPLOADED)
    mock_application_templates_storage.get_template.return_value = b"not a docx"

    response = await admin_client.post(f"/api/application-templates/{template_id}/confirm-upload")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_get_application_template_download_url(admin_client, session_maker, mock_application_templates_storage):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS)
        not_uploaded_template_id = await insert_application_template(
            session, status=ApplicationTemplateStatus.NOT_UPLOADED
        )
    mock_application_templates_storage.get_download_url.return_value = "http://storage.local/bucket/template"

    response = await admin_client.get(f"/api/application-templates/{template_id}/download-url")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "http://storage.local/bucket/template"

    response = await admin_client.get(f"/api/application-templates/{not_uploaded_template_id}/download-url")

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_update_application_template(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)
        template_id = await insert_application_template(
            session, fields=FIELDS, description="Wniosek o urlop.", description_vector=UNRELATED_VECTOR
        )
    new_fields = [
        {**FIELDS_JSON[0], "label": "Wydział", "fieldType": "SELECT", "options": ["W4", "W8"], "defaultValue": "W4"},
        {**FIELDS_JSON[1], "label": "Numer albumu", "pattern": r"\d{6}", "passToAi": False},
    ]

    response = await admin_client.put(
        f"/api/application-templates/{template_id}",
        json={
            "name": "Nowa nazwa",
            "instructions": "Instrukcje",
            "description": "Wniosek o stypendium.",
            "fields": new_fields,
            "organizationId": str(organization_id),
            "suborganizationId": str(suborganization_id),
        },
    )

    assert response.status_code == status.HTTP_200_OK
    template = await get_template(session_maker, template_id)

    assert template.name == "Nowa nazwa"
    assert template.instructions == "Instrukcje"
    assert template.description == "Wniosek o stypendium."
    assert list(template.description_vector) == DESCRIPTION_VECTOR
    assert template.fields[0].field_type == ApplicationFieldType.SELECT
    assert template.fields[1].pass_to_ai is False
    assert template.organization_id == organization_id
    assert template.suborganization_id == suborganization_id


async def test_update_application_template_with_invalid_fields(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS)

    response = await admin_client.put(
        f"/api/application-templates/{template_id}", json={"name": "Wniosek", "fields": [FIELDS_JSON[0]]}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_update_application_template_with_not_existing_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS)

    response = await admin_client.put(
        f"/api/application-templates/{template_id}",
        json={"name": "Wniosek", "fields": FIELDS_JSON, "organizationId": str(UNKNOWN_ID)},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_application_template_with_suborganization_of_other_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        other_organization_id = await insert_organization(session)
        other_suborganization_id = await insert_suborganization(session, other_organization_id)
        template_id = await insert_application_template(session, fields=FIELDS)

    response = await admin_client.put(
        f"/api/application-templates/{template_id}",
        json={
            "name": "Wniosek",
            "fields": FIELDS_JSON,
            "organizationId": str(organization_id),
            "suborganizationId": str(other_suborganization_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_application_template_with_suborganization_without_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS)

    response = await admin_client.put(
        f"/api/application-templates/{template_id}",
        json={"name": "Wniosek", "fields": FIELDS_JSON, "suborganizationId": str(UNKNOWN_ID)},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_publish_and_unpublish_application_template(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS, instructions="Instrukcje")

    response = await admin_client.post(f"/api/application-templates/{template_id}/publish")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "PUBLISHED"

    response = await admin_client.post(f"/api/application-templates/{template_id}/unpublish")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "DRAFT"


async def test_publish_application_template_without_instructions(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS)

    response = await admin_client.post(f"/api/application-templates/{template_id}/publish")

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_delete_application_template(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session)

    response = await admin_client.delete(f"/api/application-templates/{template_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await admin_client.delete(f"/api/application-templates/{template_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_published_application_templates_filtered_by_organization(user_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        other_organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id, "Wydział Prawa")
        other_suborganization_id = await insert_suborganization(session, organization_id, "Wydział Chemii")

        await insert_application_template(session, "General", PUBLISHED)
        await insert_application_template(session, "Organization", PUBLISHED, organization_id=organization_id)
        await insert_application_template(
            session, "Law", PUBLISHED, organization_id=organization_id, suborganization_id=suborganization_id
        )
        await insert_application_template(
            session,
            "Chemistry",
            PUBLISHED,
            organization_id=organization_id,
            suborganization_id=other_suborganization_id,
        )
        await insert_application_template(
            session, "Other organization", PUBLISHED, organization_id=other_organization_id
        )

    response = await user_client.get("/api/application-templates/published")

    assert response.status_code == status.HTTP_200_OK
    assert {template["name"] for template in response.json()} == {
        "General",
        "Organization",
        "Law",
        "Chemistry",
        "Other organization",
    }

    response = await user_client.get(
        "/api/application-templates/published", params={"organizationId": str(organization_id)}
    )

    assert response.status_code == status.HTTP_200_OK
    assert {template["name"] for template in response.json()} == {"General", "Organization", "Law", "Chemistry"}

    response = await user_client.get(
        "/api/application-templates/published",
        params={"organizationId": str(organization_id), "suborganizationId": str(suborganization_id)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {template["name"] for template in response.json()} == {"General", "Organization", "Law"}


async def test_delete_suborganization_keeps_application_template_in_organization(session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)
        template_id = await insert_application_template(
            session, organization_id=organization_id, suborganization_id=suborganization_id
        )

    async with session_maker.begin() as session:
        await session.execute(delete(suborganizations_table).where(suborganizations_table.c.id == suborganization_id))

    template = await get_template(session_maker, template_id)

    assert (template.organization_id, template.suborganization_id) == (organization_id, None)


async def test_delete_organization_makes_application_template_general(session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)
        template_id = await insert_application_template(
            session, organization_id=organization_id, suborganization_id=suborganization_id
        )

    async with session_maker.begin() as session:
        await session.execute(delete(organizations_table).where(organizations_table.c.id == organization_id))

    template = await get_template(session_maker, template_id)

    assert (template.organization_id, template.suborganization_id) == (None, None)


async def test_search_published_application_templates_by_name(user_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session, short_name="PWr")
        other_organization_id = await insert_organization(session)
        matching_id = await insert_application_template(
            session,
            "Wniosek o urlop dziekański",
            PUBLISHED,
            organization_id=organization_id,
            description="Wniosek o urlop.",
        )
        await insert_application_template(session, "Wniosek o stypendium socjalne", PUBLISHED)
        await insert_application_template(session, "Wniosek o urlop dziekański - szkic")
        await insert_application_template(
            session, "Wniosek o urlop dziekański - UWr", PUBLISHED, organization_id=other_organization_id
        )

    response = await user_client.get(
        "/api/application-templates/published/search",
        params={"query": "urlop dziekanski", "aiAssisted": False, "organizationId": str(organization_id)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(matching_id),
            "name": "Wniosek o urlop dziekański",
            "description": "Wniosek o urlop.",
            "fields": [],
        }
    ]


async def test_search_published_application_templates_ai_assisted(user_client, session_maker):
    async with session_maker.begin() as session:
        await insert_application_template(session, "Wniosek o urlop", PUBLISHED, description_vector=UNRELATED_VECTOR)
        await insert_application_template(session, "Podanie o urlop", PUBLISHED, description_vector=QUERY_VECTOR)
        await insert_application_template(session, "Wniosek o stypendium", PUBLISHED)
        await insert_application_template(session, "Szkic", description_vector=QUERY_VECTOR)

    response = await user_client.get(
        "/api/application-templates/published/search", params={"query": "urlop ", "aiAssisted": True}
    )

    assert response.status_code == status.HTTP_200_OK
    assert [template["name"] for template in response.json()] == [
        "Podanie o urlop",
        "Wniosek o urlop",
        "Wniosek o stypendium",
    ]


async def test_search_published_application_templates_empty_query(user_client):
    response = await user_client.get("/api/application-templates/published/search", params={"query": ""})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_search_published_application_templates_unlogged(client):
    response = await client.get("/api/application-templates/published/search", params={"query": "urlop"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_regenerate_application_template_description(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, fields=FIELDS, instructions="Instrukcje")

    response = await admin_client.post(f"/api/application-templates/{template_id}/description-generation")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert await get_scheduled_task_names(session_maker) == [APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME]
    template = await get_template(session_maker, template_id)
    assert template.description_status == ApplicationTemplateDescriptionStatus.IN_PROGRESS

    response = await admin_client.post(f"/api/application-templates/{template_id}/description-generation")

    assert response.status_code == status.HTTP_409_CONFLICT

    response = await admin_client.post(f"/api/application-templates/{UNKNOWN_ID}/description-generation")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_regenerate_published_application_template_description(admin_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session, status=PUBLISHED, instructions="Instrukcje")

    response = await admin_client.post(f"/api/application-templates/{template_id}/description-generation")

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_regenerate_application_template_description_as_normal_user(user_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(session)

    response = await user_client.post(f"/api/application-templates/{template_id}/description-generation")

    assert response.status_code == status.HTTP_403_FORBIDDEN
