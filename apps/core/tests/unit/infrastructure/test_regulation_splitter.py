from email.parser import BytesParser
from email.policy import default

import pytest
from httpx2 import AsyncClient, MockTransport, Response

from core_service.domain.value_objects.legal_units import RegulationElement, UsefulLabels
from core_service.infrastructure.ai_services.regulation_splitter import HttpRegulationSplitter
from core_service.shared.exceptions import ServiceRequestRejected, ServiceUnavailable

EXTRACTION_SERVICE_URL = "http://extraction.local"


def create_splitter(handler) -> HttpRegulationSplitter:
    return HttpRegulationSplitter(AsyncClient(transport=MockTransport(handler)), EXTRACTION_SERVICE_URL)


async def test_split_sends_regulation_file_and_returns_its_elements():
    requests = []

    def handler(request):
        requests.append(request)
        return Response(200, json=[{"label": UsefulLabels.TEXT, "text": "Art. 1. Ustawa określa zasady."}])

    elements = await create_splitter(handler).split(b"%PDF-1.7")

    assert elements == [RegulationElement(label=UsefulLabels.TEXT, text="Art. 1. Ustawa określa zasady.")]
    (request,) = requests
    assert request.url == f"{EXTRACTION_SERVICE_URL}/parse-regulation"
    multipart = BytesParser(policy=default).parsebytes(
        f"Content-Type: {request.headers['content-type']}\r\n\r\n".encode() + request.content
    )
    (file_part,) = multipart.iter_parts()
    assert file_part.get_content_disposition() == "form-data"
    assert file_part.get_param("name", header="content-disposition") == "file"
    assert file_part.get_payload(decode=True) == b"%PDF-1.7"


async def test_split_failure_raises_service_unavailable():
    with pytest.raises(ServiceUnavailable):
        await create_splitter(lambda request: Response(503)).split(b"%PDF-1.7")


async def test_split_rejected_request_raises_service_request_rejected():
    with pytest.raises(ServiceRequestRejected):
        await create_splitter(lambda request: Response(422)).split(b"%PDF-1.7")
