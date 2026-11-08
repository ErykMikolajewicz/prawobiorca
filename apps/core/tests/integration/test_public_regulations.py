import math
from unittest.mock import ANY
from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import select

from core_service.application.dtos.regulations import RegulationUploadTarget
from core_service.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationPreparationStatus,
    RegulationType,
)
from core_service.infrastructure.relational_db.repositories.sections import PRIMARY_CHUNK_SCORE_WEIGHT
from core_service.infrastructure.relational_db.schemas.regulations import regulations_table
from core_service.shared.consts import REGULATION_DESCRIPTION_GENERATION_TASK_NAME, VECTOR_LENGTH
from tests.consts import UNKNOWN_ID, USER_ID
from tests.integration.fixtures.ai_services import QUERY_VECTOR, UNRELATED_VECTOR
from tests.integration.fixtures.organizations import insert_organization, insert_suborganization
from tests.integration.fixtures.regulations import insert_regulation, insert_section
from tests.integration.fixtures.tasks import get_scheduled_task_names

UNRELATED_SIMILARITY = 1 / math.sqrt(VECTOR_LENGTH)
HALF_RELATED_VECTOR = [1.0] * (VECTOR_LENGTH // 2) + [0.0] * (VECTOR_LENGTH // 2)


async def test_get_public_regulations(client, session_maker, user):
    async with session_maker.begin() as session:
        public_act_id = await insert_regulation(session, None, "Public act.pdf", regulation_type=RegulationType.ACT)
        await insert_regulation(session, None, "Public decree.pdf", regulation_type=RegulationType.DECREE)
        await insert_regulation(session, USER_ID, "Private act.pdf", regulation_type=RegulationType.ACT)

    response = await client.get("/api/regulations", params={"documentType": RegulationType.ACT})

    assert response.status_code == status.HTTP_200_OK
    assert [regulation["id"] for regulation in response.json()] == [str(public_act_id)]


async def test_get_public_regulation(client, session_maker, user):
    async with session_maker.begin() as session:
        public_regulation_id = await insert_regulation(
            session,
            None,
            "Public act.pdf",
            preparation_status=RegulationPreparationStatus.PREPARED,
            regulation_type=RegulationType.ACT,
        )
        private_regulation_id = await insert_regulation(session, USER_ID, "Private act.pdf")

    response = await client.get(f"/api/regulations/{public_regulation_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": str(public_regulation_id),
        "createDate": ANY,
        "presentationName": "Public act.pdf",
        "description": None,
        "regulationType": RegulationType.ACT,
        "preparationStatus": RegulationPreparationStatus.PREPARED,
        "descriptionStatus": RegulationDescriptionStatus.NOT_REQUESTED,
        "organizationId": None,
        "suborganizationId": None,
    }

    response = await client.get(f"/api/regulations/{private_regulation_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_search_regulation_documents(client, session_maker, user):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)
        other_regulation_id = await insert_regulation(session, USER_ID)

        matching_section_id = await insert_section(session, regulation_id, "Matching section", [QUERY_VECTOR])
        await insert_section(session, regulation_id, "Unrelated section", [UNRELATED_VECTOR], section_order=1)
        await insert_section(session, other_regulation_id, "Other regulation section", [QUERY_VECTOR], user_id=USER_ID)

    response = await client.get(
        f"/api/regulations/{regulation_id}/documents", params={"threshold": 0.9, "limit": 10, "query": "zapytanie"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(matching_section_id),
            "score": pytest.approx(1.0),
            "header": "Art. 1",
            "text": "Matching section",
            "elements": [{"text": "Matching section", "subsection": None}],
            "highlight": {"start_element": 0, "end_element": 0},
        }
    ]


async def test_search_scores_section_by_its_two_best_chunks(client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)

        single_chunk_section_id = await insert_section(session, regulation_id, "Single chunk section", [QUERY_VECTOR])
        multi_chunk_section_id = await insert_section(
            session,
            regulation_id,
            "Multi chunk section",
            [QUERY_VECTOR, UNRELATED_VECTOR, UNRELATED_VECTOR],
            section_order=1,
        )

    response = await client.get(
        f"/api/regulations/{regulation_id}/documents", params={"threshold": 0.5, "limit": 10, "query": "zapytanie"}
    )

    assert response.status_code == status.HTTP_200_OK
    scores_by_id = {result["id"]: result["score"] for result in response.json()}
    expected_score = PRIMARY_CHUNK_SCORE_WEIGHT * 1.0 + (1 - PRIMARY_CHUNK_SCORE_WEIGHT) * UNRELATED_SIMILARITY

    assert scores_by_id[str(single_chunk_section_id)] == pytest.approx(1.0)
    assert scores_by_id[str(multi_chunk_section_id)] == pytest.approx(expected_score)


async def test_search_highlights_best_chunk_of_section(client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)
        await insert_section(
            session, regulation_id, "Highlighted section", [UNRELATED_VECTOR, QUERY_VECTOR, UNRELATED_VECTOR]
        )

    response = await client.get(
        f"/api/regulations/{regulation_id}/documents", params={"threshold": 0.5, "limit": 10, "query": "zapytanie"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["highlight"] == {"start_element": 1, "end_element": 1}


@pytest.mark.parametrize(
    ("order_by", "expected_texts"),
    [
        ("document", ["Lower score section", "Higher score section"]),
        ("score", ["Higher score section", "Lower score section"]),
    ],
)
async def test_search_orders_results(client, session_maker, order_by, expected_texts):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)
        await insert_section(session, regulation_id, "Lower score section", [QUERY_VECTOR, UNRELATED_VECTOR])
        await insert_section(session, regulation_id, "Higher score section", [QUERY_VECTOR], section_order=1)

    response = await client.get(
        f"/api/regulations/{regulation_id}/documents",
        params={"threshold": 0.5, "limit": 10, "query": "zapytanie", "order_by": order_by},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [result["text"] for result in response.json()] == expected_texts


async def test_search_public_regulations_by_description(client, session_maker, user):
    async with session_maker.begin() as session:
        matching_id = await insert_regulation(
            session, None, regulation_type=RegulationType.ACT, description_vector=QUERY_VECTOR
        )
        half_matching_id = await insert_regulation(
            session, None, regulation_type=RegulationType.DECREE, description_vector=HALF_RELATED_VECTOR
        )
        await insert_regulation(session, None, regulation_type=RegulationType.ACT, description_vector=UNRELATED_VECTOR)
        await insert_regulation(session, None, regulation_type=RegulationType.ACT)
        await insert_regulation(session, USER_ID, regulation_type=RegulationType.ACT, description_vector=QUERY_VECTOR)

    response = await client.get("/api/regulations/search", params={"query": "zapytanie", "threshold": 0.5})

    assert response.status_code == status.HTTP_200_OK
    assert [(result["regulation"]["id"], result["score"]) for result in response.json()] == [
        (str(matching_id), pytest.approx(1.0)),
        (str(half_matching_id), pytest.approx(1 / math.sqrt(2))),
    ]

    response = await client.get(
        "/api/regulations/search",
        params={"query": "zapytanie", "threshold": 0.5, "documentType": RegulationType.ACT},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [result["regulation"]["id"] for result in response.json()] == [str(matching_id)]


async def test_search_public_regulations_empty_query(client):
    response = await client.get("/api/regulations/search", params={"query": "", "threshold": 0.5})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_add_public_regulation(admin_client, session_maker, mock_regulations_storage):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)
    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    response = await admin_client.post(
        "/api/regulations",
        json={
            "scope": "PUBLIC",
            "name": "faculty-rules.pdf",
            "regulationType": RegulationType.DECREE,
            "organizationId": str(organization_id),
            "suborganizationId": str(suborganization_id),
            "generateDescription": True,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    regulation_id = UUID(response.json()["id"])
    assert response.json() == {
        "id": str(regulation_id),
        "url": "http://storage.local/bucket",
        "fields": {"key": str(regulation_id)},
    }

    async with session_maker() as session:
        result = await session.execute(select(regulations_table).where(regulations_table.c.id == regulation_id))
    regulation = result.one()

    assert regulation.user_id is None
    assert regulation.presentation_name == "faculty-rules.pdf"
    assert regulation.regulation_type == RegulationType.DECREE
    assert regulation.organization_id == organization_id
    assert regulation.suborganization_id == suborganization_id
    assert regulation.preparation_status == RegulationPreparationStatus.NOT_STARTED
    assert regulation.description_status == RegulationDescriptionStatus.IN_PROGRESS


async def test_add_public_regulation_with_suborganization_of_other_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        other_organization_id = await insert_organization(session)
        other_suborganization_id = await insert_suborganization(session, other_organization_id)

    response = await admin_client.post(
        "/api/regulations",
        json={
            "scope": "PUBLIC",
            "name": "faculty-rules.pdf",
            "organizationId": str(organization_id),
            "suborganizationId": str(other_suborganization_id),
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_public_regulations_filtered_by_organization(client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        other_organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id, "Wydział Prawa")
        other_suborganization_id = await insert_suborganization(session, organization_id, "Wydział Chemii")

        await insert_regulation(session, None, "General act.pdf")
        await insert_regulation(session, None, "Statute.pdf", organization_id=organization_id)
        await insert_regulation(
            session, None, "Law rules.pdf", organization_id=organization_id, suborganization_id=suborganization_id
        )
        await insert_regulation(
            session,
            None,
            "Chemistry rules.pdf",
            organization_id=organization_id,
            suborganization_id=other_suborganization_id,
        )
        await insert_regulation(session, None, "Other statute.pdf", organization_id=other_organization_id)

    response = await client.get("/api/regulations")

    assert response.status_code == status.HTTP_200_OK
    assert {regulation["presentationName"] for regulation in response.json()} == {
        "General act.pdf",
        "Statute.pdf",
        "Law rules.pdf",
        "Chemistry rules.pdf",
        "Other statute.pdf",
    }

    response = await client.get("/api/regulations", params={"organizationId": str(organization_id)})

    assert response.status_code == status.HTTP_200_OK
    assert {regulation["presentationName"] for regulation in response.json()} == {
        "General act.pdf",
        "Statute.pdf",
        "Law rules.pdf",
        "Chemistry rules.pdf",
    }

    response = await client.get(
        "/api/regulations",
        params={"organizationId": str(organization_id), "suborganizationId": str(suborganization_id)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert {
        (regulation["presentationName"], regulation["organizationId"], regulation["suborganizationId"])
        for regulation in response.json()
    } == {
        ("General act.pdf", None, None),
        ("Statute.pdf", str(organization_id), None),
        ("Law rules.pdf", str(organization_id), str(suborganization_id)),
    }


async def test_get_public_regulations_suborganization_without_organization(client):
    response = await client.get("/api/regulations", params={"suborganizationId": str(UNKNOWN_ID)})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_update_public_regulation_as_normal_user(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)

    response = await user_client.patch(f"/api/regulations/{regulation_id}", json={"name": "Renamed act.pdf"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_regenerate_public_regulation_description(admin_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, preparation_status=RegulationPreparationStatus.PREPARED)

    response = await admin_client.post(f"/api/regulations/{regulation_id}/description-generation")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert await get_scheduled_task_names(session_maker) == [REGULATION_DESCRIPTION_GENERATION_TASK_NAME]

    async with session_maker() as session:
        description_status = await session.scalar(
            select(regulations_table.c.description_status).where(regulations_table.c.id == regulation_id)
        )

    assert description_status == RegulationDescriptionStatus.IN_PROGRESS

    response = await admin_client.post(f"/api/regulations/{regulation_id}/description-generation")

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_regenerate_public_regulation_description_as_normal_user(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None)

    response = await user_client.post(f"/api/regulations/{regulation_id}/description-generation")

    assert response.status_code == status.HTTP_403_FORBIDDEN
