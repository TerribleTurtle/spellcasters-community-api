# Schema & API Migration Specification

> **Status**: Fully Implemented (v1.5)
> **Last Updated**: 2026-02-08
> **Note**: This document serves as the architectural reference for the v1 API.

## 1. Domain Terminology Changes

| Old Term          | New Term        | Definition / Notes                                                                             |
| :---------------- | :-------------- | :--------------------------------------------------------------------------------------------- |
| **Hero**          | **Spellcaster** | The player-controlled character.                                                               |
| **Unit** (Broad)  | **Incantation** | **Base Type**. All deck-able items (Spells, Creatures, Buildings).                             |
| **Unit** (Narrow) | **Unit**        | A sub-group of Incantations containing **Creatures** and **Buildings** (Entities with Health). |
| **Spell**         | **Spell**       | A sub-group of Incantations containing **Spells** (Instant Actions).                           |
| **Titan**         | **Titan**       | A unique Class-Ultimate entity (separated from standard Units).                                |
| **Loot**          | **Consumable**  | Items found in chests (separated from Units).                                                  |
| **Stats Object**  | **Root Stats**  | `stats` object removed. Properties (`health`, `damage`) moved to root.                         |

---

## 2. File Structure Changes

### JSON Data (`api/v1/`)

| Legacy File   | Current File        | Content Logic                                                  |
| :------------ | :------------------ | :------------------------------------------------------------- |
| `heroes.json` | `spellcasters.json` | Renamed only.                                                  |
| `units.json`  | `units.json`        | Contains **Creatures** and **Buildings** (The "Unit" subtype). |
| `units.json`  | `spells.json`       | Contains **Spells** (Extracted).                               |
| `units.json`  | `titans.json`       | Contains **Titans** (Extracted).                               |
| _(None)_      | `consumables.json`  | New file for Consumables (Loot).                               |
| _(None)_      | `upgrades.json`     | New file for Upgrades (RNG Rewards).                           |
| _(None)_      | `game_info.json`    | Global Game Constants & Mechanics.                             |

### Schemas (`schemas/v1/`)

| Legacy File        | Current File              | Changes                                                                  |
| :----------------- | :------------------------ | :----------------------------------------------------------------------- |
| `hero.schema.json` | `spellcaster.schema.json` | Title: `Spellcaster`.                                                    |
| `unit.schema.json` | `incantation.schema.json` | **Base Polmorphic Schema**. Validates ALL Incantations (Units + Spells). |
| _(None)_           | `titan.schema.json`       | Strict schema for Titans.                                                |
| _(None)_           | `consumable.schema.json`  | Schema for Consumables.                                                  |
| _(None)_           | `upgrade.schema.json`     | Schema for Upgrades.                                                     |
| _(None)_           | `game_info.schema.json`   | Schema for Game Info.                                                    |

### Deprecated / Removed Fields

| Field           | Status      | Replacement                                  |
| :-------------- | :---------- | :------------------------------------------- |
| `game_version`  | **Removed** | Use `changelog` array (first entry) instead. |
| `author`        | **Removed** | Git history handles attribution.             |
| `hero_id`       | **Renamed** | Use `spellcaster_id`.                        |
| `consumable_id` | **Renamed** | Use `entity_id`.                             |

### Asset Folder Structure

| Old Path        | New Path              | Content                         |
| :-------------- | :-------------------- | :------------------------------ |
| `assets/heroes` | `assets/spellcasters` | Spellcaster portraits/images.   |
| `assets/units`  | `assets/units`        | Creature & Building cards.      |
| `assets/units`  | `assets/spells`       | Spell cards (Split from Units). |
| `assets/units`  | `assets/titans`       | Titan cards (Split from Units). |

---

## 3. Data Hierarchy & Types

### **A. Spellcaster** (`spellcaster.schema.json`)

Root Object.

- **Type Identifier**: File location (`spellcasters.json`).

### **B. Incantation** (`incantation.schema.json`)

> **Purpose**: This is the **BASE SCHEMA** for all items that can be placed in a standard Deck Slot (1-4).
> It defines the common "Card" properties (`cost_population`, `cost_charges`, `rank`, `magic_school`) and the `changelog` array.

It supports polymorphism via the `category` field:

#### **Sub-Type: Unit** (in `units.json`)

- **Applies to**: `category: "Creature"` | `category: "Building"`
- **Validation**:
  - Must have **Health** (`health > 0`).
  - Must have **Collision** (`collision_radius`).
  - Represents a physical object on the board.

#### **Sub-Type: Spell** (in `spells.json`)

- **Applies to**: `category: "Spell"`
- **Validation**:
  - `health` usually 0 or ignored.
  - Represents an action or effect.

### **C. Titan** (`titans.json`)

- **Category Values**: `"Titan"`.
- **Validation**: `titan.schema.json`.

### **D. Consumable** (`consumables.json`)

- **Category Values**: `"Consumable"`.
- **Validation**: `consumable.schema.json`.

### **E. Upgrade** (`upgrades.json`)

- **Purpose**: RNG Level-up bonuses.
- **Validation**: `upgrade.schema.json`.
- **Key Fields**: `target_tags` (Defines applicability), `effect` (Stats modifier).

### **F. Game Info** (`game_info.json`)

- **Purpose**: Global constants and mechanics implementation details.
- **Validation**: `game_info.schema.json`.

---

## 4. Implementation Checklist for Tool Devs

1.  **Update Load Paths**:
    - Load `spellcasters.json` instead of `heroes.json`.
    - Load `units.json` (Creatures + Buildings).
    - Load `spells.json` (Spells).
    - Load `titans.json` (Titans).
2.  **Update Type Definitions**:
    - `Incantation` interface (Common Base).
    - `Unit` (extends Incantation) -> Has Health/Collision.
    - `Spell` (extends Incantation) -> Has Radius/Duration.
    - `Titan` (Standalone).
3.  **Schema Validation**:
    - All items in `units.json` AND `spells.json` must validate against `incantation.schema.json`.
4.  **Feature Support**:
    - Support the new `changelog` field (view/edit history).
    - **Note**: `game_version` field is removed. Parsers should use `changelog[0].version` for display if needed.
