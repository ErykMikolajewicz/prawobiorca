from dataclasses import dataclass

from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.texts import TextsEmbedder


@dataclass(frozen=True)
class McpDependencies:
    session_maker: SessionMaker
    texts_embedder: TextsEmbedder
