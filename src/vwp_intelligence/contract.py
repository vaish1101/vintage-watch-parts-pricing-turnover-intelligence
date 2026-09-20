from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from .evidence import accepted_unique_evidence, classify_evidence
from .pricing import percentile, price_item
from .turnover import estimate_turnover


GENERATED_AT = "2026-09-01T00:00:00Z"
MODEL_VERSION = "public-demo-1.0"


def build_dashboard_contract(inventory: list[dict], candidates_by_item: dict[str, list[dict]]) -> dict:
    accepted = {}
    all_scored = {}
    historical_by_item = {}
    active_by_item = {}
    all_dates = []
    for item in inventory:
        uid = item["inventory_id"]
        candidates = candidates_by_item.get(uid, [])
        all_scored[uid] = classify_evidence(item, candidates)
        accepted[uid] = accepted_unique_evidence(item, candidates)
        historical_by_item[uid] = [x for x in accepted[uid] if x["evidence_type"] == "historical"]
        active_by_item[uid] = [x for x in accepted[uid] if x["evidence_type"] == "active"]
        all_dates.extend(x["observed_at"] for x in historical_by_item[uid])
    reference = max(datetime.fromisoformat(x.replace("Z", "+00:00")).date() for x in all_dates) if all_dates else date(2026, 9, 1)

    velocities = {}
    scarcity_raw = {}
    for item in inventory:
        uid = item["inventory_id"]
        sold = sum(int(x.get("sold_units", 1)) for x in historical_by_item[uid])
        velocities[uid] = sold
        scarcity_raw[uid] = len(active_by_item[uid]) / (sold + 1)

    cohort_values = defaultdict(lambda: {"velocity": [], "scarcity": []})
    for item in inventory:
        key = (item["brand"], item["caliber"])
        cohort_values[key]["velocity"].append(velocities[item["inventory_id"]])
        cohort_values[key]["scarcity"].append(scarcity_raw[item["inventory_id"]])

    histories_by_cohort = defaultdict(list)
    items_by_cohort = defaultdict(int)
    all_history = []
    for item in inventory:
        uid = item["inventory_id"]
        key = (item["brand"], item["caliber"])
        histories_by_cohort[key].extend(historical_by_item[uid])
        items_by_cohort[key] += 1
        all_history.extend(historical_by_item[uid])

    output = []
    for item in inventory:
        uid = item["inventory_id"]
        key = (item["brand"], item["caliber"])
        demand = percentile(cohort_values[key]["velocity"], velocities[uid])
        scarcity = 1.0 - percentile(cohort_values[key]["scarcity"], scarcity_raw[uid])
        pricing = price_item(item, historical_by_item[uid], active_by_item[uid], reference, demand, scarcity)
        if pricing["recommended_price"] is None:
            if not all_scored[uid]:
                pricing["no_recommendation_reason"] = "NO_CANDIDATES"
            elif all(x["confidence_tier"] == "REJECTED" for x in all_scored[uid]):
                pricing["no_recommendation_reason"] = "ALL_CANDIDATES_REJECTED"
            else:
                pricing["no_recommendation_reason"] = "ONLY_LOW_CONFIDENCE_CANDIDATES"
        turnover = estimate_turnover(
            item,
            historical_by_item[uid],
            histories_by_cohort[key],
            items_by_cohort[key],
            all_history,
            len(inventory),
            reference,
            pricing["recommended_price"] is not None,
        )
        output.append({
            **item,
            **pricing,
            "active_evidence_count": len(active_by_item[uid]),
            "historical_evidence_count": len(historical_by_item[uid]),
            **turnover,
            "generated_at": GENERATED_AT,
            "model_version": MODEL_VERSION,
        })

    priced = [x for x in output if x["recommended_price"] is not None]
    portfolio_value = sum(x["recommended_price"] * x["stock_quantity"] for x in priced)
    return {
        "metadata": {
            "title": "Vintage Watch Parts Pricing & Turnover Intelligence",
            "data_classification": "SYNTHETIC_DEMONSTRATION_DATA",
            "notice": "Synthetic portfolio demo. Production data remains private.",
            "generated_at": GENERATED_AT,
            "model_version": MODEL_VERSION,
        },
        "portfolio": {
            "eligible_items": len(output),
            "stock_units": sum(x["stock_quantity"] for x in output),
            "priced_items": len(priced),
            "abstained_items": len(output) - len(priced),
            "recommended_portfolio_value": round(portfolio_value, 2),
            "historical_supported": sum(x["pricing_basis"] == "HISTORICAL_SUPPORTED" for x in priced),
            "active_only": sum(x["pricing_basis"] == "ACTIVE_ONLY" for x in priced),
        },
        "items": output,
    }
