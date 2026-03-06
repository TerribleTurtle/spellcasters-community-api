# AGENTS.md — Spellcasters Community API

> **Purpose:** Give any AI coding agent immediate, actionable context for this repo.
> Generated: 2026-03-01.

---

## 1. Project Identity

| Field           | Value                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------- |
| **Name**        | Spellcasters Community API                                                                          |
| **Repo**        | `TerribleTurtle/spellcasters-community-api`                                                         |
| **Purpose**     | Free, open-source static JSON API for the game *Spellcasters Chronicles*                            |
| **Architecture**| Static-site data API — Python scripts build/validate JSON, GitHub Pages serves `api/v2/`            |
| **License**     | MIT (code). Game assets © Quantic Dream (fan content).                                              |
| **Live URL**    | `https://terribleturtle.github.io/spellcasters-community-api/api/v2/`                              |
| **Consumers**   | SpellcastersDB (web), Spellcasters Bot (Discord), The Grimoire (manager tool)                       |

---

## 2. Stack

| Layer              | Technology                                                                                |
| ------------------ | ----------------------------------------------------------------------------------------- |
| **Language**       | Python 3.11+                                                                              |
| **Schema**         | JSON Schema Draft 2019-09 (`schemas/v2/`)                                                 |
| **Linter/Fmt**     | Ruff (check + format) via `pyproject.toml`                                                |
| **Tests**          | pytest (`tests/`, 24 test files)                                                          |
| **Type Checking**  | mypy                                                                                      |
| **Pre-commit**     | Ruff hooks (`ruff check --fix` + `ruff format`)                                           |
| **CI/CD**          | GitHub Actions (`ci.yml` — lint/test/build, `deploy.yml` — build + deploy to GitHub Pages)|
| **Hosting**        | GitHub Pages (static). CORS `*` by default.                                               |
| **Node.js (minor)**| `ajv` + `ajv-formats` + `@apidevtools/json-schema-ref-parser` — browser schema validator  |
| **Env**            | direnv (`.envrc`), optional `.env` / `.env.local`                                         |

---

## 3. Directory Structure

```
.
├── data/                    # Source JSON — one file per entity (edits happen HERE)
│   ├── heroes/              #   Hero JSON files
│   ├── units/               #   Unit JSON files
│   ├── spells/              #   Spell JSON files
│   ├── titans/              #   Titan JSON files
│   ├── consumables/         #   Consumable JSON files
│   ├── upgrades/            #   Upgrade JSON files
│   ├── map_chests/          #   Map Chest JSON files
│   ├── game_config.json     #   Game version & metadata (source of truth)
│   ├── game_systems.json    #   Game systems config
│   ├── infusions.json       #   Elemental infusion definitions
│   ├── patches.json         #   Patch history (internal, CI-managed)
│   └── queue.json           #   Patch queue (internal, CI-managed)
├── schemas/v2/              # JSON Schemas (Draft 2019-09)
│   ├── definitions/         #   Shared definitions (core, stats, enums, magic, etc.)
│   │   └── mechanics/       #     Mechanic sub-schemas (aura, spawner, etc.)
│   └── *.schema.json        #   17 top-level schemas
├── assets/                  # Game images (heroes/, units/, spells/, titans/, currencies/)
├── scripts/                 # Python build & validation tools (15 scripts)
│   ├── config.py            #   Shared paths, constants, schema mappings
│   ├── validate_integrity.py#   Primary validator (schema + referential + asset checks)
│   ├── verify_strictness.py #   Schema strictness verification
│   ├── build_api.py         #   Aggregates data/ → api/v2/
│   ├── build_audit_log.py   #   Git-based audit log
│   ├── build_changelogs.py  #   Patch history → changelog files
│   ├── generate_patch.py    #   Git diff → patches.json
│   ├── audit_v2.py          #   Deep audit tooling
│   ├── release.py           #   Version bump & changelog CLI
│   ├── patch_utils.py       #   Patch utility functions
│   ├── timeline_utils.py    #   Timeline/stat-diff utilities
│   ├── validate_schemas.py  #   Lightweight schema-only validation
│   ├── check.sh             #   Local CI runner (bash)
│   └── check.ps1            #   Local CI runner (PowerShell)
├── tests/                   # pytest suite (24 files)
├── docs/                    # Guides (extensibility, security, history)
├── types/                   # TypeScript definitions (patch-history.d.ts)
├── api/                     # Generated output (gitignored — DO NOT edit)
├── timeline/                # Generated timeline snapshots (gitignored)
├── .github/workflows/       # CI (ci.yml) + Deploy (deploy.yml)
├── Entity_Builder           # SDD for planned Entity Builder tool (not yet implemented)
├── index.html               # Landing page (GitHub Pages)
├── schema-validator.html    # Browser-based schema validator
├── schema-validator.js      # Validator frontend logic
├── ajv2019.bundle.js        # Vendored AJV bundle for browser
├── style.css                # Shared dark-theme stylesheet
├── pyproject.toml           # Ruff + pytest config
├── requirements.txt         # Python dependencies
└── package.json             # Node.js deps (AJV tooling only)
```

