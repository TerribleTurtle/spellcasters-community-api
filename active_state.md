# Project State

## Current Focus

Deployment Verified — Ready to push to `main`.

## Status: DEPLOY READY

- **Audit**: PASSED (0 Errors, 8 Warnings - known asset gaps).
- **Lint**: Flake8 clean, Pylint 10/10.
- **Tests**: All passing (pytest).
- **Build**: API artifacts generated successfully (including patch history).
- **CI/CD**: `deploy.yml` patched to include strictness check.

## Recent Changes

- **Build Script:**
  - `build_api.py` now copies changelog + timeline data into `api/v2/`.
  - Stale timeline files are cleaned before each copy.
- **Data Fix:**
  - Renamed `timeline/*.json.json` → `*.json` (double-extension bug from mock generation).
- **Schema Refactor:**
  - Deleted `balance_index` (Legacy).
  - Added `changelog_index` (Pagination).
  - Standardized Enums (`change_type`, `patch_category`).
- **Validation:**
  - `validate_integrity.py` now checks patch history scaffolds.
- **Cleanup:**
  - Removed stale references from all docs.

## Todo

- [x] Run `/deploy` to confirm build artifacts.
- [ ] Commit & push to trigger GitHub Pages deploy.
- [ ] Wait for "Early Access" launch (Feb 26th).
