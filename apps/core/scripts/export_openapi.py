import json
import sys
from pathlib import Path

sys.path.append("")

from src.main import prawobiorca


def export_openapi():
    with Path("openapi.json").open("w", encoding="utf-8") as f:
        json.dump(prawobiorca.openapi(), f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    export_openapi()
