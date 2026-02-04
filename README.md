# Spellcasters Community API (Free & Open)

**A free, open-source API for Spellcasters Chronicles.**

This project is a collaborative tool for **developers** (building apps/tools) and the **community** (wiki editors/fans).
It is **free to use** and **open for anyone to contribute**.

## 📚 Documentation

Please refer to [GUIDE.md](GUIDE.md) to learn how to:

- Use this data in your own projects
- Add new units or items
- Fix typos

## 💬 Community

Join the conversation on the [Official Discord](https://discord.com/invite/spellcasters-chronicles-1425209254847058003).

## 🌐 Live API Usage

**Base URL:** `https://terribleturtle.github.io/spellcasters-community-api/api/v1/`

Developers should use this base URL to fetch data for their applications.

- **Landing Page:** [View Live Site](https://terribleturtle.github.io/spellcasters-community-api/)
- **Game Info:** [game_info.json](https://terribleturtle.github.io/spellcasters-community-api/api/v1/game_info.json)
- **Units:** [units.json](https://terribleturtle.github.io/spellcasters-community-api/api/v1/units.json)

Full endpoint documentation is available in [GUIDE.md](GUIDE.md).

## 🚀 Quick Start (Local Build)

1.  **Install Python 3.9+**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Build & Verify:**

    ```bash
    # Windows
    verify.bat

    # Mac/Linux
    python scripts/build_api.py
    ```

    See `api/v1/units.json`

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

## 📂 Structure

- `data/`: Source JSON files.
- `assets/`: Images.
- `api/`: Generated API output (Do not edit manually).
