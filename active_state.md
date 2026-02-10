# Project Status: Active

## Current Focus

Validating Migrated Data & Populating Missing Content (Consumables, Upgrades).
Validating Migrated Data & Populating Missing Content (Consumables, Upgrades).
**Asset Management:** Manual (PNGs/WebPs managed by external tools).

## TODO

- [ ] Standardize Naming: `FOLDER_TO_SCHEMA` (plural) vs `SCHEMA_FILES` (singular).

## Completed Tasks

- [x] **Foundation:**
  - [x] Initialized Directory Structure & Git Config.
  - [x] Created `GUIDE.md`, `CONTRIBUTING.md`, `README.md`.
  - [x] Setup GitHub Actions (`deploy.yml`, `validate.yml`).
- [x] **Schema Architecture (v1.2 - 2026-02-03):**
  - [x] **Consolidated Architecture:** `unit` (Entities), `card` (Deck Data), `hero`, `consumable` (Loot), `upgrade` (RNG).
  - [x] **Fields:** Enforced `game_version`, `image_required` (default: true).
  - [x] **Deleted:** Deprecated noun-based schemas (`creature`, `building`, etc.).
- [x] **Data Migration:**
  - [x] Migrated all legacy `creatures`/`buildings`/`titans` to `data/units` + `data/cards`.
  - [x] Refactored `heroes` to new schema.
  - [x] **Note:** Unit stats updated to "Accuracy Pass 1" (gaia_beast, thanatos, etc.).
- [x] **Tooling:**
  - [x] **Validation:** `scripts/validate_integrity.py` (Checks Schemas, References, Assets).
  - [x] **Build:** `scripts/build_api.py` (Aggregates new structure).
  - [x] **Checkpoints:** Added `verify.bat` for local testing.
- [x] **Documentation:**
  - [x] Updated `index.html` with correct API endpoints.
  - [x] **UI/UX:** Relocated Discord link to footer in `index.html` to clarify affiliation.
  - [x] Updated `requirements.txt` (`jsonschema`).
- [x] **Git Sync (2026-02-04):**
  - [x] Consolidated Schemas & Data Migration pushed to `origin/main`.
  - [x] Created Entity Stubs for Steam Tank, Ballista, Rampart, Astral Tower, and Crypt.
- [x] **Hero Class System (2026-02-05):**
  - [x] Added required `class` field to `hero.schema.json` with enum: Conqueror, Duelist, Enchanter.
  - [x] Updated all 6 hero files with intrinsic class assignments based on passive abilities.
- [x] **Git Sync (2026-02-06):**
  - [x] Synchronized local changes with remote after push rejection.
  - [x] Resolved conflicts in `data/decks/test_*.json`.
  - [x] Successfully pushed to `origin/main`.
- [x] **Bug Fix (2026-02-06):**
  - [x] Fixed `TypeError` in `scripts/validate_integrity.py` where `validate_decks` returned `None` when no deck files were present.
  - [x] Corrected indentation of return statement in `validate_decks`.
- [x] **API Generation (2026-02-08):**
  - [x] Generated `api/v1/all_data.json` and individual collection files using `scripts/build_api.py`.
- [x] **Data Import (2026-02-08):**
  - [x] Created `scripts/import_units.py` to extract unit data from external source.
  - [x] Generated `data/imported_units.json` (37 units).
  - [x] Cleaned up `scripts/import_units.py` and dependencies.
- [x] **Data Merge (2026-02-08):**
  - [x] Updated `unit.schema.json`: Added `rank`, nested `stats`, removed deprecated.
  - [x] Created `scripts/merge_imported_data.py`.
  - [x] Migrated all 37 units to new schema.
  - [x] Deleted deprecated `fireball.json` (replaced by `fire_ball.json`).
  - [x] Updated `scripts/validate_integrity.py` and rebuilt API.
- [x] **Cleanup (2026-02-08):**
  - [x] Deleted deprecated scripts: `merge_imported_data.py`, `reorder_fields.js`.
  - [x] Verified and Updated `MIGRATION_SPEC.md` to reflect full v1 implementation status.
- [x] **Schema Refinement (2026-02-08):**
  - [x] Flatted `stats` object in `incantation.schema.json` and `titans.schema.json`.
  - [x] Migrated all data to root-level stats.
  - [x] Verified API output.
- [x] **Asset Archiving (2026-02-08):**
  - [x] Moved all `.png` files to `assets/_archive/`.
  - [x] Updated `scripts/validate_integrity.py` to support `.webp` (primary) and `.png` (fallback).
  - [x] Created `scripts/optimize_assets.py` to automate PNG -> WebP conversion & archiving.
  - [x] Updated `CONTRIBUTING.md` with new asset standards.
- [x] **DevOps (2026-02-08):**
  - [x] Restored `scripts/update_timestamps.py` with git status auto-detection.
  - [x] Updated `last_modified` timestamps for all data files.
  - [x] Verified `deploy.yml` workflow dependencies.
  - [x] Updated `deploy.yml` to auto-build and commit API endpoints on data change.
- [x] **Documentation Audit (2026-02-08):**
  - [x] Updated `CONTRIBUTING.md` with current schema & hierarchy details.
  - [x] Consolidated `GUIDE.md` into `CONTRIBUTING.md` and `README.md`.
  - [x] Deleted deprecated `GUIDE.md`.
  - [x] Clarified terminology (Spellcasters, Titans, Incantations) across docs.

