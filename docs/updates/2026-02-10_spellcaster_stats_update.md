# Spellcaster Stats Update (2026-02-10)

This document outlines the schema changes and data updates applied to Spellcaster primary attacks.

## 1. Schema Changes

### `spellcaster.schema.json`

- **[NEW] `projectiles`**: Added to `ability_detail.stats`.
  - Type: `integer` (nullable)
  - Description: Number of projectiles per attack. Used for multi-hit attacks where damage is split (e.g., "21x2").

## 2. Data Updates (Primary Attacks)

All primary attacks now have explicit `damage` stats and defined `mechanics`.

| Spellcaster           | Attack           | Damage | Projectiles | Mechanics / Notes                                     |
| :-------------------- | :--------------- | :----- | :---------- | :---------------------------------------------------- |
| **Iron Sorcerer**     | _Twin Strike_    | **35** | -           | **Cleave** (Arc damage)                               |
| **Swamp Witch**       | _Poison Strike_  | **21** | **2**       | **Homing** (Seek targets)                             |
| **Fire Elementalist** | _Flame Strikes_  | **28** | -           | **Cleave** (Arc damage)                               |
| **Astral Monk**       | _Astral Fists_   | **32** | -           | **Combo Sequence**: Alternates 32 (Palm) / 47 (Punch) |
| **Mystic Scribe**     | _Brush Strike_   | **23** | -           | **Cleave**, **Knockback** (Small units)               |
| **Stone Shaman**      | _Mountain Staff_ | **42** | -           | **Cleave**, **Interruption** (2 hits)                 |

_Note: `interval` is currently set to `null` for all spellcasters pending further data._
