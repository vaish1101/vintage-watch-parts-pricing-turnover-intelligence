from __future__ import annotations

import csv
from pathlib import Path

from .cleaning import normalize_inventory


def read_inventory_csv(path: str | Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return normalize_inventory(rows)

