# Common Configuration for Spellcasters API Scripts

import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas", "v1")
OUTPUT_DIR = os.path.join(BASE_DIR, "api", "v1")

# Asset Hygiene Limits
MAX_IMG_DIMENSION = 512
MAX_IMG_SIZE_KB = 100

# Schema Filenames mapping (Schema Key -> Filename)
SCHEMA_FILES = {
    "incantation": "incantation.schema.json",
    "spellcaster": "spellcaster.schema.json",
    "consumable": "consumable.schema.json",
    "upgrade": "upgrade.schema.json",
    "game_info": "game_info.schema.json",
    "titan": "titan.schema.json"
}

# Data Folder to Schema Mapping (Folder Name -> Schema Key)
FOLDER_TO_SCHEMA = {
    "units": "incantation",
    "spells": "incantation",
    "titans": "titan",
    "spellcasters": "spellcaster",
    "consumables": "consumable",
    "upgrades": "upgrade"
}
