# Helper Scripts

This directory contains Python scripts used for building, validating, and maintaining the Spellcasters Community API.

## 🛠️ Setup

Ensure you have Python 3.9+ installed and install dependencies:

```bash
pip install -r requirements.txt
```

## 📜 Scripts

### `build_api.py`

**Usage:** `python scripts/build_api.py`
Aggregates individual JSON files from `data/` into consolidated API responses in `api/v1/`.

- Generates collection files (e.g., `units.json`, `spells.json`).
- Generates a master `all_data.json`.

### `validate_integrity.py`

**Usage:** `python scripts/validate_integrity.py`
Performs strict validation on the data to ensure API quality.

- **Schema Validation:** Checks every JSON file against its schema in `schemas/v1/`.
- **Reference Integrity:** Ensures logical links are valid (e.g., Decks reference existing Cards).
- **Asset Hygiene:** Checks for missing images and warns if images are too large (>100KB) or have incorrect dimensions.

### `update_timestamps.py`

**Usage:** `python scripts/update_timestamps.py`
Automatically updates the `last_modified` timestamp in JSON files that have changed in git. This is typically run by CI/CD workflows but can be run locally before committing.

### `config.py`

Shared configuration module containing paths, constants, and helper functions used by other scripts.
