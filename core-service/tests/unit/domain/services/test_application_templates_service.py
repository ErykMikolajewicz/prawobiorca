import pytest

from src.domain.services.application_templates import is_ready_to_publish, is_semantic_search_query
from src.domain.value_objects.application_templates import ApplicationTemplateStatus


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


@pytest.mark.parametrize(
    ("status", "instructions", "expected"),
    [
        (ApplicationTemplateStatus.DRAFT, "Instrukcje", True),
        (ApplicationTemplateStatus.DRAFT, None, False),
        (ApplicationTemplateStatus.DRAFT, " ", False),
        (ApplicationTemplateStatus.NOT_UPLOADED, "Instrukcje", False),
        (ApplicationTemplateStatus.PUBLISHED, "Instrukcje", False),
    ],
)
def test_is_ready_to_publish(status, instructions, expected):
    assert is_ready_to_publish(status, instructions) is expected
