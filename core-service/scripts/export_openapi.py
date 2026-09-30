import json
import sys

sys.path.append("")

from src.main import prawobiorca


def export_openapi():
    with open("openapi.json", "w", encoding="utf-8") as f:
        json.dump(prawobiorca.openapi(), f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    export_openapi()
