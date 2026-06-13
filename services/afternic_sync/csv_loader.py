import csv
from pathlib import Path


def read_csv(path: str | Path) -> list[dict]:
    path = Path(path)

    if not path.exists():
        print(f"Afternic file not found: {path}")
        return []

    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))