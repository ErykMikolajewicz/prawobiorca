import pytest
from fastapi import status

from src.domain.value_objects.regulations import RegulationType
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, UNKNOWN_ACCESS_TOKEN


@pytest.mark.parametrize(
    "file_name, file_type, error_status",
    [
        ("", RegulationType.STATUTE, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("a" * 300, RegulationType.ACT, status.HTTP_422_UNPROCESSABLE_CONTENT),
        ("file.txt", "invalid_regulation_type", status.HTTP_422_UNPROCESSABLE_CONTENT),
    ],
    ids=("empty file name", "file name too long", "invalid regulation type"),
)
async def test_logged_used_add_public_regulation_validation(
    client,
    override_get_regulations_storage,
    override_authorize_admin_user,
    file_name,
    file_type,
    error_status,
):
    regulation_data = {"name": file_name, "regulationType": file_type}

    cookies = {ACCESS_COOKIE_NAME: ACCESS_TOKEN}
    client.cookies = cookies

    response = await client.post("api/user/regulations", json=regulation_data)

    assert response.status_code == error_status


async def test_unauthorized_user_add_public_regulation(client, override_authorize_admin_user):
    regulation_data = {"name": "test.txt", "regulationType": RegulationType.DECREE}

    cookies = {ACCESS_COOKIE_NAME: UNKNOWN_ACCESS_TOKEN}
    client.cookies = cookies

    response = await client.post("api/user/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_non_admin_user_add_public_regulation(client, override_authorize_normal_user):
    regulation_data = {"name": "test.txt", "regulationType": RegulationType.DECREE}

    cookies = {ACCESS_COOKIE_NAME: ACCESS_TOKEN}
    client.cookies = cookies

    response = await client.post("api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_403_FORBIDDEN
