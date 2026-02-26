# Common Configuration for Spellcasters API Scripts
"""
Shared configuration module for Spellcasters API scripts.

This module defines:
- Directory paths (DATA_DIR, ASSETS_DIR, etc.)
- Schema mappings (SCHEMA_FILES)
- Helper functions (load_json)
"""

import json
import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas", "v2")
OUTPUT_DIR = os.path.join(BASE_DIR, "api", "v2")

# Asset Hygiene Limits
MAX_IMG_DIMENSION = 512
MAX_IMG_SIZE_KB = 100

# Patch History Files (Preserved during build)
PATCH_HISTORY_FILES = [
    "changelog_index.json",
    "changelog.json",
    "changelog_latest.json",
]
PATCH_HISTORY_DIR = "timeline"

# Schema Filenames mapping (Schema Key -> Filename)
SCHEMA_FILES = {
    "spell": "spells.schema.json",
    "unit": "units.schema.json",
    "hero": "heroes.schema.json",
    "consumable": "consumables.schema.json",
    "upgrade": "upgrades.schema.json",
    "game_config": "game_config.schema.json",
    "titan": "titans.schema.json",
    "changelog_index": "changelog_index.schema.json",
    "changelog": "changelog.schema.json",
    "timeline_entry": "timeline_entry.schema.json",
    "status": "status.schema.json",
    "patches": "patches.schema.json",
    "changelog_latest": "changelog_latest.schema.json",
    "all_data": "all_data.schema.json",
    "audit": "audit.schema.json",
    "infusion": "infusions.schema.json",
    "game_systems": "game_systems.schema.json",
}

# Data Folder to Schema Mapping (Folder Name -> Schema Key)
FOLDER_TO_SCHEMA = {
    "units": "unit",
    "spells": "spell",
    "titans": "titan",
    "heroes": "hero",
    "consumables": "consumable",
    "upgrades": "upgrade",
}


def load_json(path):
    """
    Safely loads a JSON file.

    Args:
        path (str): Absolute path to the JSON file.

    Returns:
        dict: The parsed JSON data, or None if loading failed.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Invalid JSON in {path}: {e}")
        return None
