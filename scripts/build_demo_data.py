from __future__ import annotations

import csv
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vwp_intelligence.cleaning import normalize_inventory  # noqa: E402
from vwp_intelligence.contract import build_dashboard_contract  # noqa: E402


BRANDS = ["Aurelius", "Montvale", "Northstar"]
CALIBERS = ["CAL-A1", "CAL-B2", "CAL-C3", "CAL-D4"]
PART_NAMES = [
    "Balance bridge", "Mainspring", "Setting wheel", "Crown wheel",
    "Minute pinion", "Barrel arbor", "Click spring", "Escape wheel",
    "Train bridge", "Winding stem", "Jewel setting", "Regulator arm",
]


def synthetic_inputs(seed: int = 2407) -> tuple[list[dict], dict[str, list[dict]]]:
    rng = random.Random(seed)
    raw_inventory = []
    for index in range(72):
        raw_inventory.append({
            "brand": BRANDS[index % len(BRANDS)],
            "caliber": CALIBERS[index % len(CALIBERS)],
            "part_number": f"SYN-{1001 + index}",
            "part_name": PART_NAMES[index % len(PART_NAMES)],
            "stock_quantity": 1 + (index * 7) % 11,
        })
    inventory = normalize_inventory(raw_inventory)
    candidates: dict[str, list[dict]] = {}
    base_date = date(2026, 8, 31)

    for index, item in enumerate(inventory):
        uid = item["inventory_id"]
        rows = []
        base_price = 24 + (index % 12) * 11 + (index // 12) * 7
        exact_title = f"{item['brand']} {item['caliber']} {item['part_number']} {item['part_name']} watch part"

        if index < 24:
            historical_count = 5 if index < 8 else (3 if index < 16 else 1)
            for number in range(historical_count):
                sold_price = round(base_price * (0.88 + 0.06 * number + rng.uniform(-0.04, 0.04)), 2)
                rows.append({
                    "evidence_id": f"H-{index:03d}-{number:02d}",
                    "evidence_type": "historical",
                    "title": exact_title,
                    "price_eur": sold_price,
                    "sold_units": 1 + (number % 3),
                    "observed_at": (base_date - timedelta(days=45 * (historical_count - number))).isoformat(),
                })
            active_count = 3 + index % 5
            for number in range(active_count):
                rows.append({
                    "evidence_id": f"A-{index:03d}-{number:02d}",
                    "evidence_type": "active",
                    "title": exact_title,
                    "price_eur": round(base_price * (1.12 + rng.uniform(-0.12, 0.12)), 2),
                    "observed_at": base_date.isoformat(),
                })
        elif index < 52:
            active_count = 6 if index < 40 else 2 + index % 3
            for number in range(active_count):
                volatility = 0.07 if index < 40 else 0.30
                rows.append({
                    "evidence_id": f"A-{index:03d}-{number:02d}",
                    "evidence_type": "active",
                    "title": exact_title,
                    "price_eur": round(base_price * (1.18 + rng.uniform(-volatility, volatility)), 2),
                    "observed_at": base_date.isoformat(),
                })
        elif index < 60:
            rows.append({
                "evidence_id": f"R-{index:03d}",
                "evidence_type": "active",
                "title": f"Otherbrand complete watch {item['caliber']}",
                "price_eur": round(base_price * 8.0, 2),
                "observed_at": base_date.isoformat(),
            })
        elif index < 66:
            rows.append({
                "evidence_id": f"L-{index:03d}",
                "evidence_type": "active",
                "title": f"{item['brand']} compatible generic watch component lot",
                "price_eur": round(base_price * 0.6, 2),
                "observed_at": base_date.isoformat(),
            })
        candidates[uid] = rows
    return inventory, candidates


def write_outputs(root: Path = ROOT) -> dict:
    inventory, candidates = synthetic_inputs()
    inventory_path = root / "data" / "sample" / "synthetic_inventory.csv"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    with inventory_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["brand", "caliber", "part_number", "part_name", "stock_quantity"])
        writer.writeheader()
        for row in inventory:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    contract = build_dashboard_contract(inventory, candidates)
    dashboard_path = root / "dashboard" / "demo-data.json"
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return contract


if __name__ == "__main__":
    result = write_outputs()
    print(f"Synthetic items: {result['portfolio']['eligible_items']}")
    print(f"Priced: {result['portfolio']['priced_items']}")
    print(f"Abstained: {result['portfolio']['abstained_items']}")
    print("Wrote data/sample/synthetic_inventory.csv")
    print("Wrote dashboard/demo-data.json")

