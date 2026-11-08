from core_service.application.ports.tokenizer import Tokenizer
from core_service.infrastructure.tokenizers.mmlw import MmlwTokenizer


def get_tokenizer() -> Tokenizer:
    return MmlwTokenizer()
