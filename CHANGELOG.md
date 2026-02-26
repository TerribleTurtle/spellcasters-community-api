# Changelog

All notable changes to this project will be documented in this file.

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
