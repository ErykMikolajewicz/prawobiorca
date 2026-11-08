import json
from pathlib import Path

from src.domain.value_objects.legal_units import RegulationElement

DATA_DIR = Path(__file__).parents[1] / "data"


def load_regulation_elements(regulation_name: str) -> list[RegulationElement]:
    raw_elements = json.loads((DATA_DIR / f"{regulation_name}.json").read_text(encoding="utf-8"))

    return [RegulationElement(label=element["label"], text=element["text"]) for element in raw_elements]
