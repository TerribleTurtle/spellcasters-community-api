# Project Status

## In Progress

| Feature | Phase | Started | Notes |
|---------|-------|---------|-------|
| _(none)_ | | | |

## Completed

| Feature | Date | Summary |
|---------|------|---------|
| v0.2.0 March Patch Update | 2026-03-07 | Balance edits (5 entities), knowledge cost adjustments (24 files), summon_xp + map_objects schema additions, version bump |
| Core Schema v2 | 2026-02 | Draft 2019-09 schemas with strict mode, 17 top-level schemas, 7 entity types |
| CI/CD Pipeline | 2026-02 | GitHub Actions for lint/test/build/deploy to GitHub Pages |
| Entity Data Population | 2026-02 | 6 heroes, 24 units, 18 spells, 2 titans, 10 consumables, 3 upgrades, 2 map_chests |
| Patch System | 2026-02 | Auto-generated patch history via git diff → patches.json |

## Active Decisions & Learnings

- `unevaluatedProperties: false` enforced on all entity schemas — any new field MUST be added to schema first
- Multiplier convention: `1.0` = 100% base (not percentage points)
- Unknown values use sentinel `-1.0` with `(UNKNOWN)` in description text
- `last_modified` must be updated on every entity data change
- Schema changes adding required fields need `build_api.py` rebuild before `test_standalone_endpoints` will pass

## Known Blockers

| Blocker | Impact | Date Logged |
|---------|--------|-------------|
| Upgrade data stubs (empty `incantation_upgrades`) | Can't track upgrade effect changes | 2026-03-07 |
| Level threshold data (only levels 1 and 25 known) | Can't track XP curve changes | 2026-03-07 |

## Feature Worktrees

_None active._
