import pytest
from fastapi import status

from core_service.application.dtos.names import validate_name_characters
from core_service.domain.consts import MAX_CASE_NAME_LENGTH


@pytest.mark.parametrize(
    "name",
    [
        "Sprawa o zapłatę",
        "Umowa najmu — aneks nr 2 (wersja 1/2)",
        "§ 12 ust. 3",
        "Ustawa z\u00a0dnia 23 kwietnia 1964 r.",
        "Żółć 😀",
    ],
    ids=("plain", "punctuation", "paragraph sign", "non-breaking space", "diacritics and emoji"),
)
def test_valid_name_characters(name):
    assert validate_name_characters(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "\x00",
        "a\tb",
        "a\nb",
        "\x1b[31mred",
        "\u202efdp.exe",
        "\ufeffname",
        "a\u2028b",
        "\ue000",
    ],
    ids=(
        "null",
        "tab",
        "new line",
        "escape",
        "right-to-left override",
        "byte order mark",
        "line separator",
        "private use",
    ),
)
def test_invalid_name_characters(name):
    with pytest.raises(ValueError, match="Name contains forbidden characters!"):
        validate_name_characters(name)


@pytest.mark.parametrize(
    "case_name",
    ["", "a" * (MAX_CASE_NAME_LENGTH + 1), "\x00"],
    ids=("empty case name", "case name too long", "case name with null character"),
)
async def test_add_case_validation(client, case_name):
    response = await client.post("/api/cases", data={"caseName": case_name})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
