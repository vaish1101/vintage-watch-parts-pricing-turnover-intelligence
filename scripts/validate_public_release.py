from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_EXTENSIONS = {".duckdb", ".db", ".sqlite", ".sqlite3", ".xlsx", ".xls", ".parquet", ".zip", ".tar"}
FORBIDDEN_NAMES = {".env", ".ebay_token_cache.json"}
FORBIDDEN_TEXT = [
    "/" + "Users/", "EBAY_" + "CLIENT_SECRET", "EBAY_" + "CLIENT_ID=", "o" + "auth",
    "Stream" + "lit", "Postgre" + "SQL", "professor " + "submission",
    "Co" + "dex", "Clau" + "de",
]
REQUIRED = [
    "README.md", "dashboard/index.html", "dashboard/style.css", "dashboard/app.js",
    "dashboard/demo-data.json", "assets/architecture/system_architecture.svg",
    "assets/architecture/pricing_evidence_flow.svg",
    "assets/architecture/turnover_hierarchy.svg",
    "assets/screenshots/portfolio-overview.png", "assets/screenshots/inventory-pricing.png",
    "assets/screenshots/item-detail.png", ".github/workflows/ci.yml", ".github/workflows/pages.yml",
    "assets/screenshots/production/production-portfolio-overview.png",
    "assets/screenshots/production/production-inventory-pricing.png",
    "assets/screenshots/production/production-item-detail.png",
]


def validate() -> list[str]:
    errors = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"Missing required file: {relative}")
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_EXTENSIONS:
            errors.append(f"Forbidden artifact: {relative}")
        if path.suffix.lower() in {".py", ".md", ".html", ".css", ".js", ".json", ".yml", ".yaml", ".txt", ".svg"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in FORBIDDEN_TEXT:
                if term.lower() in text.lower():
                    errors.append(f"Forbidden text {term!r}: {relative}")
            if "\u2014" in text:
                errors.append(f"Em dash in public text: {relative}")
    data = json.loads((ROOT / "dashboard" / "demo-data.json").read_text(encoding="utf-8"))
    if data["metadata"]["data_classification"] != "SYNTHETIC_DEMONSTRATION_DATA":
        errors.append("Dashboard data is not explicitly marked synthetic")
    forbidden_fields = {"seller", "seller_username", "listing_id", "listing_url", "item_web_url", "email", "client_name"}
    for index, item in enumerate(data["items"]):
        overlap = forbidden_fields.intersection(item)
        if overlap:
            errors.append(f"Forbidden dashboard fields at item {index}: {sorted(overlap)}")
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
    for link in re.findall(r'(?:src|href)="([^"]+)"', html):
        if link.startswith(("http://", "https://", "#")):
            continue
        target = (ROOT / "dashboard" / link).resolve()
        if not target.exists():
            errors.append(f"Broken dashboard asset: {link}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for link in re.findall(r"\]\(([^)]+)\)", readme):
        if link.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = (ROOT / link.split("#", 1)[0]).resolve()
        if not target.exists():
            errors.append(f"Broken README link: {link}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print("Public release validation passed.")
