# Project Status: Active

## Current Focus

Ready for API usage and Content Expansion.

## Completed Tasks

- [x] Create Implementation Plan
- [x] Consolidate Documentation into `GUIDE.md`
- [x] Initialize Directory Structure
- [x] Create JSON Schemas (Creatures, Heroes, Spells, Items, Buildings, Titans, Upgrades)
- [x] Create Build Script (`build_api.py`) with aggregations
- [x] Setup GitHub Actions Workflow
- [ ] Populate missing JSON data (Partial: Creatures/Titans done)
  - [x] Creatures
  - [x] Titans
  - [ ] Heroes
  - [ ] Spells
  - [ ] Items
  - [ ] Buildings
  - [ ] Upgrades
- [ ] Populate Assets (Images)
  - [ ] Creatures
  - [ ] Titans
  - [ ] Heroes
  - [ ] Spells
  - [ ] Items
  - [ ] Buildings
  - [ ] Upgrades
- [x] **Project Audit & Cleanup:**
  - [x] Moved Titans to `data/titans`
  - [x] Updated all JSON data to match v1 schemas (added `date_modified`)
  - [x] Removed redundant documentation files
  - [x] Verified strict schema validation (installed `jsonschema`)
  - [x] **Community Standards:**
    - [x] Added `CONTRIBUTING.md` & `README.md` updates
    - [x] Enforced `version` field in all schemas
    - [x] Added `scripts/validate_integrity.py` for logical validation
    - [x] **Audit 2026-02-03:**
      - [x] Fixed script output buffering.
      - [x] Implemented "Opt-In" Asset Validation (`image_required` flag).
      - [x] Synced `GUIDE.md` and `CONTRIBUTING.md` with new standards.
- [x] **Mechanics Integration:**
  - [x] Added `deck.schema.json` (Starter Decks)
  - [x] Added `upgrade.schema.json` (Level-up options)
  - [x] Updated `hero.schema.json` (Population/Ranks)
  - [x] Created `data/mechanics/` for game logic placeholders
- [x] **Game Metadata:**
  - [x] Created `game_info.schema.json` & `data/game_info.json`
  - [x] Documented Developer (Quantic Dream), Publisher (Quantic Dream), and F2P model.
- [x] **Script Audit:**
  - [x] Verified `build_api.py` functionality.
  - [x] Enhanced `validate_integrity.py` to check `Titans` and `Decks` references.
  - [x] Created `data/decks` directory.

## Logic & Constraints

- **Game Info:** Single "Manifest" file at `api/v1/game_info.json`.
- **Decks:** Starter/Meta decks only. 5 Slots (Hero, Titan, 4 Cards).
- **Health:** No upper limit.
- **Flexibility:** `meta` field allows any key-value pairs.
- **Versioning:** Output is generated in `api/v1/`.
- **Items:** Strict separation between `consumable` (Inv) and `instant_xp` (Orb).
- **Assets:** Images hosted in `assets/`. Max size 1MB. Total repo size monitoring required. URL convention: `.../assets/[category]/[id].png`.
