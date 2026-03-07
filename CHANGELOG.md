# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-03-07

### Balance Updates (March 2026 Patch)

- feat(data): Harpy HP 100→80, Building/Lifestone damage modifier 0.65→0.85
- feat(data): Rhino Rider HP 0→550
- feat(data): Astral Shot damage 32→28
- feat(data): Swamp Witch Poison Strike damage 21→15, +0.88x vs Spellcasters
- feat(data): Spawner XP multiplier 0.5→0.1
- feat(data): Building spawner count 5→3, death spawn 10→6, max active 15→12
- feat(data): knowledge cost adjustments across 24 units and spells
- feat(data): Early Access compensation: 2,000 Knowledge for pre-March 2 players

### Schema Additions

- feat(schema): add `summon_xp` to `match_xp` in `game_systems.schema.json` (required)
- feat(schema): add `map_objects` with `lifestone` to `game_systems.schema.json` (optional)
- feat(schema): add `early_access_compensation` to `starting_knowledge` (required)
- feat(schema): add `max_active` to `spawner.schema.json` (optional)
- feat(data): populate `summon_xp` per-rank values (50/150/300/500)
- feat(data): populate `map_objects.lifestone` (10 HP/s heal to Spellcasters in territory)

## [0.1.2] - 2026-02-26

- feat(schema): rework `upgrades.schema.json` from RNG placeholder to archetype-based fixed upgrades
- feat(schema): create `game_systems.schema.json` (progression, ranked, match XP)
- feat(schema): add `Cast_Stone` to `consumable_effect_enum`, add `grants_incantation` and `drop_time_seconds` to consumables
- feat(schema): add `game_systems` ref to `all_data.schema.json`
- feat(data): add archetype upgrade tables (conqueror, duelist, enchanter)
- feat(data): add `game_systems.json` with progression economy, ranked mode, and match XP values
- feat(data): add Cast Stone consumables (`cast_stone_fire_ball`, `cast_stone_heal_ray`)
- feat(pipeline): register `game_systems` in `config.py` and `build_api.py`
- feat(ui): add Game Systems endpoint card to `index.html`
- chore: delete old `data/upgrades/placeholder.json`

## [0.1.0] - 2026-02-26

- feat(schema): add `knowledge_cost` field to `unlockable` definition in `core.schema.json`
- feat(schema): wire `unlockable` into `spells.schema.json` and `units.schema.json` via `allOf`
- feat(data): add `knowledge_cost` to all 35 existing spell and unit data files
- feat(data): add 7 new entities — Rhino Rider, Siren, Rocket Soldier Factory, Ice Ray, Poison Breath, Metamorphosis, Holy Arrow
- feat(assets): add Knowledge and Eldergold currency icons (PNG + WebP) in `assets/currencies/`
- feat(assets): add placeholder images for 7 new entities (PNG + WebP)
- feat(assets): replace placeholder WebP images with real art for Rhino Rider, Siren, Rocket Soldier Factory, Ice Ray, Poison Breath, Metamorphosis, Holy Arrow
- chore: bump game version to `0.1.0`

## [1.0.1] - 2026-02-26

- feat: improve version parsing robustness in release script and add comprehensive tests for API build processes including XSS sanitization.
- docs(meta): fix drift & document node toolchain
- feat(api): inject image_urls into heroes API response
- fix(deps): patch basic-ftp path traversal vulnerability (CVE)
- feat(assets): organize spellcaster ability images into heroes/abilities with standardized naming and WebP conversion
- chore: documentation health remediation, test linting fixes, and deploy preparation

## [0.0.1] - 2026-02-23

Initial Database Alpha baseline.
