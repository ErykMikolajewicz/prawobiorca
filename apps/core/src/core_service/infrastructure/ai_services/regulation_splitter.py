from collections.abc import Iterable

from httpx2 import AsyncClient, HTTPError, HTTPStatusError

from core_service.domain.value_objects.legal_units import RegulationElement
from core_service.infrastructure.service_errors import get_status_error
from core_service.shared.exceptions import ServiceUnavailable


class HttpRegulationSplitter:
    def __init__(self, client: AsyncClient, extraction_service_url: str):
        self._client = client
        self._split_url = f"{extraction_service_url}/parse-regulation"

    async def split(self, regulation: bytes) -> Iterable[RegulationElement]:
        try:
            response = await self._client.post(
                self._split_url, timeout=1500, files={"file": ("regulation.pdf", regulation)}
            )
            response.raise_for_status()
        except HTTPStatusError as e:
            raise get_status_error(e.response.status_code) from e
        except HTTPError as e:
            raise ServiceUnavailable() from e

        return [RegulationElement(label=item["label"], text=item["text"]) for item in response.json()]
