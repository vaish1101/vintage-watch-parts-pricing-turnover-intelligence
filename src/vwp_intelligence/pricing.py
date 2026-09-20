from __future__ import annotations

import math
import statistics
from datetime import date, datetime


ASK_TO_SOLD_ADJUSTMENT = 0.79
TREND_WEIGHT = 1.0
TREND_CAP = 0.10
SCARCITY_WEIGHT = 0.10
DEMAND_WEIGHT = 0.05
RECENCY_HALFLIFE_MONTHS = 12.0


def _date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _age_months(value: str, reference: date) -> float:
    return max(0.0, (reference - _date(value)).days / 30.44)


def historical_value(rows: list[dict], reference: date) -> float | None:
    if not rows:
        return None
    numerator = denominator = 0.0
    for row in rows:
        weight = math.exp(-math.log(2) * _age_months(row["observed_at"], reference) / RECENCY_HALFLIFE_MONTHS)
        volume = max(1, int(row.get("sold_units", 1)))
        numerator += weight * float(row["price_eur"]) * volume
        denominator += weight * volume
    return numerator / denominator if denominator else None


def active_value(rows: list[dict]) -> float | None:
    return statistics.median(float(row["price_eur"]) for row in rows) * ASK_TO_SOLD_ADJUSTMENT if rows else None


def price_trend(rows: list[dict], base: float | None) -> float:
    dated = sorted(((_date(row["observed_at"]), float(row["price_eur"])) for row in rows), key=lambda x: x[0])
    if len(dated) < 2 or dated[0][0] == dated[-1][0]:
        return 0.0
    origin = dated[0][0]
    xs = [(day - origin).days / 30.44 for day, _ in dated]
    ys = [price for _, price in dated]
    xbar, ybar = statistics.mean(xs), statistics.mean(ys)
    denominator = sum((x - xbar) ** 2 for x in xs)
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denominator if denominator else 0.0
    reference = base or statistics.median(ys)
    return max(-TREND_CAP, min(TREND_CAP, slope / reference if reference else 0.0))


def percentile(values: list[float], target: float) -> float:
    if not values:
        return 0.5
    return sum(value <= target for value in values) / len(values)


def price_item(item: dict, historical: list[dict], active: list[dict], reference: date, demand: float, scarcity: float) -> dict:
    H = historical_value(historical, reference)
    C = active_value(active)
    if H is None and C is None:
        return {
            "recommended_price": None,
            "lower_bound": None,
            "upper_bound": None,
            "pricing_confidence": "LOW",
            "pricing_basis": "NO_RECOMMENDATION",
            "no_recommendation_reason": "NO_TRUSTWORTHY_EVIDENCE",
            "historical_value": None,
            "current_value": None,
            "demand_index": demand,
            "scarcity_score": scarcity,
            "price_trend": 0.0,
        }
    trend = price_trend(historical, H)
    base = H if H is not None else C
    value = base * (1 + TREND_WEIGHT * trend) * (1 + SCARCITY_WEIGHT * (scarcity - 0.5)) * (1 + DEMAND_WEIGHT * (demand - 0.5))
    if H is not None:
        if len(historical) >= 5:
            confidence = "HIGH"
        elif len(historical) >= 2 or (len(historical) == 1 and len(active) >= 5):
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        basis = "HISTORICAL_SUPPORTED"
    else:
        active_prices = [float(x["price_eur"]) for x in active]
        spread = (max(active_prices) - min(active_prices)) / statistics.median(active_prices) if len(active_prices) > 1 else 1.0
        confidence = "MEDIUM" if len(active) >= 5 and spread <= 1.5 else "LOW"
        basis = "ACTIVE_ONLY"
    band = {"HIGH": 0.15, "MEDIUM": 0.25, "LOW": 0.40}[confidence]
    return {
        "recommended_price": round(value, 2),
        "lower_bound": round(value * (1 - band), 2),
        "upper_bound": round(value * (1 + band), 2),
        "pricing_confidence": confidence,
        "pricing_basis": basis,
        "no_recommendation_reason": None,
        "historical_value": round(H, 2) if H is not None else None,
        "current_value": round(C, 2) if C is not None else None,
        "demand_index": round(demand, 4),
        "scarcity_score": round(scarcity, 4),
        "price_trend": round(trend, 4),
    }

