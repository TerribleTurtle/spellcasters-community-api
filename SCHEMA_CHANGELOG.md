# Schema Changes - v1.4 Patch History System

## Overview

Adds JSON schemas and TypeScript types for the new patch history system. These define the shape of generated patch data served by the API.

## Changes

### 1. New Enums: `change_type_enum` & `patch_category_enum`

- **Location:** `definitions/enums.schema.json`
- **`change_type_enum`:** `add`, `edit`, `delete` — classifies per-entity changes.
- **`patch_category_enum`:** `Patch`, `Hotfix`, `Content` — classifies patch type.

### 2. New Schemas

- **`changelog_index.schema.json`** — Validates `api/v2/changelog_index.json`. Pagination manifest for changelog pages.
- **`changelog.schema.json`** — Validates paginated changelog pages. Array of patch entries with id, version, type, title, date, and changes array.
- **`timeline_entry.schema.json`** — Validates `api/v2/timeline/*.json`. Array of version snapshots with free-form entity state.

### 3. New TypeScript Types

- **`types/patch-history.d.ts`** — Consumer-facing type definitions: `ChangeType`, `PatchCategory`, `ChangeEntry`, `PatchEntry`, `ChangelogPage`, `ChangelogLatest`, `ChangelogIndex`, `TimelineEntry`, `EntityTimeline`.

### 4. Validation Pipeline

- `validate_integrity.py` now validates patch history files against their schemas.

## Developer Action Required

- None (additive change, no breaking changes).

---

> **UNSTABLE SCHEMA:** The schema is currently in flux. Breaking changes may occur without notice until the Early Access launch on **Feb 26th**.

# Schema Changes - v1.3 Hero Speed Cleanup

## Overview

This update removes the `movement_speed` attribute from Heroes to better reflect their gameplay implementation.

## Changes

### 1. `heroes.schema.json` Update

- **Removed:** `movement_speed` property.
- **Validation:** Presence of `movement_speed` is now forbidden.

### 2. `stats.schema.json` Refactor

- **New Definition:** `mobility_stats` (contains `movement_speed`).
- **Refactor:** `base_stats` (used by Heroes) no longer includes `movement_speed`.
- **Refactor:** `stats` (used by Units/Titans) includes `mobility_stats` via `allOf`.

## Developer Action Required

- Update Hero data parsers to ignore or remove `movement_speed`.

# Schema Changes - v1.2 Architecture Normalization

## Overview

This update deprecates the monolithic `incantation` schema in favor of specific `spell` and `unit` schemas. It also introduces a more granular structure for shared definitions.

## Changes

### 1. New Schemas

- **`definitions/core.schema.json`**: Contains core shared definitions (`aura`, `damage_modifiers`, `changelog`).
- **`definitions/stats.schema.json`**: Contains shared stat definitions.
- **`unit.schema.json`**: Validates Creatures and Buildings.
- **`spell.schema.json`**: Validates Spells.

### 2. Deprecations

- **`incantation.schema.json`**: **DELETED**.
- All data files in `data/units/` now point to `unit.schema.json`.
- All data files in `data/spells/` now point to `spell.schema.json`.

### 3. Standardization

- `damage_modifiers` now supports both single strings and arrays for `target_type` across all schemas.
- `titan` and `spellcaster` schemas now reference `definitions/core.schema.json` for shared fields.

# Schema Changes - v1.1 Movement Update

## Overview

This update standardizes how `mechanics` are defined across all entities and adds explicit traversal capabilities (Movement Types) to Spellcasters.

## Changes

### 1. New Field: `movement_type`

- **Location:** `heroes.schema.json` (Root)
- **Values:** `Ground` (Default), `Flying`, `Hover`
- **Purpose:** Explicitly defines the traversal mode of the entity for pathfinding and "Target Type" damage modifiers (e.g. "Deals 1.5x damage to Flying units").
- **Migration:** All existing Heroes have been initialized to `"movement_type": "Ground"`.

### 2. Standardized `mechanics`

- **Location:** `heroes.schema.json` -> `abilities`
- **Change:** Converted `mechanics` from a generic **Array** to a strict **Object**.
- **Structure:** Matches `spell.schema.json`.
  ```json
  "mechanics": {
    "aura": [...],
    "damage_modifiers": [...],
    "spawner": [...],
    "waves": 3,
    // ... other standard keys
  }
  ```
- **Rationale:** Allows a single parsing logic to handle mechanics for Units, Titans, and Hero Abilities.

### 3. New Stat: `stacks`

- **Location:** `heroes.schema.json` -> `stats`
- **Purpose:** define max stacks/charges for buffs/debuffs (e.g., defensive layers).

## Developer Action Required

- Update parsers to expect `movement_type` on Spellcaster objects.
- Update Ability parsers to handle `mechanics` as an Object, not an Array.
