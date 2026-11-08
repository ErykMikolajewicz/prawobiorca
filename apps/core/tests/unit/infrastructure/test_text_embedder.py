import json

import pytest
from httpx2 import AsyncClient, ConnectError, MockTransport, Response

from src.domain.value_objects.sections import SectionChunk
from src.infrastructure.ai_services.text_embedder import EMBEDDING_MODEL_NAME, TextsEmbedder
from src.shared.exceptions import ServiceUnavailable

EMBEDDING_SERVICE_URL = "http://embedding.local"


def create_embedder(handler) -> TextsEmbedder:
    return TextsEmbedder(AsyncClient(transport=MockTransport(handler)), EMBEDDING_SERVICE_URL)


def respond_with_vectors(requests: list):
    def handler(request):
        requests.append(request)
        texts_count = len(json.loads(request.content)["input"])
        return Response(
            200,
            json={"data": [{"index": index, "embedding": [float(index)]} for index in reversed(range(texts_count))]},
        )

    return handler


def get_sent_texts(request) -> list[str]:
    body = json.loads(request.content)
    assert body["model"] == EMBEDDING_MODEL_NAME
    return body["input"]


async def test_embed_queries_sends_prefixed_queries_and_returns_vectors_in_input_order():
    requests = []

    vectors = await create_embedder(respond_with_vectors(requests)).embed_queries(["urlop", "stypendium"])

    assert vectors == [[0.0], [1.0]]
    (request,) = requests
    assert request.url == f"{EMBEDDING_SERVICE_URL}/v3/embeddings"
    assert get_sent_texts(request) == ["[query]: urlop", "[query]: stypendium"]


async def test_embed_texts_sends_texts_without_prefix():
    requests = []

    await create_embedder(respond_with_vectors(requests)).embed_texts(["Opis regulaminu."])

    assert get_sent_texts(requests[0]) == ["Opis regulaminu."]


async def test_embed_chunks_sends_chunks_with_their_titles():
    requests = []
    chunk = SectionChunk(text="Student ma prawo do urlopu.", chunk_index=0, embed_title="Art. 1")

    await create_embedder(respond_with_vectors(requests)).embed_chunks([chunk])

    assert get_sent_texts(requests[0]) == ["Art. 1\nStudent ma prawo do urlopu."]


def fail_with_connection_error(request):
    raise ConnectError("Connection refused", request=request)


@pytest.mark.parametrize(
    "handler", [lambda request: Response(503), fail_with_connection_error], ids=("error status", "connection error")
)
async def test_embedding_failure_raises_service_unavailable(handler):
    with pytest.raises(ServiceUnavailable):
        await create_embedder(handler).embed_texts(["Opis."])
