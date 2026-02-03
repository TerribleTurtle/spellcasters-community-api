# Spellcasters Community API Guide

**The Definitive Guide to the Spellcasters Chronicles Static API.**

---

## 1. Project Overview

**Goal:** Create a robust, serverless, and versioned database for _Spellcasters Chronicles_ data (Creatures, Spells, Heroes, Buildings).
**Architecture:** GitHub Repository -> Python Build Script -> Validated JSON API (hosted on GitHub Pages).

This project serves as the "Source of Truth" for all external tools, wikis, and community projects.

---

## 2. Directory Structure

The project follows a "Parallel Structure" to separate raw source data from assets and build logic.

```
spellcasters-community-api/
├── assets/                 # Images and Icons
│   ├── creatures/          # e.g., orc_grunt.png
│   ├── titans/             # e.g., gaia_beast.png
│   ├── spells/
│   ├── heroes/
│   ├── buildings/
│   ├── items/
│   └── upgrades/
├── data/                   # Raw JSON Data Sources
│   ├── creatures/          # e.g., orc_grunt.json
│   ├── titans/             # e.g., gaia_beast.json
│   ├── heroes/
│   ├── spells/
│   ├── items/
│   ├── buildings/
│   ├── decks/              # Starter Decks / Meta Builds
│   ├── upgrades/           # Level-up options
│   └── mechanics/          # Game Logic (Curves, Settings)
├── schemas/                # Validation Logic
│   └── v1/                 # Versioned JSON Schemas
│       ├── creature.schema.json
│       ├── deck.schema.json
│       ├── upgrade.schema.json
│       └── ...
├── scripts/                # Build Tools
│   └── build_api.py        # The Compiler Script
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/          # Automation (CI/CD)
├── .gitignore
```

---

## 3. Data Protocols & Schema

### Core Principles

1.  **Flexible Metadata:** Future-proof data using the `meta` object. This allows adding arbitrary key-value pairs (e.g., specific flags, patch notes, internal IDs) without breaking the core schema.
2.  **Versioning:** All API output is versioned (e.g., `api/v1/`).

### Standard "Creature" JSON Template

File: `data/creatures/unit_id.json`

```json
{
  "id": "orc_grunt",
  "image_required": true,
  "name": "Orc Grunt",
  "type": "Infantry",
  "rank": 1,
  "description": "Standard infantry unit.",
  "date_modified": "2024-01-01T12:00:00Z",
  "stats": {
    "health": 200,
    "dps": 10,
    "speed": 4,
    "hps": 0,
    "range": 0, // 0 or "Melee" if verified by logic
    "cost": 50 // Optional
  },
  "tags": ["Grunt"],
  "meta": {
    "version_added": "Closed Beta 1"
  }
}
```

### Flexibility via `meta`

The `meta` field is designed to be unstructured. You can add any valid JSON key-pair here.

- _Good:_ `"meta": { "seasonal_event": "Winter 2024" }`
- _Bad:_ Adding root-level fields like `"seasonal_event": "Winter 2024"` (This breaks strict schema validation).

---

## 4. Setup & Building

### Prerequisites

- Python 3.9+

### Build Script

The build script (`scripts/build_api.py`) addresses three tasks:

1.  **Validation:** Checks all `data/` files against `schemas/`.
2.  **Integrity Check:** `scripts/validate_integrity.py` ensures all references (e.g. drops, abilities) exist.
3.  **Aggregation:** Combines individual files into huge `all_*.json` lists.
4.  **Deploy Prep:** outputs to `api/v1/`.

**Run the build:**

```bash
pip install -r requirements.txt
python scripts/validate_integrity.py
python scripts/build_api.py
```

---

## 5. Contributing

1.  **Add Data:** Create a new `.json` file in the appropriate `data/` subfolder.
2.  **Add Images:** Place a `.png` file in `assets/` with the **exact same filename** as the JSON ID.
    - Example: `data/creatures/orc_grunt.json` -> `assets/creatures/orc_grunt.png`
3.  **Verify:** Run the python script to ensure no schema errors. A [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) will guide you through the submission process.
4.  **Push:** Commit changes. GitHub Actions will automatically deploy to the API endpoint.

### 5.1 Image Hosting Guidelines

We use a **Git-Native** hosting strategy for robustness and simplicity.

- **Location:** `assets/[category]/[id].png`
- **Size Limit:** Must be < 1MB per image.
- **Total Limit:** We aim to keep the repo under 1GB.
- **Format:** `.png` preferred.
- **Access:** Images are fetched directly via the GitHub Pages URL.
  - Example: `https://terribleturtle.github.io/spellcasters-community-api/assets/creatures/orc_grunt.png`
  - **Validation:** `scripts/validate_integrity.py` checks for these images.
    - **Note:** Missing images are only flagged if `"image_required": true` is set in the JSON file. If omitted (default `false`), no warning is issued.

### 5.2 Optional Drops

- **Creatures:** The `drops` field is optional.
  - **Neutral Creeps:** Should have drops defined.
  - **Player Summons:** Should NOT have drops defined.

---

## 6. Accessing the API

Base URL: `https://terribleturtle.github.io/spellcasters-community-api/api/v1/`

- **Creatures:** `.../all_creatures.json`
- **Spells:** `.../all_spells.json`
- **Heroes:** `.../all_heroes.json`
- **Decks:** `.../all_decks.json`
- **Upgrades:** `.../all_upgrades.json`
- **Game Info:** `.../game_info.json` (Singleton)
