# Project History & Changelog

## 2026-02-10: v1.2 - Architecture Normalization & Strict Typing

**Status:** Implemented
**Focus:** Schema Integrity, DRY Principles, and Strict Validation.

### 🚨 Breaking Changes for Tool Developers

If you maintain a tool (deck builder, wiki, analysis script) that consumes this API, you may need to update your parsers.

#### 1. `incantation` is Dead

The generic `incantation` schema has been **deleted**.

- **Old Behavior:** All files in `data/spells/` and `data/units/` validated against `incantation.schema.json`.
- **New Behavior:**
  - `data/spells/` -> **`spell.schema.json`**
  - `data/units/` -> **`unit.schema.json`**

#### 2. Strict `mechanics` Typing

- **Titans:** `mechanics` object now enforces `additionalProperties: false`.
- **Spellcasters:** Defined via `common` definitions.

#### 3. Data Standards (v1.2)

- **Multipliers:** Use standard multipliers (e.g., `1.5` for 150%).
- **Unknown Values:** Use `-1.0` as a sentinel for unknown numerical values.
- **`tags`**: Now mandatory for all major schemas, even if empty array `[]`.

### 🏗️ Architecture Changes

#### Centralized Schema Definitions (DRY)

Common definitions moved to `schemas/v2/definitions/*.schema.json`.

- **`magic_school`**: Enum of magic schools.
- **`rank`**: Enum of ranks (I-V).
- **`movement_type`**: Enum (Ground, Flying, Hover).
- **`image_required`**: Boolean flag.

#### Terminology Standardization

- **"Incantation"** -> **"Spell"** in all descriptions and docs.

### 🛡️ Validation & Integrity

The source of truth for validation is `scripts/validate_integrity.py`.

- **Run:** `python scripts/validate_integrity.py`
- Enforces `$schema` references, strict typing, and referential integrity.
