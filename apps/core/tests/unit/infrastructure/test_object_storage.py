from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from core_service.domain.exceptions.regulations import RegulationContentNotFound
from core_service.infrastructure.object_storage.repository import S3RegulationsStorage
from core_service.shared.exceptions import ServiceRequestRejected, ServiceUnavailable

REGULATION_ID = UUID("0f1e2d3c-4b5a-4968-8776-655443322110")


def create_client_error(status_code: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": str(status_code)},
            "ResponseMetadata": {
                "RequestId": "",
                "HostId": "",
                "HTTPStatusCode": status_code,
                "HTTPHeaders": {},
                "RetryAttempts": 0,
            },
        },
        "",
    )


def create_storage(client: AsyncMock) -> S3RegulationsStorage:
    return S3RegulationsStorage(
        client, MagicMock(), bucket="bucket", signed_url_expiration_seconds=60, max_file_size_bytes=1024
    )


@pytest.mark.parametrize(
    ("error", "expected_error"),
    [
        (create_client_error(404), RegulationContentNotFound),
        (create_client_error(403), ServiceRequestRejected),
        (create_client_error(503), ServiceUnavailable),
        (EndpointConnectionError(endpoint_url="http://storage.local"), ServiceUnavailable),
    ],
    ids=("not found", "access denied", "slow down", "connection error"),
)
async def test_get_regulation_maps_storage_errors(error, expected_error):
    client = AsyncMock()
    client.get_object.side_effect = error

    with pytest.raises(expected_error):
        await create_storage(client).get_regulation(REGULATION_ID)


async def test_check_regulation_exists_returns_false_for_missing_object():
    client = AsyncMock()
    client.head_object.side_effect = create_client_error(404)

    assert await create_storage(client).check_regulation_exists(REGULATION_ID) is False


async def test_check_regulation_exists_does_not_hide_storage_errors():
    client = AsyncMock()
    client.head_object.side_effect = create_client_error(403)

    with pytest.raises(ServiceRequestRejected):
        await create_storage(client).check_regulation_exists(REGULATION_ID)