---

## 4. Entity Architecture

The API is built from **7 entity types**, each with its own schema, data directory, and asset directory:

| Entity         | Data Path               | Schema                             | Assets               | Has Image |
| -------------- | ----------------------- | ---------------------------------- | --------------------- | --------- |
| **Heroes**     | `data/heroes/*.json`    | `schemas/v2/heroes.schema.json`    | `assets/heroes/`      | ✅        |
| **Units**      | `data/units/*.json`     | `schemas/v2/units.schema.json`     | `assets/units/`       | ✅        |
| **Spells**     | `data/spells/*.json`    | `schemas/v2/spells.schema.json`    | `assets/spells/`      | ✅        |
| **Titans**     | `data/titans/*.json`    | `schemas/v2/titans.schema.json`    | `assets/titans/`      | ✅        |
| **Consumables**| `data/consumables/*.json`| `schemas/v2/consumables.schema.json`| —                     | ❌        |
| **Upgrades**   | `data/upgrades/*.json`  | `schemas/v2/upgrades.schema.json`  | —                     | ❌        |
| **Map Chests** | `data/map_chests/*.json`| `schemas/v2/map_chests.schema.json`| `assets/maps/`        | ✅        |

**Standalone data files** (not per-entity):
- `data/game_config.json` → `game_config.schema.json`
- `data/game_systems.json` → `game_systems.schema.json`
- `data/infusions.json` → `infusions.schema.json`

**Schema design:**
- Draft 2019-09 with `unevaluatedProperties: false` (strict mode)
- Deep `$ref` hierarchy: entity → `definitions/core.schema.json`, `stats.schema.json`, `enums.schema.json`, `mechanics.schema.json` → `mechanics/*.schema.json`
- `allOf` composition for inheritance. `if/then/else` for conditionals (e.g., Buildings).
- `oneOf` for polymorphic fields (e.g., cleave: boolean or object).

---

## 5. Conventions

### File Naming
- **Entity data:** `data/{plural_type}/{entity_id}.json` — `entity_id` is `snake_case` (`^[a-z0-9_]+$`)
- **Schemas:** `schemas/v2/{plural_type}.schema.json`
- **Assets:** `assets/{type}/{entity_id}.webp` — max 512×512px, max 100 KB
- **Scripts:** `scripts/{verb}_{noun}.py` (e.g., `validate_integrity.py`, `build_api.py`)
- **Tests:** `tests/test_{module}.py` — mirrors script names

### Python
- Ruff config: `line-length = 120`, target `py311`
- Linting rules: `E`, `W`, `F`, `I`, `B`, `UP` (ignores `E501`)
- Format: double quotes, space indentation
- Imports sorted by isort (via Ruff `I` rule)
- Shared config in `scripts/config.py` — all paths, schema mappings, constants defined there

### JSON Data
- `last_modified`: ISO 8601 UTC timestamp, required on every entity
- `image_required`: Defaults to `true` for entities with assets
- Unknown values: Use sentinel `-1.0` with `(UNKNOWN)` in condition text
- Multipliers: `1.0` = 100% base (not percentage points)
- No manual editing of `api/`, `timeline/`, `changelog*.json` — these are build artifacts

---

## 6. Commands

### Install
```bash
pip install -r requirements.txt
```

### Lint & Format
```bash
python -m ruff check scripts/ tests/           # Check
python -m ruff check --fix scripts/ tests/      # Auto-fix
python -m ruff format scripts/ tests/           # Format
python -m ruff format --check scripts/ tests/   # Format (check only)
```

### Test
```bash
python -m pytest                                # All tests
python -m pytest -v                             # Verbose
python -m pytest tests/test_schemas.py          # Single module
python -m pytest -k "test_name"                 # By name
```

### Validate
```bash
python scripts/validate_integrity.py            # Full validation (schema + referential + assets)
python scripts/verify_strictness.py             # Schema strictness checks
python scripts/validate_schemas.py              # Lightweight schema-only check
```

### Build
```bash
python scripts/build_audit_log.py               # Generate audit.json
python scripts/build_changelogs.py              # Generate changelog files
python scripts/build_api.py                     # Aggregate data/ → api/v2/
```

### Full Local CI
```bash
# Linux/macOS
bash scripts/check.sh

# Windows (PowerShell)
.\scripts\check.ps1
```
Runs: Ruff Check → Ruff Format → pytest → validate_integrity → verify_strictness

