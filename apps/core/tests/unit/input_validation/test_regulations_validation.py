import pytest
from fastapi import status

from core_service.domain.value_objects.regulations import RegulationType
from tests.consts import ACCESS_TOKEN
from tests.fixtures.clients import create_client


@pytest.mark.parametrize(
    ("file_name", "file_type"),
    [
        ("", RegulationType.STATUTE),
        ("a" * 300, RegulationType.ACT),
        ("file.txt", "invalid_regulation_type"),
    ],
    ids=("empty file name", "file name too long", "invalid regulation type"),
)
async def test_add_regulation_validation(override_get_regulations_storage, file_name, file_type):
    regulation_data = {"scope": "PRIVATE", "name": file_name, "regulationType": file_type}

    async with create_client(ACCESS_TOKEN) as client:
        response = await client.post("/api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