- [x] **Documentation Audit & Cleanup (2026-02-10):**
  - [x] Moved `CONTRIBUTING.md` to `docs/`.
  - [x] Removed deprecated `assets/_archive` and `optimize_assets` references.
  - [x] Added `scripts/README.md` and docstrings to all Python scripts.
  - [x] Updated `README.md` with new links and SpellcastersDB shoutout.

- [x] **Refactor & Migration (2026-02-08):**
  - [x] Split `unit` schema into `spellcaster`, `titan`, `incantation`.
  - [x] Migrated Titans and Spells to dedicated data directories.
  - [x] Verified and pushed to `origin/main`.
- [x] **Schema Update (2026-02-08):**
  - [x] Added `movement_type` to `incantation.schema.json`.
  - [x] Added `mechanics` object to `incantation.schema.json` for complex spell effects.
  - [x] Updated `earthquake.json` with multi-wave damage and building bonus.
  - [x] Updated units to use `Flying` and `Hover` movement types.
  - [x] Expanded `spellcaster.schema.json` with `stats` and `mechanics` for abilities.
  - [x] Migrated Stone Shaman "Interruption" mechanic to primary ability.
  - [x] Pushed all schema changes and updated data to `origin/main`.
- [x] **Schema v1.1 (2026-02-09):**
  - [x] Updated `incantation`, `titan`, `spellcaster` schemas to support `mechanics` object (Aura, Spawner, Modifiers).
  - [x] Standardized percentage buffs as Multipliers in data.
  - [x] Migrated Unit, Spell, Titan, and Spellcaster data to v1.1 standards.
  - [x] Validated integrity.
- [x] **Schema v1.1 (Movement & Features - 2026-02-09):**
  - [x] Added `movement_type` to `spellcaster.schema.json`.
  - [x] Standardized `mechanics` to Object structure in `spellcaster.schema.json`.
  - [x] Added `features` array to `mechanics` in all schemas for named keywords.
  - [x] Restored "Interruption" to `stone_shaman.json` using `features`.
  - [x] Rebuilt API v1.
- [x] **Balance Update (2026-02-09):**
  - [x] Updated `spells`: Earthquake (Stagger, Building Dmg), Fire Rain (Creature Dmg).
  - [x] Updated `units`: Skeleton Warrior (Dmg, Capture), Rocket Soldier (Targeting), Lizard Archer (Building Dmg), Dryad (Tooltip).
  - [x] Updated `titans`: Gaia Beast (Auto-Capture), Thanatos (Retaliation).
  - [x] Verified build.

- [x] **Balance Update Part 2 (2026-02-09):**
  - [x] **Wyvern**: Range increased to 36.
  - [x] **Spellcasters**: Updated mechanics descriptions for Mystic Scribe, Astral Monk, Iron Sorcerer, Fire Elementalist, Swamp Witch.
  - [x] **Fire Ray**: Adjusted damage to 14/tick (5 waves).
  - [x] **Fire Ray**: Adjusted damage to 14/tick (5 waves).
  - [x] Verified and Built API.

- [x] **Code Cleanup & Modernization (2026-02-09):**
  - [x] **Phase 1 (Critical):** Centralized `load_json` in `config.py`, pruned dead code (`build_api.py`, `validate_integrity.py`), optimized `deploy.yml` (removed redundant build).
  - [x] **Phase 2 (Refactor):** Extracted `validate_entry_assets` in `validate_integrity.py`, standardized logging in `optimize_assets.py`.
  - [x] **Verification:** Verified build process and script integrity (Blast Radius Check).

- [x] **Security Hardening (2026-02-10):**
  - [x] **Supply Chain:** Pinned dependencies in `requirements.txt`.
  - [x] **Governance:** Added `docs/SECURITY.md` and configured Dependabot.
  - [x] **Hardening:** Implemented recursive XSS sanitization in `build_api.py`.
  - [x] **Verification:** Validated that legitimate content (quotes, >) is preserved while scripts are neutralized.
  - [x] **Dependency Fix (2026-02-10):**
    - [x] Downgraded `jsonschema` to v4.25.1 to resolve installation error (v4.26.0 unavailable).

- [x] **Performance Optimization (2026-02-10):**
  - [x] **Algorithmic:** Fixed O(N^2) loop in `validate_integrity.py` (Upgrade Tags).
  - [x] **I/O:** Implemented single-pass data loading and asset caching (`.asset_cache.json`).
  - [x] **Verification:** Confirmed O(N) scaling and cache hit speedup (~340ms -> ~304ms).

- [x] **Security Patch (2026-03-15):**
  - [x] **Dependency:** Upgraded `tj-actions/changed-files` to v46.0.1 to mitigate supply chain vulnerability.

## Logic & Constraints

- **Single Source of Truth:** `data/` folder JSON files.
- **Strict Schema:** All data MUST validate against `schemas/v1/*.schema.json`.
- **References:**
  - Cards MUST link to a valid `entity_id` in `units.json`.
  - Decks MUST link to valid Heroes and Cards.
  - Decks MUST contain at least one Rank I or Rank II CREATURE card.
- **Assets:**
  - Location: `assets/[category]/[id].png`.
  - Validation: Controlled by `image_required` boolean in schema.
  - Failure Policy: Missing assets generate **WARNINGS**, not Errors.
- **Game Rules (Data):**
  - **Damage:** Integer (True Damage).
  - **Cost:** Population + Charges (No Gold/Mana).
  - **Versioning:** `game_version` string required on all entities (Current: `0.0.1` - Dev).
