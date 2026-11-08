from pathlib import Path

from tokenizers import Tokenizer as HFTokenizer


class MmlwTokenizer:
    max_tokens = 512

    def __init__(self, tokenizer_path: str | Path | None = None):
        if tokenizer_path is None:
            tokenizer_path = Path(__file__).parent / "tokenizer.json"
        self._tokenizer = HFTokenizer.from_file(str(tokenizer_path))
        self._tokenizer.no_truncation()

    def count_tokens(self, text: str) -> int:
        encoding = self._tokenizer.encode(text)
        return len(encoding.tokens)
