from __future__ import annotations

from datetime import datetime

from .matching import score_candidate


def classify_evidence(item: dict, candidates: list[dict]) -> list[dict]:
    scored = []
    for candidate in candidates:
        row = score_candidate(item, candidate)
        if row["contradiction"]:
            tier = "REJECTED"
        elif row["match_score"] >= 0.95:
            tier = "AUTO_CONFIRMED"
        elif row["match_score"] >= 0.80:
            tier = "HIGH_CONFIDENCE"
        else:
            tier = "LOW_CONFIDENCE"
        row["confidence_tier"] = tier
        scored.append(row)
    return scored


def accepted_unique_evidence(item: dict, candidates: list[dict]) -> list[dict]:
    accepted = [
        row for row in classify_evidence(item, candidates)
        if row["confidence_tier"] in {"AUTO_CONFIRMED", "HIGH_CONFIDENCE"}
    ]
    newest: dict[str, dict] = {}
    for row in accepted:
        key = str(row["evidence_id"])
        stamp = datetime.fromisoformat(str(row.get("observed_at", "2000-01-01")).replace("Z", "+00:00"))
        previous = newest.get(key)
        if previous is None or stamp > previous[0]:
            newest[key] = (stamp, row)
    return [value[1] for value in newest.values()]

