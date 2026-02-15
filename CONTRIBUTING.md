# Contributing to Spellcasters Community API

Thank you for your interest in contributing! This project is **100% community-driven** and relies on submissions from people like you to keep the database accurate.

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

> [!NOTE]
> **Terminology:** In the game lore, characters are called **Spellcasters**. In this codebase and schema, they are strictly referred to as **Heroes** (`data/heroes`). These terms are interchangeable.

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
    - `data/heroes/` - Player characters.
    - `data/units/` - Creatures and Buildings.
    - `data/spells/` - Spells.
    - `data/titans/` - Titan cards.
    - `data/consumables/` - Loot items.
3.  **Follow the Schema:** Ensure your JSON matches the corresponding schema in `schemas/v2/`.
    - **Changelog:** Use the `changelog` array to track version history.
    - `last_modified`: Update this timestamp.
    - `image_required`: Defaults to `true`.
4.  **Add Assets:**
    - **Production:** Add the image to `assets/[category]/[id].webp`.
    - **Automatic:** Place `.webp` files directly in `assets/[category]/[id].webp`.
      - **Constraints:** Max 512x512px, Max 100KB.
      - **Note:** We no longer support automatic PNG-to-WebP conversion. Please use an external tool to convert your images to WebP before submitting.

### 📚 Data Reference & Hierarchy

#### 1. Heroes (`data/heroes`)

Refers to the player-controlled characters.

- **Data Location:** `data/heroes/[id].json`
- **Schema:** `schemas/v2/heroes.schema.json`
- **Key Fields**: `class` (Conqueror/Duelist/Enchanter), `difficulty` (1-3).

#### 2. Units (`data/units`)

- **Schema**: `schemas/v2/units.schema.json`
- **Description**: Physical entities with health, collision, and movement. (Creatures & Buildings)

#### 3. Spells (`data/spells`)

- **Schema**: `schemas/v2/spells.schema.json`
- **Description**: Instant actions or effects.

#### 4. Titans (`data/titans`)

Unique class-ultimate entities.

- **Schema**: `schemas/v2/titans.schema.json`

#### 5. Consumables (`data/consumables`)

Loot items found in chests.

#### 5. Consumables (`data/consumables`)

Loot items found in chests.

#### 6. Upgrades (`data/upgrades`)

RNG Level-up bonus options.

- **Schema**: `schemas/v2/upgrades.schema.json`
- **Key Fields**:
  - `target_tags`: Array of Unit tags this upgrade applies to (e.g., `["Construct", "Melee"]`).
  - `effect`: Object defining stats to modify (e.g., `{"damage": 5}`).

#### 7. Game Config (`data/game_config.json`)

The single source of truth for the Game Version and global metadata.

### 📈 Data Standards (v1.1)

#### 1. Multipliers (Percentage Values)

To avoid ambiguity between "Increased By" vs "Total", we use standard **Multipliers**:

- **1.0** = 100% (Base Damage).
- **1.5** = 150% (Deals 1.5x Damage). "Strong vs X".
- **0.5** = 50% (Deals 0.5x Damage). "Weak vs X".
- **2.6** = 260% (Deals 2.6x Damage).

**Rule of Thumb**:

- "Deals X% Damage" -> `Multiplier = X / 100`.
- "Deals X% **Increased** Damage" -> `Multiplier = 1 + (X / 100)`.

#### 2. Handling Unknown Values (Beta Data)

Since we are in Beta, some exact numbers may be missing.

**Standard**: Use **`-1.0`** as a **Sentinel Value** for "Unknown/To Be Verified".

- **Description Field**: Append `(UNKNOWN)` to the condition so it's searchable.
- **Example**:
  ```json
  "multiplier": -1.0,
  "condition": "MovementType == Flying (UNKNOWN)"
  ```

### 3. Complex Mechanics (v2)

We use strongly-typed objects for mechanics to ensure the game engine can read them without parsing text.

- **`pierce`** (Boolean): Projectiles pass through enemies.
- **`stealth`** (Object): Duration and break conditions.
- **`cleave`** (Object): Radius, Arc, and Damage %.
- **`damage_modifiers`** (Array):
  - **Match:** Target Type (e.g., "Building").
  - **Condition:** Structured logic (e.g., `{"field": "target.hp_percent", "op": "<", "val": 0.5}`).
    - _Note: Legacy string conditions (e.g., "Always") are strictly forbidden._

### 2. Updating Existing Data

1.  Modify the fields in the existing JSON file.
2.  **Update `last_modified`** to the current timestamp.
3.  Add a new entry to the `changelog` array if the change is significant.

### 3. Verification

Before submitting a Pull Request, run the verification script to check your changes:

**Windows / Mac / Linux:**

```bash
python scripts/validate_integrity.py
```

If the tests pass without errors, your data is valid!
(Note: The validation script will also check asset integrity.)

If the tests pass without errors, your data is valid!
(Note: The validation script will also check asset integrity.)

#### Logic Integrity Rules

Beyond the schema, `validate_integrity.py` enforces strict logic compliance:

1.  **Referential Integrity:**
    - Upgrade targets MUST exist.
2.  **Upgrade Targets:**
    - Every tag listed in an Upgrade's `target_tags` MUST exist on at least one Unit in the database. You cannot target a tag that doesn't exist.

## 🛡️ Safety Systems

This project uses an automated **Safety System** to prevent accidental damage. When you open a Pull Request, our robots will immediately check:

1.  **Schema Validity:** Did you fill in all required fields correctly?
2.  **Integrity Check:** Did you delete a file that is being used by something else?
    - _Example: You cannot delete a Spell if a Hero still has it in their 'abilities' list._

> [!TIP]
> If your PR fails a check, click "Details" next to the failure to see exactly what went wrong.

## 🛡️ Security

### Data Sanitization (XSS Prevention)

The API build pipeline (`scripts/build_api.py`) automatically sanitizes all string fields to prevent Cross-Site Scripting (XSS) attacks.

- **Behavior:** All `<` characters are replaced with `&lt;`.
- **Developer Note:** If you intend to render text from this API, strictly treat it as **text content**, not innerHTML. If you must render HTML, you are responsible for decoding and sanitizing it again in your application.

### Vulnerability Reporting

If you discover a security vulnerability, please **DO NOT** open a public issue.
Refer to our [Security Policy](docs/SECURITY.md) for reporting instructions.

## Reporting Bugs

Please use the GitHub Issues tab to report:

- **Incorrect data values:** Use the **Data Submission / Correction** template.
- **Script failures or bugs:** Use the **Bug Report** template.
- **New Ideas:** Use the **Feature Request** template.

## Usage Rights

By contributing to this repository, you agree that your contributions may be used freely by the community for any Spellcasters Chronicles related projects.
