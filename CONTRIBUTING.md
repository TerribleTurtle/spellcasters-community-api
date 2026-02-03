# Contributing to Spellcasters Community API

Thank you for your interest in contributing! This project relies on community submissions to keep the database accurate and up-to-date.

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## How to Contribute

### ⚡ Quick Fix (Typos & Small Edits)

You don't need to be a developer to fix a typo!

1.  Navigate to the file you want to change on GitHub.
2.  Click the **Pencil Icon** (Edit this file).
3.  Make your change.
4.  Scroll down to "Commit changes" and select **"Create a new branch for this commit and start a pull request"**.
5.  Click **Propose changes**.

### 🛠️ Advanced: Adding New Data

To add a new creature, spell, hero, or item:

1.  **Fork the repository.**
2.  **Create a new JSON file** in the appropriate `data/` subdirectory (e.g., `data/creatures/new_creature.json`).
3.  **Follow the Schema:** Ensure your JSON matches the corresponding schema in `schemas/v1/`.
    - You must include a `version` field (e.g., `"version": "1.0.0"`).
    - You must include `date_modified`.
    - **Optional:** If the item _requires_ an in-game asset (e.g., a card art), set `"image_required": true`. Default is `false`.
4.  **Add Assets (Optional):** If you have the icon, add it to `assets/` with the exact same filename (e.g., `assets/creatures/new_creature.png`).

### 2. Updating Existing Data

1.  Modify the fields in the existing JSON file.
2.  **Update `date_modified`** to the current timestamp.
3.  Increment the `version` if the change is structural or significant.

### 3. Verification

Before submitting a Pull Request, run the build script to verify your changes:

```bash
python scripts/build_api.py
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
