# Spellcasters Community API

The central, static API for Spellcasters Chronicles data.

## 📚 Documentation

Please refer to [GUIDE.md](GUIDE.md) for the complete Setup, Usage, and Contribution guide.

## 🚀 Quick Start

1.  **Install Python 3.9+**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Build API:**
    ```bash
    python scripts/build_api.py
    ```
    See `api/v1/all_creatures.json`

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

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
