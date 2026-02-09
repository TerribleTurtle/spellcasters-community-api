# Developer Update Guide: Schema v1.1 & Data Standardization

## Summary

We are deploying a schema update to support complex unit mechanics (Auras, Spawners, Conditional Damage Modifiers) and standardizing how percentage buffs are stored.

## Key Changes

### 1. Data Standardization: Multipliers

**Goal**: Remove ambiguity between "Increased By" vs "Total Value".
**New Standard**: All percentage-based modifiers are stored as **Multipliers**.

- **1.0** = 100% (No Change / Base Damage)
- **1.5** = 150% (50% Increased Damage)
- **0.5** = 50% (50% Reduced Damage)
- **2.6** = 260% (160% Increased Damage)

### 2. Schema: `mechanics` Object

We have moved away from flattening unique abilities into the root object. All complex logic now lives in the `mechanics` object.

#### Supported Mechanics

- **`aura`**:
  - `radius`: Number (Distance)
  - `value`: Number (Amount per tick)
  - `interval`: Number (Seconds)
  - `target_type`: "Ally", "Enemy", "All"
- **`damage_modifiers`**:
  - `target_type`: "Building", "Creature", "Spellcaster"
  - `multiplier`: Number (e.g., `1.5` for +50% dmg)
- **`spawner`**:
  - `unit_id`: String (Entity ID to spawn)
  - `count`: Integer
  - `trigger`: "Death", "Interval"

### 3. Client Impact

- Frontend must update `UnitCard` and `SpellDetail` components to parse `mechanics` arrays.
- Damage calculation logic should simply multiply `base_damage * mechanics.damage_modifiers.multiplier` when conditions are met.
