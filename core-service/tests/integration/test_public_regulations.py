import math
from unittest.mock import ANY
from uuid import UUID, uuid4

import pytest
from fastapi import status
from sqlalchemy import delete, insert, select

from src.app.dtos.regulations import RegulationUploadTarget
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationPreparationStatus,
    RegulationType,
)
from src.framework.dependencies.ai_services import get_texts_embedder
from src.infrastructure.relational_db.repositories.sections import PRIMARY_CHUNK_SCORE_WEIGHT
from src.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table
from src.infrastructure.relational_db.schemas.regulations import regulations_table
from src.infrastructure.relational_db.schemas.sections import (
    regulations_chunks_table,
    regulations_sections_table,
)
from src.main import prawobiorca
from src.shared.consts import ACCESS_COOKIE_NAME, VECTOR_LENGTH
from tests.consts import ACCESS_TOKEN, USER_ID


async def test_get_public_regulations(client, override_session_maker, session_maker, set_user, clean_user):
    async with session_maker.begin() as session:
        statement = (
            insert(regulations_table)
            .values(
                [
                    {
                        "user_id": None,
                        "presentation_name": "Public act.pdf",
                        "preparation_status": RegulationPreparationStatus.PREPARED,
                        "regulation_type": RegulationType.ACT,
                    },
                    {
                        "user_id": None,
                        "presentation_name": "Public decree.pdf",
                        "preparation_status": RegulationPreparationStatus.NOT_STARTED,
                        "regulation_type": RegulationType.DECREE,
                    },
                    {
                        "user_id": USER_ID,
                        "presentation_name": "Private act.pdf",
                        "preparation_status": RegulationPreparationStatus.PREPARED,
                        "regulation_type": RegulationType.ACT,
                    },
                ]
            )
            .returning(regulations_table.c.id)
        )

        result = await session.scalars(statement)

    regulations_ids = result.all()
    public_act_id, public_decree_id, private_act_id = regulations_ids

    try:
        response = await client.get("/api/regulations", params={"documentType": RegulationType.ACT})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(public_act_id),
                "createDate": ANY,
                "presentationName": "Public act.pdf",
                "description": None,
                "regulationType": RegulationType.ACT,
                "preparationStatus": RegulationPreparationStatus.PREPARED,
                "descriptionStatus": RegulationDescriptionStatus.NOT_REQUESTED,
                "organizationId": None,
                "suborganizationId": None,
            }
        ]

    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id.in_(regulations_ids)))


async def test_get_public_regulation(client, override_session_maker, session_maker, set_user, clean_user):
    async with session_maker.begin() as session:
        public_regulation_id = await insert_regulation(session, None, "Public act.pdf")
        private_regulation_id = await insert_regulation(session, USER_ID, "Private act.pdf")

    try:
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

    finally:
        async with session_maker.begin() as session:
            await session.execute(
                delete(regulations_table).where(
                    regulations_table.c.id.in_([public_regulation_id, private_regulation_id])
                )
            )


class StubTextsEmbedder:
    @staticmethod
    async def embed_queries(queries):
        return [[1.0] * VECTOR_LENGTH]


QUERY_VECTOR = [1.0] * VECTOR_LENGTH
UNRELATED_VECTOR = [1.0, *[0.0] * (VECTOR_LENGTH - 1)]
UNRELATED_SIMILARITY = 1 / math.sqrt(VECTOR_LENGTH)


async def insert_regulation(session, user_id, presentation_name):
    return await session.scalar(
        insert(regulations_table)
        .values(
            {
                "user_id": user_id,
                "presentation_name": presentation_name,
                "preparation_status": RegulationPreparationStatus.PREPARED,
                "regulation_type": RegulationType.ACT,
            }
        )
        .returning(regulations_table.c.id)
    )


async def insert_section(session, regulation_id, user_id, unit_number, text, section_order, chunk_vectors):
    section_id = await session.scalar(
        insert(regulations_sections_table)
        .values(
            {
                "header": f"Rozdział 5 Pracownicy uczelni > Art. {unit_number}",
                "text": text,
                "section_order": section_order,
                "elements": [{"text": text, "subsection": None}],
                "regulation_id": regulation_id,
                "user_id": user_id,
            }
        )
        .returning(regulations_sections_table.c.id)
    )

    await session.execute(
        insert(regulations_chunks_table).values(
            [
                {
                    "section_id": section_id,
                    "chunk_index": chunk_index,
                    "text": f"{text} chunk {chunk_index}",
                    "vector": vector,
                    "span_start_element": chunk_index,
                    "span_end_element": chunk_index,
                }
                for chunk_index, vector in enumerate(chunk_vectors)
            ]
        )
    )

    return section_id


