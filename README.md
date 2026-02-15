# Spellcasters Community API (Free & Open)

**A free, open-source API for Spellcasters Chronicles.**

> [!WARNING]
> **BETA NOTICE:** Current data reflects the **Closed Beta**.
> We will begin manual updates for **Early Access** on and after **Feb 26th**.
>
> **SCHEMA ALERT:** The JSON schema is volatile and may change without notice until **Feb 26th**.

This project is a collaborative tool for **developers** (building apps/tools) and the **community** (wiki editors/fans).
It is **free to use** and **open for anyone to contribute**.

## 📚 Documentation

Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to:

- Use this data in your own projects
- Add new units or items
- Fix typos

## 💬 Community

This project is a fan-made initiative.

- **Looking for the game devs?** [Join the Official Game Discord](https://discord.com/invite/spellcasters-chronicles-1425209254847058003).
- **Want to help with this API?** Check out [CONTRIBUTING.md](CONTRIBUTING.md).

## 🌐 Live API Usage

**Base URL:** `https://terribleturtle.github.io/spellcasters-community-api/api/v2/`

Developers should use this base URL to fetch data for their applications.

- **Landing Page:** [View Live Site](https://terribleturtle.github.io/spellcasters-community-api/)
- **System:**
  - [status.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/status.json) - API Health & Version Info
  - [game_config.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/game_config.json) - Game Version & Metadata
- **Collections:**
  - [heroes.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/heroes.json)
  - [units.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/units.json)
  - [spells.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/spells.json)
  - [titans.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/titans.json)
  - [consumables.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/consumables.json)
  - [upgrades.json](https://terribleturtle.github.io/spellcasters-community-api/api/v2/upgrades.json)

### 🌟 API in Action

Check out [SpellcastersDB](https://www.spellcastersdb.com/), a community-built database and deckbuilder powered by this API!

Full endpoint documentation is available in [CONTRIBUTING.md](CONTRIBUTING.md).

## 🚀 Quick Start (Local Build)

1.  **Install Python 3.9+**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Build & Verify:**

    ```bash
    python scripts/validate_integrity.py
    ```

    See `api/v2/units.json`

## 🤝 Contributing

This project is built by the community, for the community. **Anyone is free to contribute!**

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

- **Found a typo?** Reference the [Quick Fix Guide](CONTRIBUTING.md#%E2%9A%A1-quick-fix-typos--small-edits).
- **Adding data?** See the [Advanced Guide](CONTRIBUTING.md#%F0%9F%9B%A0%EF%B8%8F-advanced-adding-new-data).

## 📄 License

This project is open source under the [MIT License](LICENSE).

### ⚠️ Legal & IP Disclaimer

> [!IMPORTANT]
> **Spellcasters Chronicles** is a trademark of **Quantic Dream**.

This project is a community-maintained tool and is **not** affiliated with, endorsed by, or sponsored by Quantic Dream.

- **Code:** The source code of this API builder is licensed under the MIT License.
- **Assets & Data:** All game images, icons, names, and lore are the intellectual property of the game developers. They are used here for educational/informational purposes under standard Fan Content principles.
- **Fan Content Policy:** Users of this API must respect the IP rights of the original creators.
- **Assets:** Images in the `assets/` folder are provided for reference only.
- **Data:** Game data is collected by the community and may not reflect the latest live game state.

### ⚠️ Data Accuracy Disclaimer

While we strive for accuracy, this API is maintained by volunteers. Data is entered manually and may contain errors. **Do not** use this data for financial decisions or competitive play without verifying it in-game.

### 🛡️ Security Disclaimer

This API provides **raw data** from community contributions.
**Developers:** You MUST sanitize this data before rendering it in your applications. Treating descriptions or text fields as trusted HTML may expose your users to Cross-Site Scripting (XSS) attacks.

### 3. Complex Mechanics (v2)

We use strongly-typed objects for mechanics to ensure the game engine can read them without parsing text.

- **`pierce`** (Boolean): Projectiles pass through enemies.
- **`stealth`** (Object): Duration and break conditions.
- **`cleave`** (Boolean | Object): Projectiles pass multiple targets. Object defines Radius, Arc, and Damage %.
- **`damage_modifiers`** (Array):
  - **Match:** Target Type (e.g., "Building").
  - **Condition:** Structured logic (e.g., `{"field": "target.hp_percent", "op": "<", "val": 0.5}`).
    - _Note: Legacy string conditions (e.g., "Always") are strictly forbidden._

## 📂 Structure

- `data/`: Source JSON files.
- `assets/`: Images.
- `api/`: Generated API output (Do not edit manually).
