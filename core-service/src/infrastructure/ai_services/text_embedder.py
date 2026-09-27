from typing import Iterable

from httpx2 import AsyncClient, HTTPError

from src.domain.value_objects.sections import SectionChunk
from src.shared.exceptions import ServiceUnavailable

EMBEDDING_MODEL_NAME = "mmlw-retrieval-roberta-large-v2"


class TextsEmbedder:
    def __init__(self, client: AsyncClient, embedding_service_url: str):
        self._client = client
        self._embedding_url = f"{embedding_service_url}/v3/embeddings"

    async def embed_chunks(self, chunks: Iterable[SectionChunk]) -> list[list[float]]:
        return await self._embed([chunk.embedding_text for chunk in chunks])

    async def embed_queries(self, queries: Iterable[str]) -> list[list[float]]:
        prefix = "[query]: "

        return await self._embed([prefix + query for query in queries])

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.post(
                self._embedding_url, timeout=300, json={"model": EMBEDDING_MODEL_NAME, "input": texts}
            )
            response.raise_for_status()
        except HTTPError as e:
            raise ServiceUnavailable() from e
        embeddings_data = sorted(response.json()["data"], key=lambda item: item["index"])

        return [item["embedding"] for item in embeddings_data]
