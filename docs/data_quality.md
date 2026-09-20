# Data quality and governance

## Stable identities

Inventory identity is deterministic from normalized brand, caliber and part number. Caliber and part number remain text identifiers.

Marketplace evidence uses a stable evidence identity. Repeated observations of the same physical listing are reduced to the newest observation before evidence counts or price medians are calculated.

## Source grain

Active listings represent current asking prices. Individual sold exports represent transactions. Aggregate historical rows may represent multiple sold units at an average price. These grains are kept explicit and are not silently counted as equivalent transactions.

## Snapshot scope

The private audit found 7,204 old decision rows and two old summary rows whose inventory identities were not present in the current staging snapshot. All orphan decision rows were non-confirmed states. Current pricing joins accepted evidence to current eligible inventory and the final dashboard contract contains 728 unique current items, so stale rows do not enter current client outputs.

The operational improvement is to add explicit snapshot or upload-batch scope to decision and summary tables. Historical records should be retired through a controlled migration, not blindly deleted.

## Abstention

No-recommendation outcomes are part of the product contract. Common reasons include no candidates, rejected contradictions and only low-confidence candidates. An abstention is preferable to an unsupported precise price.

## Public data

Every row in the public dashboard is intentionally fabricated. It does not preserve real client combinations of part number, stock, listing identity or evidence.

