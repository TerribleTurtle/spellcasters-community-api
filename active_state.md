# Project State

## Current Focus

Deployment Readiness & UI Polish.

## Recent Changes

- **UI Polish:** Implemented Dark Mode for `index.html` documentation.
- **CI/CD:** Fixed linting errors in `scripts/migration/remove_hero_speed.py`.
- **Verification:** Passed `flake8`, `pytest`, and `validate_integrity.py`.
- Added JSON schemas for patch history (`balance_index`, `changelog`, `timeline_entry`).
- Added `patch_type_enum` to `enums.schema.json`.
- Created TypeScript types: `types/patch-history.d.ts`.
- Updated `validate_integrity.py` to validate patch files.
- Updated `CONTRIBUTING.md` and `SCHEMA_CHANGELOG.md` (v1.4).
- Created patch history scaffold: `balance_index.json`, `changelog.json`, `changelog_latest.json`.
- Updated `build_api.py` to preserve patch history files during build.
- Added Patch History documentation to `README.md` and `index.html`.
- Removed `movement_speed` from Hero schema and data.
- Updated `stats.schema.json` to decouple speed from base stats.

## Todo

- [x] Build local artifacts (Current).