### Node.js (only for browser schema validator changes)
```bash
npm install
npx browserify build_ajv.js -o ajv2019.bundle.js
```

---

## 7. CI/CD Pipeline

### `ci.yml` — Pull Requests & Non-main Branches
1. **Lint & Format** — Ruff check + format (auto-commits fixes on PRs)
2. **Unit Tests** — `python -m pytest`
3. **Build & Validate** (requires lint + test) — `validate_integrity.py` → `verify_strictness.py` → `build_audit_log.py` → `build_changelogs.py` → `build_api.py`

### `deploy.yml` — Main Branch (GitHub Pages)
1. **Lint** — Ruff check + format (no auto-commit)
2. **Unit Tests** — `python -m pytest`
3. **Build** (requires lint + test) — validate → strictness → `generate_patch.py` → audit → changelogs → `build_api.py` → assemble `public/` → upload artifact → deploy to GitHub Pages

---

## 8. Adding a New Entity Type

Follow this exact sequence (the build system enforces it):

1. **Schema first:** Create `schemas/v2/{plural}.schema.json` using `$ref` to `definitions/`
2. **Register in `scripts/config.py`:**
   - Add entry to `SCHEMA_FILES` dict (schema key → filename)
   - Add entry to `FOLDER_TO_SCHEMA` dict (folder name → schema key)
3. **Create data directory:** `data/{plural}/` with at least one `.json` file
4. **Create asset directory** (if `image_required`): `assets/{plural}/`
5. **Update `scripts/build_api.py`** to aggregate the new entity type
6. **Update `scripts/validate_integrity.py`** for any referential integrity rules
7. **Add tests:** Create `tests/test_{entity}.py`
8. **Verify:** Run `python scripts/validate_integrity.py` + `python -m pytest`

See `docs/EXTENSIBILITY_GUIDE.md` for full details on schema strictness philosophy.

---

## 9. Recommended Build Order

When developing new features, follow this dependency order:

1. **Schema Definitions** — Define all new schemas and `$ref` compositions first. The entire build pipeline validates against schemas, so nothing works without them.
2. **Config Registration** — Update `scripts/config.py` with schema and folder mappings. All scripts read from this central config.
3. **Data Files** — Create entity JSON files that conform to the new schemas.
4. **Validation Scripts** — Update `validate_integrity.py` with any new referential integrity rules.
5. **Build Scripts** — Update `build_api.py` to include the new entity type in API output.
6. **Tests** — Write tests covering schema validation, integrity checks, and build output.

> **Parallelizable after step 3:** Once schemas, config, and data exist, validation updates, build updates, and test writing can happen in parallel across separate git worktrees.

---

## 10. Key Files to Read First

| File                          | Why                                                         |
| ----------------------------- | ----------------------------------------------------------- |
| `scripts/config.py`           | Central registry of all paths, schema mappings, and constants|
| `scripts/validate_integrity.py`| Primary validation — schema + referential + asset checks    |
| `schemas/v2/definitions/core.schema.json` | Shared identity, meta, asset definitions     |
| `schemas/v2/definitions/enums.schema.json`| All enum values (category, class, rank, etc.) |
| `CONTRIBUTING.md`             | Data standards, multiplier conventions, entity hierarchy     |
| `docs/EXTENSIBILITY_GUIDE.md` | How schema strictness works, how to add/change fields       |

---

## 11. Safety Rails

### ❌ Forbidden Actions
- **Never edit files in `api/`** — these are generated by `build_api.py`
- **Never edit `changelog*.json` or `timeline/`** — generated by CI pipeline
- **Never modify `data/patches.json` or `data/queue.json` manually** — managed by `generate_patch.py`
- **Never add a field to a data file without updating its schema first** — build will reject it (`unevaluatedProperties: false`)
- **Never delete a data file that is referenced by another entity** — referential integrity checks will fail
- **Never run `rm -rf` outside of `api/`, `timeline/`, or `__pycache__/`**
- **Never install packages globally** — use `pip install -r requirements.txt` in a venv
- **Never modify `.env` or `.envrc`** in a PR

### 🔁 Error Recovery
1. If build fails: run `python scripts/validate_integrity.py` for diagnostics
2. If schema validation fails: check `schemas/v2/` for `unevaluatedProperties` violations
3. If referential integrity fails: check cross-entity references (upgrade targets, hero abilities)
4. **Stop after 3 consecutive failures** on the same issue — ask the user

### ✅ Pre-commit Checklist
1. `python -m ruff check scripts/ tests/` passes
2. `python -m ruff format --check scripts/ tests/` passes
3. `python -m pytest` passes
4. `python scripts/validate_integrity.py` passes
5. `python scripts/verify_strictness.py` passes
