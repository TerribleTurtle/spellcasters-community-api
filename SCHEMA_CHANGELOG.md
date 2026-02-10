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
