from core_service.domain.services.regulation_chunking import Tokenizer
from core_service.infrastructure.tokenizers.mmlw import MmlwTokenizer


def get_tokenizer() -> Tokenizer:
    return MmlwTokenizer()
