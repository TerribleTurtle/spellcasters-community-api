"""
API Builder Script

This script aggregates individual JSON data files from `data/` into consolidated
API response files in `api/v1/`. It generates:
- Collection files (e.g., units.json, spells.json)
- A master all_data.json file
"""

import json
import os
import glob
import sys
import subprocess
from datetime import datetime, timezone

import config
from config import load_json
from validate_integrity import validate_integrity

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
    "titans": "titans"
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
    # Only delete files we are about to regenerate to preserve patch history
    # 1. Collection files
    for key in AGGREGATION_MAP:
        path = os.path.join(OUTPUT_DIR, f"{key}.json")
        if os.path.exists(path):
            os.remove(path)

    # 2. Single files
    for key in SINGLE_FILES:
        path = os.path.join(OUTPUT_DIR, f"{key}.json")
        if os.path.exists(path):
            os.remove(path)

    # 3. Master & Status
    for fname in ["all_data.json", "status.json"]:
        path = os.path.join(OUTPUT_DIR, fname)
        if os.path.exists(path):
            os.remove(path)

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


def get_last_modified_date(filepath):
    """
    Gets the last commit date for a file from git history.
    Fallback to OS modification time or current time if git fails.
    """
    try:
        # Get ISO 8601 date from latest commit for this file
        # %cI = committer date, strict ISO 8601 format
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cI', filepath],
            capture_output=True,
            text=True,
            check=True
        )
        timestamp = result.stdout.strip()
        if timestamp:
            return timestamp
    except Exception:
        pass

    # Fallback: Use current time
    return datetime.now(timezone.utc).isoformat()


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
    if isinstance(data, dict):
        return {k: sanitize_recursive(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_recursive(v) for v in data]
    return data


def main():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    print(f"Building API {VERSION_API}...")

    # 1. Safety Lock: Validate Integrity
    try:
        validate_integrity()
    except SystemExit as e:
        if e.code != 0:
            print("[FATAL] Validation failed. Build aborted.")
            sys.exit(1)

    ensure_output_dir()

    # Load Game Config for Version
    game_config_path = os.path.join(DATA_DIR, "game_config.json")
    game_config = load_json(game_config_path)
    version = game_config.get("version", "0.0.1") if game_config else "0.0.1"

    all_data = {
        "build_info": {
            "version": version,
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

                # Inject last_modified from git history if missing
                if 'last_modified' not in content:
                    content['last_modified'] = get_last_modified_date(file)

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

                # Inject last_modified from git history if missing
                if 'last_modified' not in content:
                    content['last_modified'] = get_last_modified_date(path)

                save_json(f"{key}.json", content)
                all_data[key] = content
            else:
                errors += 1
        else:
            print(f"[WARN] File not found: {path}")

    # Save Master File
    save_json("all_data.json", all_data)

    if errors > 0:
        print(f"[FAIL] Build failed with {errors} errors.")
        sys.exit(1)

    # Generate Status/Upgrade Endpoint (Placeholder)
    print("Generating status.json...")
    status_data = {
        "status": "online",
        "environment": "dev",
        "maintenance": False,
        "valid_versions": [version],
        "min_client_version": "0.0.0",
        "upgrade_required": False,
        "message": "Development Server Online",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    save_json("status.json", status_data)

    print("Build Complete.")


if __name__ == "__main__":
    main()
