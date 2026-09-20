from __future__ import annotations

import re


def clean_identifier(value: object) -> str:
    """Preserve identifier semantics while removing spreadsheet artifacts."""
    text = "" if value is None else str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def normalize_label(value: object) -> str:
    return re.sub(r"\s+", " ", clean_identifier(value)).strip()


def canonical_inventory_id(brand: object, caliber: object, part_number: object) -> str:
    parts = [normalize_label(x).lower() for x in (brand, caliber, part_number)]
    normalized = [re.sub(r"[^a-z0-9]+", "_", part).strip("_") or "unknown" for part in parts]
    return "_".join(normalized)

