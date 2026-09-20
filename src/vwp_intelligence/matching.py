from __future__ import annotations

import re


WEIGHTS = {
    "part_number_exactness": 0.35,
    "brand_match": 0.25,
    "component_type_match": 0.20,
    "caliber_match": 0.10,
    "listing_quality": 0.10,
}
NEGATIVE_KEYWORDS = {
    "compatible", "replacement", "style", "alternative", "homage",
    "similar", "bundle", "lot", "generic", "aftermarket", "fits",
}
CONTRADICTIONS = {"complete watch", "bracelet", "dial", "case only", "manual"}


def _token(value: str, title: str) -> bool:
    return bool(value and re.search(r"\b" + re.escape(value.lower()) + r"\b", title.lower()))


def score_candidate(item: dict, candidate: dict) -> dict:
    title = str(candidate.get("title", ""))
    lower = title.lower()
    negative_hits = sorted(word for word in NEGATIVE_KEYWORDS if re.search(r"\b" + re.escape(word) + r"\b", lower))
    contradiction_hits = sorted(word for word in CONTRADICTIONS if word in lower)
    component = str(item.get("part_name", "")).lower()
    component_tokens = [x for x in re.findall(r"[a-z]+", component) if len(x) > 3]
    component_match = 1.0 if any(_token(x, title) for x in component_tokens) else 0.5
    components = {
        "part_number_exactness": 1.0 if _token(str(item["part_number"]), title) else 0.0,
        "brand_match": 1.0 if _token(str(item["brand"]), title) else 0.0,
        "component_type_match": component_match,
        "caliber_match": 1.0 if _token(str(item["caliber"]), title) else 0.5,
        "listing_quality": max(0.0, 1.0 - 0.34 * len(negative_hits)),
    }
    score = round(sum(components[name] * weight for name, weight in WEIGHTS.items()), 4)
    contradiction = bool(contradiction_hits) or components["brand_match"] == 0
    return {
        **candidate,
        "match_score": score,
        "score_components": components,
        "contradiction": contradiction,
        "negative_hits": negative_hits,
        "contradiction_hits": contradiction_hits,
    }

