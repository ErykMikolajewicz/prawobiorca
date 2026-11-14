import unicodedata
from typing import Annotated

from pydantic import AfterValidator

FORBIDDEN_NAME_CHARACTER_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Zl", "Zp"})


def validate_name_characters(name: str) -> str:
    if any(unicodedata.category(character) in FORBIDDEN_NAME_CHARACTER_CATEGORIES for character in name):
        raise ValueError("Name contains forbidden characters!")
    return name


Name = Annotated[str, AfterValidator(validate_name_characters)]
