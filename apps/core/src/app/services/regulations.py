import asyncio

from src.app.ports.regulations import RegulationSplitter
from src.app.ports.tokenizer import Tokenizer
from src.app.services.embedding import SectionsEmbedder
from src.domain.value_objects.regulations import RegulationAct
from src.domain.value_objects.sections import SectionsCollection


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

        sections = await asyncio.to_thread(regulation_act.get_sections_to_embed)

        await self._sections_embedder.embed_sections(sections)

        return sections
