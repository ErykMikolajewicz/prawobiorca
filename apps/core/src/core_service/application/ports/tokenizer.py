from typing import Protocol


class Tokenizer(Protocol):
    max_tokens: int

    def count_tokens(self, text: str) -> int: ...
