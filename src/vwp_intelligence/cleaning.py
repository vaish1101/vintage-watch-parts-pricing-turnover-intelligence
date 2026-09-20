from __future__ import annotations

from .identity import canonical_inventory_id, clean_identifier, normalize_label


def positive_stock(value: object) -> int:
    try:
        stock = int(float(str(value).strip()))
    except (TypeError, ValueError):
        raise ValueError(f"Invalid stock quantity: {value!r}") from None
    if stock <= 0:
        raise ValueError("Stock must be positive for the public demo contract.")
    return stock


def normalize_inventory_row(row: dict) -> dict:
    brand = normalize_label(row.get("brand"))
    caliber = clean_identifier(row.get("caliber"))
    part_number = clean_identifier(row.get("part_number"))
    if not brand or not caliber or not part_number:
        raise ValueError("brand, caliber and part_number are required")
    return {
        "inventory_id": canonical_inventory_id(brand, caliber, part_number),
        "brand": brand,
        "caliber": caliber,
        "part_number": part_number,
        "part_name": normalize_label(row.get("part_name")) or "Watch component",
        "stock_quantity": positive_stock(row.get("stock_quantity")),
    }


def normalize_inventory(rows: list[dict]) -> list[dict]:
    output = []
    seen = set()
    for row in rows:
        clean = normalize_inventory_row(row)
        if clean["inventory_id"] in seen:
            raise ValueError(f"Duplicate inventory identity: {clean['inventory_id']}")
        seen.add(clean["inventory_id"])
        output.append(clean)
    return output

