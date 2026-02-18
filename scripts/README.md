# Helper Scripts

This directory contains Python scripts used for building, validating, and maintaining the Spellcasters Community API.

## 🛠️ Setup

Ensure you have Python 3.11+ installed and install dependencies:

```bash
pip install -r requirements.txt
```

## 📜 Scripts

### `build_api.py`

**Usage:** `python scripts/build_api.py`
Aggregates individual JSON files from `data/` into consolidated API responses in `api/v2/`.

- Generates collection files (e.g., `units.json`, `spells.json`).
- Generates a master `all_data.json` and `status.json`.
- Copies Patch History endpoints (`changelog*.json`, `timeline/`).

### `check.ps1`

**Usage:** `.\scripts\check.ps1` (PowerShell)
Local CI/CD runner that executes all checks sequentially:

1. Flake8 & Pylint
2. Unit Tests
3. Integrity Validation
4. Strictness Verification

### `validate_integrity.py`

**Usage:** `python scripts/validate_integrity.py`
Performs strict validation on the data to ensure API quality.

- **Schema Validation:** Checks every JSON file against its schema in `schemas/v2/`.
- **Reference Integrity:** Ensures logical links are valid (e.g., Upgrade targets reference existing Unit tags).
- **Asset Hygiene:** Checks for missing images and warns if images are too large (>100KB) or have incorrect dimensions.

### `check_data_consistency.py`

**Usage:** `python scripts/check_data_consistency.py`
Audits V2 data against the legacy V1 source of truth (`V1_all_data.json`) to control data migration quality.

- Generates a `consistency_report.txt` detailing mismatches.

### `release.py`

**Usage:** `python scripts/release.py`
Interactive CLI tool to handle version bumping and changelog generation.

- Updates `game_config.json` version.
- Prepends new entry to `CHANGELOG.md`.

### `validate_schemas.py`

**Usage:** `python scripts/validate_schemas.py`
A lightweight, pure-schema validation tool.

- Validates all data files against their schemas using `jsonschema` and `referencing`.
- Useful for quick syntax checks without the full integrity logic of `validate_integrity.py`.

### `verify_strictness.py`

**Usage:** `python scripts/verify_strictness.py`
Test suite for the schema system itself.

- Verifies that schemas correctly reject invalid data (e.g., unknown properties, bad patterns).
- Ensures "strict mode" is actually strict.

### `audit_v2.py`

**Usage:** `python scripts/audit_v2.py`
Tools for performing deep audits of the data and schema layers. These are typically run during major refactors or prior to a release to catch subtle logical errors.

### `config.py`

Shared configuration module containing paths, constants, and helper functions used by other scripts.
