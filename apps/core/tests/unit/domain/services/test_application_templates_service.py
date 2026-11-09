import pytest

from core_service.domain.services.application_templates import is_semantic_search_query


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("urlop", False),
        ("  urlop", False),
        ("urlop ", True),
        ("urlop dziekański", True),
        ("  urlop dziekański", True),
    ],
)
def test_is_semantic_search_query(query, expected):
    assert is_semantic_search_query(query) is expected
