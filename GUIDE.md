# Spellcasters Community API Guide

**The Definitive Guide to the Spellcasters Chronicles Static API.**

---

## 1. Project Overview

**Goal:** Maintain a **Free & Open API** for _Spellcasters Chronicles_.

Think of this as the community's shared encyclopedia—open to everyone, owned by no one.

- **For Developers:** A standardized database to build apps, deck builders, and calculators.
- **For Community:** A reliable reference for wikis and spreadsheets.
- **For Everyone:** A place to contribute and ensure data accuracy.

---

## 2. Directory Structure

The project keeps raw data (JSON files) separate from images (Assets).

```
spellcasters-community-api/
├── assets/                 # Images and Icons
│   ├── units/              # e.g., orc_grunt.png
│   ├── cards/              # e.g., fireball.png
│   ├── heroes/
│   ├── consumables/
│   └── upgrades/
├── data/                   # Raw JSON Data Sources
│   ├── units/              # e.g., orc_grunt.json
│   ├── cards/              # e.g., fireball.json
│   ├── heroes/
│   ├── consumables/
│   ├── cards/              # Starter Decks / Meta Builds
│   ├── upgrades/           # Level-up options
│   └── mechanics/          # Game Logic (Curves, Settings)
├── schemas/                # Validation Logic
│   └── v1/                 # Versioned JSON Schemas
│       ├── unit.schema.json
│       ├── card.schema.json
│       ├── hero.schema.json
│       ├── consumable.schema.json
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

### Standard JSON Templates

#### 1. Unit (The Entity)

File: `data/units/orc_grunt.json`

```json
{
  "game_version": "0.0.1",
  "entity_id": "orc_grunt",
  "name": "Orc Grunt",
  "category": "Creature",
  "description": "Standard infantry unit.",
  "image_required": true,
  "health": 200,
  "damage": 10,
  "attack_speed": 1.5,
  "movement_speed": 4,
  "range": 0,
  "projectile_speed": null,
  "movement_type": "Ground",
  "tags": ["Grunt", "Melee"]
}
```

#### 2. Card (The Deck Item)

File: `data/cards/card_orc_grunt_I.json`

```json
{
  "game_version": "0.0.1",
  "card_id": "card_orc_grunt_I",
  "entity_id": "orc_grunt",
  "name": "Orc Grunt",
  "rank": "I",
  "cost_population": 1,
  "cost_charges": 1,
  "cast_time": 1.0,
  "image_required": true
}
```

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
    - Example: `data/units/orc_grunt.json` -> `assets/units/orc_grunt.png`
3.  **Verify:** Run the python script to ensure no schema errors. A [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) will guide you through the submission process.
4.  **Push:** Commit changes. GitHub Actions will automatically deploy to the API endpoint.

### 5.1 Image Hosting

We host images directly in the repository for simplicity.

- **Location:** `assets/[category]/[id].png`
- **Size Limit:** Must be < 1MB per image.
- **Total Limit:** We aim to keep the repo under 1GB.
- **Format:** `.png` preferred.
- **Access:** Images are fetched directly via the GitHub Pages URL.
  - Example: `https://terribleturtle.github.io/spellcasters-community-api/assets/units/orc_grunt.png`
  - **Validation:** `scripts/validate_integrity.py` checks for these images.
    - **Note:** Missing images are only flagged if `"image_required": true` is set in the JSON file. If omitted (default `true` per v1.0), warnings will be issued.

### 5.2 Optional Drops

- **Creatures:** The `drops` field is optional.
  - **Neutral Creeps:** Should have drops defined.
  - **Player Summons:** Should NOT have drops defined.

---

## 6. Accessing the API

Base URL: `https://terribleturtle.github.io/spellcasters-community-api/api/v1/`

- **Units:** `.../units.json`
- **Cards:** `.../cards.json`
- **Heroes:** `.../heroes.json`
- **Consumables:** `.../consumables.json`
- **Upgrades:** `.../upgrades.json`
- **Game Info:** `.../game_info.json` (Singleton)
