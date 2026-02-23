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

1. Ruff Check & Format
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

### `generate_patch.py`

**Usage:** `python scripts/generate_patch.py`
Computes differences for JSON files changed in the current git commit and automatically merges them into the current active patch block in `data/patches.json`.

- Creates timeline snapshots for newly added entities.
- Expects `BEFORE_SHA` and `AFTER_SHA` environment variables in CI (falls back to local `HEAD~1` and `HEAD`).

### `build_changelogs.py`

**Usage:** `python scripts/build_changelogs.py`
Reads `data/patches.json` and generates API-consumable files in the repository root:

- `changelog.json` — Full array of all patch entries.
- `changelog_latest.json` — Single most-recent patch object.
- `changelog_index.json` — Pagination manifest.
- `changelog_page_N.json` — Paginated chunks.

These root files are then copied into `api/v2/` by `build_api.py`.

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

## 🔑 CI/CD Environment Variables

Some scripts rely on environment variables when running in GitHub Actions:

- **`BEFORE_SHA`**: The commit SHA before the push. Used by `generate_patch.py` to diff changes. (Fallback: `HEAD~1`)
- **`AFTER_SHA`**: The commit SHA after the push. Used by `generate_patch.py`. (Fallback: `HEAD`)

> **Note:** The deploy workflow (`deploy.yml`) requires `contents:write`, `pages:write`, and `id-token:write` permissions.
> **Local Development:** You do **not** need a `.env` file to run scripts locally. They will gracefully fall back to local git history (`HEAD~1` and `HEAD`).
