# Reproduce the public demo

The public pipeline is offline and deterministic. It does not require credentials, a database or network access.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Build the synthetic contract

```bash
python scripts/run_sample_pipeline.py
```

This recreates:

- `data/sample/synthetic_inventory.csv`
- `dashboard/demo-data.json`

## Run tests

```bash
python -m pytest -q
python scripts/validate_public_release.py
```

## View the dashboard locally

```bash
python -m http.server 8080 --directory dashboard
```

Open `http://localhost:8080/`.

The reproduction workflow intentionally does not reconstruct private client inventory, raw marketplace exports or the operational database.

