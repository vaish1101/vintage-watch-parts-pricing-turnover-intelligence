import pytest

from vwp_intelligence.cleaning import normalize_inventory, normalize_inventory_row
from vwp_intelligence.identity import canonical_inventory_id, clean_identifier


def test_text_identifiers_are_preserved():
    assert clean_identifier("16-1") == "16-1"
    assert clean_identifier("330.0") == "330"
    assert canonical_inventory_id("Aurelius", "7", "16-1") == "aurelius_7_16_1"


def test_inventory_normalization_preserves_identity_fields():
    row = normalize_inventory_row({
        "brand": " Aurelius ", "caliber": "7", "part_number": "16-1",
        "part_name": "Balance bridge", "stock_quantity": "3",
    })
    assert row["caliber"] == "7"
    assert row["part_number"] == "16-1"
    assert row["stock_quantity"] == 3


def test_duplicate_inventory_identity_is_rejected():
    rows = [
        {"brand": "Aurelius", "caliber": "7", "part_number": "16-1", "stock_quantity": 1},
        {"brand": "Aurelius", "caliber": "7", "part_number": "16-1", "stock_quantity": 2},
    ]
    with pytest.raises(ValueError, match="Duplicate inventory identity"):
        normalize_inventory(rows)

