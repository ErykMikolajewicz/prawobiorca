import json
from http import HTTPStatus
from pathlib import Path

import httpx2
import pytest

from tests.consts import PARSING_TIMEOUT

DATA_DIR = Path(__file__).parents[1] / "data"


@pytest.mark.parametrize(
    "regulation_name",
    [
        "pwr-regulamin_2025_slice_7-9",
        "ustawa-nauka_slice_30-31",
    ],
)
def test_parse_regulation(parse_regulation_url, regulation_name):
    pdf_path = DATA_DIR / f"{regulation_name}.pdf"
    expected_response_path = DATA_DIR / f"{regulation_name}.json"

    with pdf_path.open("rb") as pdf_file:
        response = httpx2.post(
            parse_regulation_url,
            files={
                "file": (
                    pdf_path.name,
                    pdf_file,
                    "application/pdf",
                )
            },
            timeout=PARSING_TIMEOUT,
        )

    assert response.status_code == HTTPStatus.OK

    parsed_regulation = response.json()
    expected_regulation = json.loads(expected_response_path.read_text(encoding="utf-8"))

    assert parsed_regulation == expected_regulation
