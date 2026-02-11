# Schema & Data Architecture Reference Guide

**Date:** 2026-02-10
**Status:** Implemented

This document outlines the changes made during the recent Schema Integrity & Validation Audit. These updates enforce stricter data validation and improve maintainability through DRY principles.

## 1. Centralized Schema Definitions (DRY)

Commonly used enum values and property definitions have been moved to `schemas/v1/common.schema.json` to prevent duplication and ensure consistency.

### New Shared Definitions:

- **`magic_school`**: Enum of all magic schools (Elemental, Wild, War, etc.)
- **`rank`**: Enum of ranks (I, II, III, IV, V)
- **`movement_type`**: Enum of movement types (Ground, Flying, Hover)
- **`image_required`**: Boolean flag (default: true)
- **`changelog`**: Standardized array of change objects.

**Developer Action:** When adding new properties to schemas (e.g., `unit`, `spell`, `spellcaster`, `titan`), ALWAYS use `$ref` to `common.schema.json` for these types instead of redefining them inline.

**Example Usage:**

```json
"magic_school": { "$ref": "common.schema.json#/definitions/magic_school" }
```

## 2. Strict Typing Enforcement

Nullable types (e.g., `["integer", "null"]`) have been REMOVED from `spellcaster.schema.json` within the `stats` object.

- **Rule:** If a stat (like `interval` or `damage`) is not relevant for an ability, **omit the key entirely**. Do NOT set it to `null`.
- **Impact:** All spellcaster data files have been updated to remove `null` values.

## 3. Required Fields

The following field is now **MANDATORY** in all major schemas (`unit`, `spell`, `spellcaster`, `titan`):

- **`tags`**: An array of strings. Even if empty, it must be present: `"tags": []`.

## 4. Terminology Standardization

To align data descriptions with schema terminology:

- **"Incantation"** has been replaced with **"Spell"** in all description text.
- **Validation:** Use `Spell` exclusively in all future documentation and data entries.

## 5. Titan Data Validation

Titan data files (`gaia_beast.json`, `thanatos.json`) now require a `$schema` reference for validation.

**Required Schema Reference:**

```json
"$schema": "../../schemas/v1/titan.schema.json"
```

## 6. Validation Script

The source of truth for data integrity is `scripts/validate_integrity.py`.

**Run Validation:**

```bash
python scripts/validate_integrity.py
```

This script includes:

- Validation for `$schema` references.
- Strict type compliance (no `null` where not allowed).
- Required fields (including `tags`).
- Referential integrity (e.g., `magic_school` values match the enum).
