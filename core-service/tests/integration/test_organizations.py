from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from sqlalchemy import select

from src.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table
from tests.consts import UNKNOWN_ID
from tests.integration.fixtures.organizations import insert_organization, insert_suborganization


async def test_get_organizations(client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(
            session, "Politechnika Wrocławska", "PWr", create_date=datetime(2026, 1, 1, tzinfo=UTC)
        )
        other_organization_id = await insert_organization(session, create_date=datetime(2026, 1, 2, tzinfo=UTC))
        mechanical_id = await insert_suborganization(session, organization_id, "Wydział Mechaniczny")
        chemical_id = await insert_suborganization(session, organization_id, "Wydział Chemiczny")

    response = await client.get("/api/organizations")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(organization_id),
            "name": "Politechnika Wrocławska",
            "shortName": "PWr",
            "suborganizations": [
                {"id": str(chemical_id), "name": "Wydział Chemiczny"},
                {"id": str(mechanical_id), "name": "Wydział Mechaniczny"},
            ],
        },
        {
            "id": str(other_organization_id),
            "name": "Uniwersytet Wrocławski",
            "shortName": "UWr",
            "suborganizations": [],
        },
    ]


async def test_add_organization(admin_client, session_maker):
    response = await admin_client.post(
        "/api/organizations", json={"name": "Uniwersytet Wrocławski", "shortName": "UWr"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    organization_id = UUID(response.json())

    async with session_maker() as session:
        result = await session.execute(select(organizations_table).where(organizations_table.c.id == organization_id))
    organization = result.one()

    assert organization.name == "Uniwersytet Wrocławski"
    assert organization.short_name == "UWr"


async def test_add_organization_as_normal_user(user_client):
    response = await user_client.post("/api/organizations", json={"name": "Uniwersytet Wrocławski", "shortName": "UWr"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_update_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)

    response = await admin_client.put(
        f"/api/organizations/{organization_id}",
        json={"name": "Uniwersytet Wrocławski im. X", "shortName": "UWr2"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        result = await session.execute(select(organizations_table).where(organizations_table.c.id == organization_id))
    organization = result.one()

    assert organization.name == "Uniwersytet Wrocławski im. X"
    assert organization.short_name == "UWr2"


async def test_update_organization_not_found(admin_client):
    response = await admin_client.put(
        f"/api/organizations/{UNKNOWN_ID}", json={"name": "Uniwersytet", "shortName": "U"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)

    response = await admin_client.delete(f"/api/organizations/{organization_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        suborganization = await session.scalar(
            select(suborganizations_table.c.id).where(suborganizations_table.c.id == suborganization_id)
        )
    assert suborganization is None

    response = await admin_client.delete(f"/api/organizations/{organization_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_add_suborganization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)

    response = await admin_client.post(
        f"/api/organizations/{organization_id}/suborganizations", json={"name": "Wydział Prawa"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    suborganization_id = UUID(response.json())

    async with session_maker() as session:
        result = await session.execute(
            select(suborganizations_table).where(suborganizations_table.c.id == suborganization_id)
        )
    suborganization = result.one()

    assert suborganization.organization_id == organization_id
    assert suborganization.name == "Wydział Prawa"


async def test_add_suborganization_to_missing_organization(admin_client):
    response = await admin_client.post(
        f"/api/organizations/{UNKNOWN_ID}/suborganizations", json={"name": "Wydział Prawa"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_suborganization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)

    response = await admin_client.put(
        f"/api/organizations/{organization_id}/suborganizations/{suborganization_id}",
        json={"name": "Wydział Nauk Społecznych"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        name = await session.scalar(
            select(suborganizations_table.c.name).where(suborganizations_table.c.id == suborganization_id)
        )
    assert name == "Wydział Nauk Społecznych"


async def test_update_suborganization_not_found(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)

    response = await admin_client.put(
        f"/api/organizations/{organization_id}/suborganizations/{UNKNOWN_ID}", json={"name": "Wydział"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_suborganization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)

    response = await admin_client.delete(f"/api/organizations/{organization_id}/suborganizations/{suborganization_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await admin_client.delete(f"/api/organizations/{organization_id}/suborganizations/{suborganization_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_suborganization_of_other_organization(admin_client, session_maker):
    async with session_maker.begin() as session:
        organization_id = await insert_organization(session)
        other_organization_id = await insert_organization(session)
        suborganization_id = await insert_suborganization(session, organization_id)

    response = await admin_client.delete(
        f"/api/organizations/{other_organization_id}/suborganizations/{suborganization_id}"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
