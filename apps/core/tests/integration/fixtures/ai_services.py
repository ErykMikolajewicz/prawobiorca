from unittest.mock import create_autospec

import pytest

from core_service.application.ports.texts import TextsEmbedder
from core_service.shared.consts import VECTOR_LENGTH

QUERY_VECTOR = [1.0] * VECTOR_LENGTH
DESCRIPTION_VECTOR = [0.0, 1.0, *[0.0] * (VECTOR_LENGTH - 2)]
UNRELATED_VECTOR = [1.0, *[0.0] * (VECTOR_LENGTH - 1)]


@pytest.fixture
def mock_texts_embedder():
    embedder = create_autospec(TextsEmbedder)
    embedder.embed_queries.return_value = [QUERY_VECTOR]
    embedder.embed_texts.return_value = [DESCRIPTION_VECTOR]
    return embedder
