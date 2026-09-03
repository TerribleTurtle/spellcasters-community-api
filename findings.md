# Project Findings & Architectural Rules

## Architecture Overview
- **Type**: Static-site data API (Python scripts build/validate JSON, GitHub Pages serves `api/v2/`).
- **Data Source**: JSON files in `data/` directory.
- **Validation**: Strict JSON Schema Draft 2019-09 (`schemas/v2/`).

## Key Conventions
- **Data Integrity**: Never edit generated directories (`api/`, `timeline/`, `changelog*.json`).
- **Schema Updates**: Update `schemas/v2/` before adding any new fields to `data/`.
- **Validation Execution**: Run `python scripts/validate_integrity.py` to check for issues.

## Security & Vulnerability Policy (`docs/SECURITY.md`)
- **Static API Scope**: Scope limited to JSON data integrity, build scripts, and GitHub Actions workflows.
- **Node.js Dev Dependencies**: Vulnerabilities in transitive Node dependencies (like `fast-uri`, `js-yaml`, `qs`, `brace-expansion`) are resolved via the `overrides` block in `package.json` to enforce patched versions across the dependency tree without waiting for upstream library updates.
- **Accepted Exceptions**:
  - **`elliptic` (Alert #4)**: Located in dev dependency chain (`browserify` -> `elliptic`). Package is on latest version (`6.6.1`) with no patch available. Recognized as an accepted local dev build exception in `docs/SECURITY.md` and currently ignored.

## Rejected Approaches
- (None recorded yet)

