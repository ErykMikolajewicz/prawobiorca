from src.app.ports.tokenizer import Tokenizer
from src.infrastructure.tokenizers.mmlw import MmlwTokenizer


def get_tokenizer() -> Tokenizer:
    return MmlwTokenizer()
