from vwp_intelligence.evidence import accepted_unique_evidence, classify_evidence
from vwp_intelligence.matching import score_candidate


ITEM = {
    "brand": "Aurelius", "caliber": "CAL-A1", "part_number": "SYN-1001",
    "part_name": "Balance bridge",
}


def candidate(title, evidence_id="E-1", observed_at="2026-08-01"):
    return {"evidence_id": evidence_id, "evidence_type": "active", "title": title, "price_eur": 50, "observed_at": observed_at}


def test_exact_identity_receives_strong_score():
    result = score_candidate(ITEM, candidate("Aurelius CAL-A1 SYN-1001 balance bridge watch part"))
    assert result["match_score"] == 1.0
    assert result["contradiction"] is False


def test_brand_and_product_contradiction_is_rejected():
    rows = classify_evidence(ITEM, [candidate("Otherbrand complete watch CAL-A1")])
    assert rows[0]["confidence_tier"] == "REJECTED"


def test_duplicate_evidence_keeps_newest_observation():
    rows = [
        candidate("Aurelius CAL-A1 SYN-1001 balance bridge watch part", observed_at="2026-07-01"),
        {**candidate("Aurelius CAL-A1 SYN-1001 balance bridge watch part", observed_at="2026-08-01"), "price_eur": 55},
    ]
    accepted = accepted_unique_evidence(ITEM, rows)
    assert len(accepted) == 1
    assert accepted[0]["price_eur"] == 55

