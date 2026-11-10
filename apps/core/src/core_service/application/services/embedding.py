from core_service.application.ports.texts import TextsEmbedder
from core_service.domain.value_objects.sections import SectionsCollection


class SectionsEmbedder:
    def __init__(self, texts_embedder: TextsEmbedder, batch_size: int):
        self._texts_embedder = texts_embedder
        self._batch_size = batch_size

    async def embed_sections(self, sections_collection: SectionsCollection) -> None:
        for batch in sections_collection.get_chunks_batch_iterator(self._batch_size):
            batch_vectors = await self._texts_embedder.embed_chunks(batch)
            for chunk, vector in zip(batch, batch_vectors, strict=True):
                chunk.vector = vector


async def embed_description(texts_embedder: TextsEmbedder, description: str | None) -> list[float] | None:
    if description is None or not description.strip():
        return None

    vectors = await texts_embedder.embed_texts([description])
    return vectors[0]
