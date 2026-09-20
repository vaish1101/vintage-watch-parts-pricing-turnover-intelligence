from __future__ import annotations

import json
from pathlib import Path

from build_demo_data import ROOT, write_outputs


def main() -> None:
    contract = write_outputs(ROOT)
    portfolio = contract["portfolio"]
    print("Vintage Watch Parts Pricing & Turnover Intelligence")
    print("Synthetic public pipeline completed successfully.")
    print(json.dumps(portfolio, indent=2, sort_keys=True))
    print(f"Dashboard: {(Path(ROOT) / 'dashboard' / 'index.html').resolve()}")


if __name__ == "__main__":
    main()