async def test_search_regulations_documents(client, override_session_maker, session_maker, set_user, clean_user):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public searchable regulation.pdf")
        other_regulation_id = await insert_regulation(session, USER_ID, "User searchable regulation.pdf")

        matching_section_id = await insert_section(
            session, regulation_id, None, "112", "Matching public regulation section", 0, [QUERY_VECTOR]
        )
        await insert_section(
            session, regulation_id, None, "114", "Unrelated public regulation section", 1, [UNRELATED_VECTOR]
        )
        await insert_section(
            session, other_regulation_id, USER_ID, "113", "Matching user regulation section", 0, [QUERY_VECTOR]
        )

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.9, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(matching_section_id),
                "score": pytest.approx(1.0),
                "header": "Rozdział 5 Pracownicy uczelni > Art. 112",
                "text": "Matching public regulation section",
                "elements": [{"text": "Matching public regulation section", "subsection": None}],
                "highlight": {"start_element": 0, "end_element": 0},
            }
        ]
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(
                delete(regulations_table).where(regulations_table.c.id.in_([regulation_id, other_regulation_id]))
            )


async def test_search_scores_section_by_its_two_best_chunks(
    client, override_session_maker, session_maker, set_user, clean_user
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public multi chunk regulation.pdf")

        single_chunk_section_id = await insert_section(
            session, regulation_id, None, "112", "Single chunk section", 0, [QUERY_VECTOR]
        )
        multi_chunk_section_id = await insert_section(
            session,
            regulation_id,
            None,
            "113",
            "Multi chunk section",
            1,
            [QUERY_VECTOR, UNRELATED_VECTOR, UNRELATED_VECTOR],
        )

    expected_score = PRIMARY_CHUNK_SCORE_WEIGHT * 1.0 + (1 - PRIMARY_CHUNK_SCORE_WEIGHT) * UNRELATED_SIMILARITY

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        results_by_id = {result["id"]: result["score"] for result in response.json()}

        assert results_by_id[str(single_chunk_section_id)] == pytest.approx(1.0)
        assert results_by_id[str(multi_chunk_section_id)] == pytest.approx(expected_score)
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_search_highlights_best_chunk_of_section(
    client, override_session_maker, session_maker, set_user, clean_user
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public highlighted regulation.pdf")

        await insert_section(
            session,
            regulation_id,
            None,
            "112",
            "Highlighted section",
            0,
            [UNRELATED_VECTOR, QUERY_VECTOR, UNRELATED_VECTOR],
        )

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["highlight"] == {"start_element": 1, "end_element": 1}
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


@pytest.mark.parametrize(
    ("order_by", "expected_texts"),
    [
        ("document", ["Lower score section", "Higher score section"]),
        ("score", ["Higher score section", "Lower score section"]),
    ],
)
async def test_search_orders_results(
    client, override_session_maker, session_maker, set_user, clean_user, order_by, expected_texts
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public ordered regulation.pdf")

        await insert_section(
            session, regulation_id, None, "112", "Lower score section", 0, [QUERY_VECTOR, UNRELATED_VECTOR]
        )
        await insert_section(session, regulation_id, None, "113", "Higher score section", 1, [QUERY_VECTOR])

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query", "order_by": order_by},
        )

        assert response.status_code == status.HTTP_200_OK
        assert [result["text"] for result in response.json()] == expected_texts
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_search_public_regulations_by_description(
    client, override_session_maker, session_maker, set_user, clean_user
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()
    half_related_vector = [1.0] * (VECTOR_LENGTH // 2) + [0.0] * (VECTOR_LENGTH // 2)

    async with session_maker.begin() as session:
        regulations_ids = await session.scalars(
            insert(regulations_table)
            .values(
                [
                    {
                        "user_id": None,
                        "presentation_name": "Matching act.pdf",
                        "regulation_type": RegulationType.ACT,
                        "description_vector": QUERY_VECTOR,
                    },
                    {
                        "user_id": None,
                        "presentation_name": "Half matching decree.pdf",
                        "regulation_type": RegulationType.DECREE,
                        "description_vector": half_related_vector,
                    },
                    {
                        "user_id": None,
                        "presentation_name": "Unrelated act.pdf",
                        "regulation_type": RegulationType.ACT,
                        "description_vector": UNRELATED_VECTOR,
                    },
                    {
                        "user_id": None,
                        "presentation_name": "Act without description.pdf",
                        "regulation_type": RegulationType.ACT,
                        "description_vector": None,
                    },
                    {
                        "user_id": USER_ID,
                        "presentation_name": "Private matching act.pdf",
                        "regulation_type": RegulationType.ACT,
                        "description_vector": QUERY_VECTOR,
                    },
                ]
            )
            .returning(regulations_table.c.id)
        )
    regulations_ids = regulations_ids.all()
    matching_id, half_matching_id, *_ = regulations_ids

    try:
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
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id.in_(regulations_ids)))


async def test_search_public_regulations_empty_query(client, override_session_maker):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    try:
        response = await client.get("/api/regulations/search", params={"query": "", "threshold": 0.5})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)


async def test_add_public_regulation_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
):
    regulation_data = {"scope": "PUBLIC", "name": "public-regulation.pdf", "regulationType": RegulationType.DECREE}

    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert "id" in response_json
    assert "url" in response_json
    assert "fields" in response_json
    regulation_id = UUID(response_json["id"])

    try:
        async with session_maker() as session:
            statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
            result = await session.execute(statement)
        regulation = result.one_or_none()

        assert regulation is not None
        assert regulation.user_id is None
        assert regulation.presentation_name == "public-regulation.pdf"
        assert regulation.preparation_status == RegulationPreparationStatus.NOT_STARTED
        assert regulation.regulation_type == RegulationType.DECREE
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_confirm_public_regulation_upload_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_get_regulations_preparation_scheduler,
    mock_regulation_preparation_scheduler,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=None,
                presentation_name="public_confirm.pdf",
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    mock_regulations_storage.check_regulation_exists.return_value = True

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/regulations/{regulation_id}/confirm-upload")

        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_regulations_storage.check_regulation_exists.assert_awaited_once_with(regulation_id)
        mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
            ANY, None, regulation_id
        )

        async with session_maker() as session:
            statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
            result = await session.execute(statement)
        regulation = result.one_or_none()

        assert regulation is not None
        assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_update_public_regulation_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public act.pdf")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.patch(
            f"/api/regulations/{regulation_id}",
            json={"name": "Renamed act.pdf", "description": "Opis regulacji"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "id": str(regulation_id),
            "createDate": ANY,
            "presentationName": "Renamed act.pdf",
            "description": "Opis regulacji",
            "regulationType": RegulationType.ACT,
            "preparationStatus": RegulationPreparationStatus.PREPARED,
            "descriptionStatus": RegulationDescriptionStatus.NOT_REQUESTED,
            "organizationId": None,
            "suborganizationId": None,
        }
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_update_public_regulation_as_normal_user(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public act.pdf")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.patch(f"/api/regulations/{regulation_id}", json={"name": "Renamed act.pdf"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def insert_organization(session, short_name):
    return await session.scalar(
        insert(organizations_table)
        .values(name=f"Uczelnia {short_name}", short_name=short_name)
        .returning(organizations_table.c.id)
    )


async def insert_suborganization(session, organization_id, name):
    return await session.scalar(
        insert(suborganizations_table)
        .values(organization_id=organization_id, name=name)
        .returning(suborganizations_table.c.id)
    )


async def insert_organization_regulation(session, presentation_name, organization_id, suborganization_id):
    return await session.scalar(
        insert(regulations_table)
        .values(
            {
                "user_id": None,
                "presentation_name": presentation_name,
                "preparation_status": RegulationPreparationStatus.PREPARED,
                "organization_id": organization_id,
                "suborganization_id": suborganization_id,
            }
        )
        .returning(regulations_table.c.id)
    )


async def test_get_public_regulations_filtered_by_organization(client, override_session_maker, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session, "UWr")
        other_organization_id = await insert_organization(session, "UMed")
        suborganization_id = await insert_suborganization(session, organization_id, "Wydział Prawa")
        other_suborganization_id = await insert_suborganization(session, organization_id, "Wydział Chemii")

        general_id = await insert_organization_regulation(session, "General act.pdf", None, None)
        await insert_organization_regulation(session, "Statute.pdf", organization_id, None)
        await insert_organization_regulation(session, "Law rules.pdf", organization_id, suborganization_id)
        await insert_organization_regulation(session, "Chemistry rules.pdf", organization_id, other_suborganization_id)
        await insert_organization_regulation(session, "Other statute.pdf", other_organization_id, None)

    try:
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
    finally:
        async with session_maker.begin() as session:
            await session.execute(
                delete(organizations_table).where(
                    organizations_table.c.id.in_([organization_id, other_organization_id])
                )
            )
            await session.execute(delete(regulations_table).where(regulations_table.c.id == general_id))


async def test_get_public_regulations_suborganization_without_organization(client, override_session_maker):
    response = await client.get("/api/regulations", params={"suborganizationId": str(uuid4())})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_add_public_regulation_with_organization(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session, "UWr")
        suborganization_id = await insert_suborganization(session, organization_id, "Wydział Prawa")

    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(
            "/api/regulations",
            json={
                "scope": "PUBLIC",
                "name": "faculty-rules.pdf",
                "organizationId": str(organization_id),
                "suborganizationId": str(suborganization_id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        regulation_id = UUID(response.json()["id"])

        async with session_maker() as session:
            result = await session.execute(select(regulations_table).where(regulations_table.c.id == regulation_id))
        regulation = result.one()

        assert regulation.organization_id == organization_id
        assert regulation.suborganization_id == suborganization_id
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(organizations_table).where(organizations_table.c.id == organization_id))


async def test_add_public_regulation_with_suborganization_of_other_organization(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session, "UWr")
        other_organization_id = await insert_organization(session, "UMed")
        other_suborganization_id = await insert_suborganization(session, other_organization_id, "Wydział Lekarski")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(
            "/api/regulations",
            json={
                "scope": "PUBLIC",
                "name": "faculty-rules.pdf",
                "organizationId": str(organization_id),
                "suborganizationId": str(other_suborganization_id),
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
    finally:
        async with session_maker.begin() as session:
            await session.execute(
                delete(organizations_table).where(
                    organizations_table.c.id.in_([organization_id, other_organization_id])
                )
            )


async def test_delete_suborganization_deletes_its_regulations(client, override_session_maker, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session, "UWr")
        suborganization_id = await insert_suborganization(session, organization_id, "Wydział Prawa")
        statute_id = await insert_organization_regulation(session, "Statute.pdf", organization_id, None)
        faculty_rules_id = await insert_organization_regulation(
            session, "Law rules.pdf", organization_id, suborganization_id
        )

    try:
        async with session_maker.begin() as session:
            await session.execute(
                delete(suborganizations_table).where(suborganizations_table.c.id == suborganization_id)
            )

        async with session_maker() as session:
            remaining_ids = await session.scalars(
                select(regulations_table.c.id).where(regulations_table.c.id.in_([statute_id, faculty_rules_id]))
            )

        assert remaining_ids.all() == [statute_id]
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(organizations_table).where(organizations_table.c.id == organization_id))


async def test_add_public_regulation_with_description_generation(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
):
    regulation_data = {"scope": "PUBLIC", "name": "public-regulation.pdf", "generateDescription": True}

    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_201_CREATED
    regulation_id = UUID(response.json()["id"])

    try:
        async with session_maker() as session:
            description_status = await session.scalar(
                select(regulations_table.c.description_status).where(regulations_table.c.id == regulation_id)
            )

        assert description_status == RegulationDescriptionStatus.IN_PROGRESS
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_regenerate_public_regulation_description_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulation_description_generation_scheduler,
    mock_regulation_description_generation_scheduler,
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public act.pdf")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)
    scheduler = mock_regulation_description_generation_scheduler

    try:
        response = await client.post(f"/api/regulations/{regulation_id}/description-generation")

        assert response.status_code == status.HTTP_202_ACCEPTED
        scheduler.schedule_regulation_description_generation.assert_awaited_once_with(ANY, None, regulation_id)

        response = await client.post(f"/api/regulations/{regulation_id}/description-generation")

        assert response.status_code == status.HTTP_409_CONFLICT
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_regenerate_public_regulation_description_as_normal_user(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_regulation_description_generation_scheduler,
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public act.pdf")

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/regulations/{regulation_id}/description-generation")

        assert response.status_code == status.HTTP_403_FORBIDDEN
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_update_public_regulation_description_clears_description_vector(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=None,
                presentation_name="Public act.pdf",
                description="Opis",
                description_vector=UNRELATED_VECTOR,
            )
            .returning(regulations_table.c.id)
        )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    async def get_description_vector():
        async with session_maker() as session:
            return await session.scalar(
                select(regulations_table.c.description_vector).where(regulations_table.c.id == regulation_id)
            )

    try:
        response = await client.patch(
            f"/api/regulations/{regulation_id}", json={"name": "Renamed act.pdf", "description": "Opis"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert await get_description_vector() is not None

        response = await client.patch(
            f"/api/regulations/{regulation_id}", json={"name": "Renamed act.pdf", "description": "Nowy opis"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert await get_description_vector() is None
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))
