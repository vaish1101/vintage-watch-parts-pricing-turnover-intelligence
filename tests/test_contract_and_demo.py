import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_demo():
    return json.loads((ROOT / "dashboard" / "demo-data.json").read_text(encoding="utf-8"))


def test_contract_is_one_row_per_eligible_item():
    data = load_demo()
    ids = [row["inventory_id"] for row in data["items"]]
    assert len(ids) == data["portfolio"]["eligible_items"]
    assert len(ids) == len(set(ids))


def test_priced_plus_abstained_equals_eligible():
    portfolio = load_demo()["portfolio"]
    assert portfolio["priced_items"] + portfolio["abstained_items"] == portfolio["eligible_items"]


def test_demo_schema_and_forbidden_fields():
    data = load_demo()
    required = {
        "inventory_id", "brand", "caliber", "part_number", "part_name", "stock_quantity",
        "recommended_price", "lower_bound", "upper_bound", "pricing_confidence", "pricing_basis",
        "active_evidence_count", "historical_evidence_count", "turnover_method",
        "turnover_confidence", "median_days_to_sale", "p_sale_30d", "p_sale_90d",
        "no_recommendation_reason", "generated_at", "model_version",
    }
    forbidden = {"seller", "seller_username", "listing_id", "listing_url", "item_web_url", "client_name"}
    for row in data["items"]:
        assert required <= set(row)
        assert not forbidden.intersection(row)
    assert data["metadata"]["data_classification"] == "SYNTHETIC_DEMONSTRATION_DATA"


def test_demo_generation_is_deterministic():
    paths = [ROOT / "dashboard" / "demo-data.json", ROOT / "data" / "sample" / "synthetic_inventory.csv"]
    before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_demo_data.py")], cwd=ROOT, check=True, capture_output=True, text=True)
    after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    assert before == after


def test_probability_fields_are_bounded():
    for row in load_demo()["items"]:
        for key in ("p_sale_30d", "p_sale_90d"):
            assert row[key] is None or 0 <= row[key] <= 1
