# Schema Changes - v1.4 Patch History System

## Overview

Adds JSON schemas and TypeScript types for the new patch history system. These define the shape of generated patch data served by the API.

## Changes

### 1. New Enum: `patch_type_enum`

- **Location:** `definitions/enums.schema.json`
- **Values:** `buff`, `nerf`, `rework`, `fix`, `new`
- **Purpose:** Classifies balance changes for deckbuilder icons and patch displays.

### 2. New Schemas

- **`balance_index.schema.json`** — Validates `api/v2/balance_index.json`. Maps entity IDs to `patch_type_enum`.
- **`changelog.schema.json`** — Validates `api/v2/changelog.json`. Array of patch entries with version, date, description, and affected entities.
- **`timeline_entry.schema.json`** — Validates `api/v2/timeline/*.json`. Array of version snapshots with free-form entity state.

### 3. New TypeScript Types

- **`types/patch-history.d.ts`** — Consumer-facing type definitions: `PatchType`, `BalanceIndex`, `PatchEntry`, `Changelog`, `ChangelogLatest`, `TimelineEntry`, `EntityTimeline`.

### 4. Validation Pipeline

- `validate_integrity.py` now validates patch history files against their schemas.

## Developer Action Required

- None (additive change, no breaking changes).

---

> **UNSTABLE SCHEMA:** The schema is currently in flux. Breaking changes may occur without notice until the Early Access launch on **Feb 26th**.

# Schema Changelog - v1.1 Movement Update

## Overview

This update standardizes how `mechanics` are defined across all entities and adds explicit traversal capabilities (Movement Types) to Spellcasters.

## Changes

### 1. New Field: `movement_type`

- **Location:** `spellcaster.schema.json` (Root)
- **Values:** `Ground` (Default), `Flying`, `Hover`
- **Purpose:** Explicitly defines the traversal mode of the entity for pathfinding and "Target Type" damage modifiers (e.g. "Deals 1.5x damage to Flying units").
- **Migration:** All existing spellcasters have been initialized to `"movement_type": "Ground"`.

### 2. Standardized `mechanics`

- **Location:** `spellcaster.schema.json` -> `abilities`
- **Change:** Converted `mechanics` from a generic **Array** to a strict **Object**.
- **Structure:** Matches `incantation.schema.json`.
  ```json
  "mechanics": {
    "aura": [...],
    "damage_modifiers": [...],
    "spawner": [...],
    "waves": 3,
    // ... other standard keys
  }
  ```
- **Rationale:** Allows a single parsing logic to handle mechanics for Units, Titans, and Spellcaster Abilities.

### 3. New Stat: `stacks`

- **Location:** `spellcaster.schema.json` -> `stats`
- **Purpose:** define max stacks/charges for buffs/debuffs (e.g., defensive layers).

## Developer Action Required

- Update parsers to expect `movement_type` on Spellcaster objects.
- Update Ability parsers to handle `mechanics` as an Object, not an Array.

# Schema Changes - v1.2 Architecture Normalization

## Overview

This update deprecates the monolithic `incantation` schema in favor of specific `spell` and `unit` schemas. It also introduces a `common` schema for shared definitions.

## Changes

### 1. New Schemas

- **`unit.schema.json`**: Inherits from `common`. Validates Creatures and Buildings.
- **`spell.schema.json`**: Inherits from `common`. Validates Spells.
- **`common.schema.json`**: Contains shared definitions (`aura`, `damage_modifiers`, `changelog`).

### 2. Deprecations

- **`incantation.schema.json`**: **DELETED**.
- All data files in `data/units/` now point to `unit.schema.json`.
- All data files in `data/spells/` now point to `spell.schema.json`.

### 3. Standardization

- `damage_modifiers` now supports both single strings and arrays for `target_type` across all schemas.
- `titan` and `spellcaster` schemas now reference `common.schema.json` for shared fields.

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
