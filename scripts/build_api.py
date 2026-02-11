import json
import os
import html
import glob
import sys
import hashlib
from datetime import datetime, timezone

import config
from config import load_json

"""
API Builder Script

This script aggregates individual JSON data files from `data/` into consolidated
API response files in `api/v1/`. It generates:
- Collection files (e.g., units.json, spells.json)
- A master all_data.json file
"""


# Configuration
VERSION_API = "v2"
OUTPUT_DIR = config.OUTPUT_DIR
DATA_DIR = config.DATA_DIR

# Schema to Data Directory Map
# Output FilenameBase -> Source Directory
AGGREGATION_MAP = {
    "heroes": "heroes",
    "consumables": "consumables",
    "upgrades": "upgrades",
    "units": "units",
    "spells": "spells",
    "titans": "titans",
    "decks": "decks"
}

# Single File Copy
SINGLE_FILES = {
    "game_config": "game_config.json"
}

def ensure_output_dir():
    """Creates the output directory if it does not exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")
    
    # Cleanup old files
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*.json")):
        os.remove(f)
    print(f"Cleaned up output directory: {OUTPUT_DIR}")

def save_json(filename, data):
    """
    Saves data to a JSON file in the output directory.

    Args:
        filename (str): The name of the file (e.g., 'units.json').
        data (dict | list): The data to serialize.
    """
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Generated {path} ({len(data)} items)")


def sanitize_recursive(data):
    """
    Recursively escapes HTML characters in strings to prevent XSS.
    
    Args:
        data (dict | list | str | any): The data to sanitize.
        
    Returns:
        The sanitized data structure.
    """
    if isinstance(data, str):
        # Only escape < to prevent tag injection, preserving > and quotes for readability and game math
        return data.replace("<", "&lt;")
    elif isinstance(data, dict):
        return {k: sanitize_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_recursive(v) for v in data]
    return data



from validate_integrity import validate_integrity

def main():
    print(f"Building API {VERSION_API}...")
    
    # 1. Safety Lock: Validate Integrity
    try:
        validate_integrity()
    except SystemExit as e:
        if e.code != 0:
            print("[FATAL] Validation failed. Build aborted.")
            sys.exit(1)
    
    ensure_output_dir()
    
    all_data = {
        "build_info": {
            "version": "0.0.1",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    errors = 0

    # Aggregate Collections
    for key, folder in AGGREGATION_MAP.items():
        print(f"Aggregating {key} from data/{folder}...")
        collection = []
        source_path = os.path.join(DATA_DIR, folder)
        
        if not os.path.exists(source_path):
            print(f"[WARN] Directory not found: {source_path}")
            all_data[key] = []
            # Not a critical error, just a warning
            continue

        files = glob.glob(os.path.join(source_path, "*.json"))
        for file in files:
            content = load_json(file)
            if content:
                content = sanitize_recursive(content)
                collection.append(content)
            else:
                errors += 1
        
        # Save individual aggregation
        save_json(f"{key}.json", collection)
        all_data[key] = collection

    # Process Single Files
    for key, filename in SINGLE_FILES.items():
        print(f"Processing {key}...")
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            content = load_json(path)
            if content:
                content = sanitize_recursive(content)
                save_json(f"{key}.json", content)
                all_data[key] = content
            else:
                errors += 1
        else:
            print(f"[WARN] File not found: {path}")
            # Optional file missing is not always a critical error depending on logic,
            # but usually single files are expected.
            # strict mode: errors += 1 (?) -> Let's keep it as warn for now unless critical.


    # Save Master File
    save_json("all_data.json", all_data)
    
    if errors > 0:
        print(f"[FAIL] Build failed with {errors} errors.")
        sys.exit(1)
        
    print("Build Complete.")

if __name__ == "__main__":
    main()
