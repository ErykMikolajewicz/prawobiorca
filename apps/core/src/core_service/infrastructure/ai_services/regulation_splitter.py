from collections.abc import Iterable
from http import HTTPStatus

from httpx2 import AsyncClient, HTTPError, HTTPStatusError, Response

from core_service.domain.exceptions.regulations import RegulationDocumentRejected
from core_service.domain.value_objects.legal_units import RegulationElement
from core_service.domain.value_objects.regulations import RegulationPreparationFailureReason
from core_service.infrastructure.service_errors import get_status_error
from core_service.shared.exceptions import ServiceUnavailable

EXTRACTION_REJECTION_REASONS = {
    "INCOMPLETE_CONVERSION": RegulationPreparationFailureReason.INCOMPLETE_DOCUMENT,
    "CONVERSION_FAILED": RegulationPreparationFailureReason.UNREADABLE_DOCUMENT,
}


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
            raise _get_response_error(e.response) from e
        except HTTPError as e:
            raise ServiceUnavailable() from e

        return [RegulationElement(label=item["label"], text=item["text"]) for item in response.json()]


def _get_response_error(response: Response) -> Exception:
    if response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT:
        reason = EXTRACTION_REJECTION_REASONS.get(str(response.json()["detail"]))
        if reason is not None:
            return RegulationDocumentRejected(reason)
    return get_status_error(response.status_code)
