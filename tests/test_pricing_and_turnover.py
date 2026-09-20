from datetime import date

from vwp_intelligence.pricing import ASK_TO_SOLD_ADJUSTMENT, price_item, price_trend
from vwp_intelligence.turnover import estimate_turnover, turnover_from_hazard


ITEM = {"brand": "Aurelius", "caliber": "CAL-A1", "part_number": "SYN-1001", "stock_quantity": 2}


def hist(price, day, evidence_id):
    return {"evidence_id": evidence_id, "evidence_type": "historical", "price_eur": price, "sold_units": 1, "observed_at": day}


def active(price, evidence_id):
    return {"evidence_id": evidence_id, "evidence_type": "active", "price_eur": price, "observed_at": "2026-08-01"}


def test_historical_value_takes_precedence_over_active_asks():
    history = [hist(100, "2026-06-01", "H1"), hist(110, "2026-07-01", "H2")]
    low_active = [active(50, "A1")]
    high_active = [active(500, "A2")]
    first = price_item(ITEM, history, low_active, date(2026, 8, 1), 0.5, 0.5)
    second = price_item(ITEM, history, high_active, date(2026, 8, 1), 0.5, 0.5)
    assert first["recommended_price"] == second["recommended_price"]
    assert first["pricing_basis"] == "HISTORICAL_SUPPORTED"


def test_active_only_fallback_uses_adjustment():
    rows = [active(100, "A1"), active(120, "A2")]
    result = price_item(ITEM, [], rows, date(2026, 8, 1), 0.5, 0.5)
    assert result["recommended_price"] == round(110 * ASK_TO_SOLD_ADJUSTMENT, 2)
    assert result["pricing_basis"] == "ACTIVE_ONLY"


def test_trend_is_bounded():
    rows = [hist(10, "2026-01-01", "H1"), hist(1000, "2026-02-01", "H2")]
    assert price_trend(rows, 10) == 0.10


def test_price_bounds_expand_around_point_estimate():
    result = price_item(ITEM, [], [active(100, "A1")], date(2026, 8, 1), 0.5, 0.5)
    assert result["lower_bound"] < result["recommended_price"] < result["upper_bound"]


def test_abstention_with_no_evidence():
    result = price_item(ITEM, [], [], date(2026, 8, 1), 0.5, 0.5)
    assert result["recommended_price"] is None
    assert result["pricing_basis"] == "NO_RECOMMENDATION"


def test_turnover_probability_ranges():
    result = turnover_from_hazard(0.5)
    assert 0 <= result["p_sale_30d"] <= result["p_sale_90d"] <= 1
    assert result["median_days_to_sale"] > 0


def test_turnover_hierarchy_prefers_direct_then_cohort():
    history = [hist(100, "2026-07-01", "H1")]
    direct = estimate_turnover(ITEM, history, history, 3, history, 10, date(2026, 8, 1), True)
    cohort = estimate_turnover(ITEM, [], history * 3, 3, history, 10, date(2026, 8, 1), True)
    abstained = estimate_turnover(ITEM, [], [], 0, [], 0, date(2026, 8, 1), False)
    assert direct["turnover_method"] == "DIRECT_ITEM_HAZARD"
    assert cohort["turnover_method"] == "COMPARABLE_COHORT_HAZARD"
    assert abstained["median_days_to_sale"] is None

