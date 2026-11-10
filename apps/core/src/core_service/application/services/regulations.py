from fastapi.concurrency import run_in_threadpool

from core_service.application.ports.regulations import RegulationSplitter
from core_service.application.services.embedding import SectionsEmbedder
from core_service.domain.services.regulation_chunking import RegulationAct, Tokenizer
from core_service.domain.value_objects.sections import SectionsCollection


class RegulationPreparator:
    def __init__(
        self,
        regulation_splitter: RegulationSplitter,
        sections_embedder: SectionsEmbedder,
        tokenizer: Tokenizer,
    ):
        self._regulation_splitter = regulation_splitter
        self._sections_embedder = sections_embedder
        self._tokenizer = tokenizer

    async def prepare_regulation(self, regulation: bytes) -> SectionsCollection:
        regulations_elements = await self._regulation_splitter.split(regulation)
        regulation_act = RegulationAct(regulations_elements, self._tokenizer)

        sections = await run_in_threadpool(regulation_act.get_sections_to_embed)

        await self._sections_embedder.embed_sections(sections)

        return sections
