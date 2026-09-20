from __future__ import annotations

import math
from datetime import date, datetime


HALFLIFE_MONTHS = 12.0


def _day(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def recency_hazard(rows: list[dict], reference: date, item_count: int = 1) -> float:
    if not rows:
        return 0.0
    dates = [_day(row["observed_at"]) for row in rows]
    span = max(1.0, (reference - min(dates)).days / 30.44)
    effective_window = max(1.0, (HALFLIFE_MONTHS / math.log(2)) * (1 - math.exp(-math.log(2) * span / HALFLIFE_MONTHS)))
    weighted_units = 0.0
    for row in rows:
        age = max(0.0, (reference - _day(row["observed_at"])).days / 30.44)
        weighted_units += max(1, int(row.get("sold_units", 1))) * math.exp(-math.log(2) * age / HALFLIFE_MONTHS)
    return weighted_units / (effective_window * max(1, item_count))


def turnover_from_hazard(lam: float) -> dict:
    if lam <= 0:
        return {"median_days_to_sale": None, "p_sale_30d": None, "p_sale_90d": None}
    return {
        "median_days_to_sale": round(min(3650.0, 30.0 * math.log(2) / lam)),
        "p_sale_30d": round(1 - math.exp(-lam), 4),
        "p_sale_90d": round(1 - math.exp(-3 * lam), 4),
    }


def estimate_turnover(item: dict, item_history: list[dict], cohort_history: list[dict], cohort_items: int, portfolio_history: list[dict], portfolio_items: int, reference: date, priced: bool) -> dict:
    if not priced:
        return {
            "turnover_method": "NO_PRICE_RECOMMENDATION",
            "turnover_confidence": "LOW",
            "median_days_to_sale": None,
            "p_sale_30d": None,
            "p_sale_90d": None,
        }
    if item_history:
        method = "DIRECT_ITEM_HAZARD"
        confidence = "HIGH" if len(item_history) >= 3 or sum(int(x.get("sold_units", 1)) for x in item_history) >= 5 else "LOW"
        lam = recency_hazard(item_history, reference)
    elif cohort_history and cohort_items >= 3:
        method = "COMPARABLE_COHORT_HAZARD"
        confidence = "MEDIUM"
        lam = recency_hazard(cohort_history, reference, cohort_items)
    elif portfolio_history:
        method = "HIERARCHICAL_PORTFOLIO_PRIOR"
        confidence = "LOW"
        lam = recency_hazard(portfolio_history, reference, portfolio_items)
    else:
        method = "INSUFFICIENT_SOLD_EVIDENCE"
        confidence = "LOW"
        lam = 0.0
    return {"turnover_method": method, "turnover_confidence": confidence, **turnover_from_hazard(lam)}

