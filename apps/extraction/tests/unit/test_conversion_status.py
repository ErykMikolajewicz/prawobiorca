from http import HTTPStatus
from types import SimpleNamespace

from docling.datamodel.base_models import ConversionStatus, ErrorItem
from docling.exceptions import ConversionError
from docling_core.types.doc import DocItemLabel, DoclingDocument
from fastapi.testclient import TestClient

from extraction_service.main import app

REGULATION_TEXT = "§ 1. Student może złożyć wniosek o przedłużenie terminu."

PAGE_ERROR = ErrorItem(component_type="pipeline", module_name="StandardPdfPipeline", error_message="Page 2 failed.")


class FakeConverter:
    def __init__(self, status: ConversionStatus, errors: list[ErrorItem]):
        self._status = status
        self._errors = errors

    def convert(self, file_path):
        document = DoclingDocument(name="regulation")
        document.add_text(label=DocItemLabel.TEXT, text=REGULATION_TEXT)
        return SimpleNamespace(status=self._status, errors=self._errors, document=document)


class FailingConverter:
    def convert(self, file_path):
        raise ConversionError("Conversion failed with status: failure.")


def parse_regulation(converter):
    app.state.converter = converter
    return TestClient(app).post("/parse-regulation", files={"file": ("regulation.pdf", b"%PDF-1.7")})


def test_parse_regulation_returns_text_of_complete_conversion():
    response = parse_regulation(FakeConverter(ConversionStatus.SUCCESS, errors=[]))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == [{"label": DocItemLabel.TEXT, "text": REGULATION_TEXT}]


def test_parse_regulation_rejects_partial_conversion_with_text():
    response = parse_regulation(FakeConverter(ConversionStatus.PARTIAL_SUCCESS, errors=[PAGE_ERROR]))

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "INCOMPLETE_CONVERSION"}


def test_parse_regulation_rejects_failed_conversion():
    response = parse_regulation(FailingConverter())

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json() == {"detail": "CONVERSION_FAILED"}
