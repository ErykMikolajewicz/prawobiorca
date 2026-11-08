import pytest
from fastapi import status

from src.domain.value_objects.regulations import RegulationType
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN


@pytest.mark.parametrize(
    ("file_name", "file_type"),
    [
        ("", RegulationType.STATUTE),
        ("a" * 300, RegulationType.ACT),
        ("file.txt", "invalid_regulation_type"),
    ],
    ids=("empty file name", "file name too long", "invalid regulation type"),
)
async def test_add_regulation_validation(client, override_get_regulations_storage, file_name, file_type):
    regulation_data = {"scope": "PRIVATE", "name": file_name, "regulationType": file_type}

    cookies = {ACCESS_COOKIE_NAME: ACCESS_TOKEN}
    client.cookies = cookies

    response = await client.post("api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
