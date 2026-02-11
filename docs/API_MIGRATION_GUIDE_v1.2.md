# API Migration Guide: v1.1 -> v1.2

> **Date:** Feb 10, 2026
> **Version:** v1.2
> **Focus:** Architecture Normalization & Strict Typing

This document details the breaking changes introduced in version 1.2 of the Spellcasters Community API. If you are building tools (deck builders, wikis, analysis scripts) that consume this API, you likely need to update your parsers.

## 🚨 Breaking Changes

### 1. `incantation` is Dead

The generic `incantation` schema has been **deleted**. It previously acted as a catch-all for both Spells and Units, leading to loose validation.

- **Old Behavior:** All files in `data/spells/` and `data/units/` validated against `incantation.schema.json`.
- **New Behavior:**
  - Files in `data/spells/` now validate against **`spell.schema.json`**.
  - Files in `data/units/` now validate against **`unit.schema.json`**.

### 2. Strict `mechanics` Typing

We have moved from "wild west" JSON objects to strict definitions for `mechanics`.

- **Titans:** The `mechanics` object now enforces `additionalProperties: false`. If your tool was reading undocumented keys from Titans, those keys are now illegal and have been removed or standardized.
- **Spellcasters:** Now strictly defined via `common` definitions.

### 3. Asset Validation

Asset existence checks are now enforced for `unit` and `spell` types explicitly. Ensure your asset pipelines recognize these new schema keys.

## 🏗️ New Architecture

We have introduced a **Common Schema** library to standardize definitions across the entire API.

| Schema File              | Purpose               | Key Changes                                                                       |
| :----------------------- | :-------------------- | :-------------------------------------------------------------------------------- |
| **`common.schema.json`** | Shared definitions    | Contains `aura`, `damage_modifiers`, `changelog`, `spawner`.                      |
| **`unit.schema.json`**   | Creatures & Buildings | Inherits from `common`. Adds `health`, `movement_speed`, `collision`.             |
| **`spell.schema.json`**  | Spells                | Inherits from `common`. Adds `cooldown`, `cast_time`. **No longer has `health`**. |

## 🛠️ Developer Migration Checklist

If you maintain a tool that consumes this API:

1.  [ ] **Update Schema References:** If you validate our JSON files, update your validator to load `unit.schema.json` and `spell.schema.json` instead of expecting `incantation`.
2.  [ ] **Check `damage_modifiers`:**
    - The `target_type` field now officially supports **Arrays of Strings** in addition to single Strings.
    - _Example:_ `"target_type": ["Ground", "Hover"]` is now standard. Ensure your parser handles both `string` and `string[]`.
3.  [ ] **Verify "Unknown" Values:**
    - We are standardizing on `-1.0` (float) for unknown numerical values in Beta data.
4.  [ ] **Handling Spawners:**
    - The `spawner` mechanic structure is now identical across Units (Buildings) and Spellcasters (Abilities).

## 🔍 Example Diff

**Before (v1.1 - Incantation):**

```json
{
  "$schema": "../../schemas/v1/incantation.schema.json",
  "entity_id": "fire_ball",
  // ...
  "health": null // Irrelevant field often present
}
```

**After (v1.2 - Spell):**

```json
{
  "$schema": "../../schemas/v1/spell.schema.json",
  "entity_id": "fire_ball"
  // ...
  // No "health" field allowed
}
```
