from datetime import datetime
from uuid import UUID, uuid4

from fastapi import status
from sqlalchemy import delete, insert, select

from src.infrastructure.relational_db.schemas.organizations import organizations_table, suborganizations_table
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN


async def insert_organization(session_maker) -> UUID:
    async with session_maker.begin() as session:
        statement = (
            insert(organizations_table)
            .values(name="Uniwersytet Wrocławski", short_name="UWr")
            .returning(organizations_table.c.id)
        )
        organization_id = await session.scalar(statement)
    return organization_id


async def insert_suborganization(session_maker, organization_id: UUID) -> UUID:
    async with session_maker.begin() as session:
        statement = (
            insert(suborganizations_table)
            .values(organization_id=organization_id, name="Wydział Prawa")
            .returning(suborganizations_table.c.id)
        )
        suborganization_id = await session.scalar(statement)
    return suborganization_id


async def delete_organization(session_maker, organization_id: UUID) -> None:
    async with session_maker.begin() as session:
        await session.execute(delete(organizations_table).where(organizations_table.c.id == organization_id))


async def test_get_organizations(client, override_session_maker, session_maker):
    async with session_maker.begin() as session:
        default_organization_id = await session.scalar(
            select(organizations_table.c.id).where(organizations_table.c.short_name == "PWr")
        )
        statement = (
            insert(organizations_table)
            .values(name="Uniwersytet Wrocławski", short_name="UWr", create_date=datetime(2100, 1, 1))
            .returning(organizations_table.c.id)
        )
        organization_id = await session.scalar(statement)
        statement = (
            insert(suborganizations_table)
            .values(
                [
                    {
                        "organization_id": default_organization_id,
                        "name": "Wydział Mechaniczny",
                        "create_date": datetime(2100, 1, 1),
                    },
                    {
                        "organization_id": default_organization_id,
                        "name": "Wydział Chemiczny",
                        "create_date": datetime(2100, 1, 2),
                    },
                ]
            )
            .returning(suborganizations_table.c.id)
        )
        result = await session.scalars(statement)
    mechanical_id, chemical_id = result.all()

    try:
        response = await client.get("/api/organizations")
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(organizations_table).where(organizations_table.c.id == organization_id))
            await session.execute(
                delete(suborganizations_table).where(
                    suborganizations_table.c.organization_id == default_organization_id
                )
            )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(default_organization_id),
            "name": "Politechnika Wrocławska",
            "shortName": "PWr",
            "suborganizations": [
                {"id": str(mechanical_id), "name": "Wydział Mechaniczny"},
                {"id": str(chemical_id), "name": "Wydział Chemiczny"},
            ],
        },
        {
            "id": str(organization_id),
            "name": "Uniwersytet Wrocławski",
            "shortName": "UWr",
            "suborganizations": [],
        },
    ]


async def test_add_organization(client, override_session_maker, session_maker, override_authorize_admin_user):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(
        "/api/admin/organizations", json={"name": "Uniwersytet Wrocławski", "shortName": "UWr"}
    )

    assert response.status_code == status.HTTP_201_CREATED
    organization_id = UUID(response.json())

    try:
        async with session_maker() as session:
            result = await session.execute(
                select(organizations_table).where(organizations_table.c.id == organization_id)
            )
        organization = result.one()

        assert organization.name == "Uniwersytet Wrocławski"
        assert organization.short_name == "UWr"
    finally:
        await delete_organization(session_maker, organization_id)


async def test_add_organization_as_normal_user(client, override_session_maker, override_authorize_normal_user):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(
        "/api/admin/organizations", json={"name": "Uniwersytet Wrocławski", "shortName": "UWr"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_update_organization(client, override_session_maker, session_maker, override_authorize_admin_user):
    organization_id = await insert_organization(session_maker)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.put(
            f"/api/admin/organizations/{organization_id}",
            json={"name": "Uniwersytet Wrocławski im. X", "shortName": "UWr2"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        async with session_maker() as session:
            result = await session.execute(
                select(organizations_table).where(organizations_table.c.id == organization_id)
            )
        organization = result.one()

        assert organization.name == "Uniwersytet Wrocławski im. X"
        assert organization.short_name == "UWr2"
    finally:
        await delete_organization(session_maker, organization_id)

    response = await client.put(
        f"/api/admin/organizations/{organization_id}", json={"name": "Uniwersytet", "shortName": "U"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_organization(client, override_session_maker, session_maker, override_authorize_admin_user):
    organization_id = await insert_organization(session_maker)
    suborganization_id = await insert_suborganization(session_maker, organization_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/admin/organizations/{organization_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        suborganization = await session.scalar(
            select(suborganizations_table.c.id).where(suborganizations_table.c.id == suborganization_id)
        )
    assert suborganization is None

    response = await client.delete(f"/api/admin/organizations/{organization_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_add_suborganization(client, override_session_maker, session_maker, override_authorize_admin_user):
    organization_id = await insert_organization(session_maker)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(
            f"/api/admin/organizations/{organization_id}/suborganizations", json={"name": "Wydział Prawa"}
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
    finally:
        await delete_organization(session_maker, organization_id)


async def test_add_suborganization_to_missing_organization(
    client, override_session_maker, override_authorize_admin_user
):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/admin/organizations/{uuid4()}/suborganizations", json={"name": "Wydział Prawa"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_suborganization(client, override_session_maker, session_maker, override_authorize_admin_user):
    organization_id = await insert_organization(session_maker)
    suborganization_id = await insert_suborganization(session_maker, organization_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.put(
            f"/api/admin/suborganizations/{suborganization_id}", json={"name": "Wydział Nauk Społecznych"}
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        async with session_maker() as session:
            name = await session.scalar(
                select(suborganizations_table.c.name).where(suborganizations_table.c.id == suborganization_id)
            )
        assert name == "Wydział Nauk Społecznych"
    finally:
        await delete_organization(session_maker, organization_id)

    response = await client.put(f"/api/admin/suborganizations/{suborganization_id}", json={"name": "Wydział"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_suborganization(client, override_session_maker, session_maker, override_authorize_admin_user):
    organization_id = await insert_organization(session_maker)
    suborganization_id = await insert_suborganization(session_maker, organization_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.delete(f"/api/admin/suborganizations/{suborganization_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await client.delete(f"/api/admin/suborganizations/{suborganization_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
    finally:
        await delete_organization(session_maker, organization_id)
