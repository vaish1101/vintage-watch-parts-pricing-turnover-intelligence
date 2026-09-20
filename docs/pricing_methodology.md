# Pricing methodology

## Historical-first value

When accepted sold evidence exists, the base value is a recency and volume weighted historical sold price. The recency half-life is 12 months.

When no accepted sold evidence exists, the model falls back to the median accepted active asking price multiplied by 0.79. Active only recommendations are clearly labelled and receive wider uncertainty treatment.

## Adjustments

The point estimate applies bounded adjustments:

```text
TMV = Base
    x (1 + price trend)
    x (1 + 0.10 x (scarcity - 0.5))
    x (1 + 0.05 x (demand - 0.5))
```

- Trend is the sold-price slope relative to historical value and is capped at plus or minus 10%.
- Scarcity compares active supply with sold volume within caliber peers.
- Demand ranks sold velocity within caliber peers.

## Parameter classification

| Parameter | Classification | Public interpretation |
|---|---|---|
| 0.79 ask adjustment | Implemented parameter, retrospectively benchmarked | Best of 0.79, 0.90 and 1.00 on the current same-snapshot comparison, but not independently validated |
| 12-month half-life | Business rule | Gives more influence to recent sold evidence |
| Trend weight 1.0 | Implemented scaling rule | Applies the measured and capped trend directly |
| Trend cap 10% | Guardrail | Prevents sparse trends from dominating price |
| Scarcity weight 0.10 | Implemented parameter | No reproducible independent calibration artifact was found |
| Demand weight 0.05 | Initial business parameter | Explicitly not backtested |

## Reproduced evaluation

The repaired evaluation reads the same accepted evidence classes as the current pricing implementation.

- Leave-one-evidence-out observations: 975
- Model MAE: EUR 83.50
- Model median absolute error: EUR 34.17
- Simple baseline MAE: EUR 82.88
- Simple baseline median absolute error: EUR 33.32

The model did not beat the simple baseline on MAE in this retrospective check. This limits any claim of predictive superiority.

For 236 items containing both historical and active signals, the median historical to active ratio was 0.786. The 0.79 active ask adjustment is therefore a retrospectively calibrated project parameter supported within the audited snapshot, not an independently validated universal market discount. Active only items have no accepted realized sale outcome in the snapshot and remain unvalidated as a separate segment.

Percentage errors are secondary because very low-price parts make them unstable.

## Bounds and confidence

The public sample uses wider bands as evidence weakens. The production contract also checks historical depth, price dispersion, identity strength and agreement between current and sold evidence before assigning the final client tier.
