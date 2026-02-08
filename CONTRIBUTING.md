# Contributing to Spellcasters Community API

Thank you for your interest in contributing! This project is **100% community-driven** and relies on submissions from people like you to keep the database accurate.

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## How to Contribute

### ⚡ Quick Fix (Typos & Small Edits)

You don't need to be a developer to fix a typo!

1.  Navigate to the file you want to change on GitHub.
2.  Click the **Pencil Icon** (Edit this file).
3.  Make your change.
4.  Scroll down to "Commit changes" and select **"Create a new branch for this commit and start a pull request"**.
5.  Click **Propose changes**.

### 🎨 Artist or Lorekeeper?

We need you! If you see a Unit with a missing description or a placeholder icon, you can contribute those just as easily as code.

### 🛠️ Advanced: Adding New Data

To add a new Spellcaster, Unit, Spell, Titan, or Consumable:

1.  **Fork the repository.**
2.  **Create a new JSON file** in the appropriate `data/` subdirectory.
    - `data/spellcasters/` - Player characters.
    - `data/units/` - Creatures and Buildings.
    - `data/spells/` - Spells.
    - `data/titans/` - Titan cards.
    - `data/consumables/` - Loot items.
3.  **Follow the Schema:** Ensure your JSON matches the corresponding schema in `schemas/v1/`.
    - **Changelog:** Use the `changelog` array to track version history.
    - `last_modified`: Update this timestamp.
    - `image_required`: Defaults to `true`.
4.  **Add Assets:**
    - **Production:** Add the image to `assets/[category]/[id].webp`.
    - **Archive:** Source PNGs should be stored in `assets/_archive/[category]/[id].png`.
    - **Automatic:** Place `.png` files in the main folder and run `python scripts/optimize_assets.py`. This script will generate the `.webp` and archive the `.png` for you.

### 📚 Data Reference & Hierarchy

#### 1. Spellcasters (`data/spellcasters`)

Refers to the player-controlled character (previously "Hero").

- **Schema**: `spellcaster.schema.json`
- **Key Fields**: `class` (Conqueror/Duelist/Enchanter), `difficulty` (1-3).

#### 2. Incantations

The base type for all deck-able items.

- **Schema**: `incantation.schema.json`
- **Sub-types**:
  - **Units** (`data/units`): Physical entities with `health`, `collision_radius`.
  - **Spells** (`data/spells`): Instant actions or effects.

#### 3. Titans (`data/titans`)

Unique class-ultimate entities.

- **Schema**: `titan.schema.json`

#### 4. Consumables (`data/consumables`)

Loot items found in chests.

### 2. Updating Existing Data

1.  Modify the fields in the existing JSON file.
2.  **Update `last_modified`** to the current timestamp.
3.  Add a new entry to the `changelog` array if the change is significant.

### 3. Verification

Before submitting a Pull Request, run the verification script to check your changes:

**Windows:**

```cmd
verify.bat
```

**Mac/Linux:**

```bash
python scripts/validate_integrity.py && python scripts/build_api.py
```

If the script passes without errors, your data is valid!

## 🛡️ Safety Systems

This project uses an automated **Safety System** to prevent accidental damage. When you open a Pull Request, our robots will immediately check:

1.  **Schema Validity:** Did you fill in all required fields correctly?
2.  **Integrity Check:** Did you delete a file that is being used by something else?
    - _Example: You cannot delete a Spell if a Hero still has it in their 'abilities' list._

> [!TIP]
> If your PR fails a check, click "Details" next to the failure to see exactly what went wrong.

## Reporting Bugs

Please use the GitHub Issues tab to report:

- **Incorrect data values:** Use the **Data Submission / Correction** template.
- **Script failures or bugs:** Use the **Bug Report** template.
- **New Ideas:** Use the **Feature Request** template.

## Usage Rights

By contributing to this repository, you agree that your contributions may be used freely by the community for any Spellcasters Chronicles related projects.
