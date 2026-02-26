"""
API Builder Script

This script aggregates individual JSON data files from `data/` into consolidated
API response files in `api/v2/`. It generates:
- Collection files (e.g., units.json, spells.json)
- A master all_data.json file
"""

import glob
import json
import os
import shutil
import sys
from datetime import UTC, datetime

import config
from config import load_json
from timeline_utils import build_entity_stat_changes, resolve_entity_id
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
    "titans": "titans",
}

# Single File Copy
SINGLE_FILES = {
    "game_config": "game_config.json",
    "patches": "patches.json",
    "infusions": "infusions.json",
    "game_systems": "game_systems.json",
}

# Timeline Tracking Configuration
TIMELINE_DIR = os.path.join(config.BASE_DIR, "timeline")
TRACKED_FIELDS = {
    "heroes": ["health", "difficulty", "abilities.primary.damage"],
    "units": ["health", "dps", "range", "recharge_time", "attack_interval"],
    "spells": ["damage", "range", "recharge_time", "duration", "value"],
    "titans": ["health", "damage", "dps", "movement_speed"],
    "consumables": ["value", "stack_size", "duration"],
    "upgrades": ["archetype", "level_cap"],
}


def ensure_output_dir():
    """
    Creates the output directory if it does not exist.
    Also cleans up existing generated JSON files to prevent stale data.
    """
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Generated {path} ({len(data)} items)")


def sanitize_recursive(data):
    """
    Escapes HTML characters in strings to prevent XSS.
    Uses an iterative approach to handle arbitrarily deep nesting.

    Args:
        data (dict | list | str | any): The data to sanitize.

    Returns:
        The sanitized data structure.
    """
    if isinstance(data, str):
        return data.replace("<", "&lt;")
    if not isinstance(data, (dict, list)):
        return data

    # Iterative deep-copy-and-sanitize using a stack
    if isinstance(data, dict):
        root = {}
    else:
        root = [None] * len(data)

    # Stack entries: (source_container, key_or_index, dest_container)
    stack = []

    # Seed the stack with top-level items
    if isinstance(data, dict):
        for k, v in data.items():
            stack.append((v, k, root))
    else:
        for i, v in enumerate(data):
            stack.append((v, i, root))

    while stack:
        value, key, dest = stack.pop()

        if isinstance(value, str):
            dest[key] = value.replace("<", "&lt;")
        elif isinstance(value, dict):
            new_dict = {}
            dest[key] = new_dict
            for k, v in value.items():
                stack.append((v, k, new_dict))
        elif isinstance(value, list):
            new_list = [None] * len(value)
            dest[key] = new_list
            for i, v in enumerate(value):
                stack.append((v, i, new_list))
        else:
            dest[key] = value

    return root


def inject_hero_image_urls(entity):
    """
    Injects root-relative image URLs for hero card and abilities.
    Only includes URLs if the corresponding .webp file exists in assets/.
    """
    eid = entity.get("entity_id")
    if not eid:
        return

    image_urls = {}

    # Check card art
    card_rel_path = f"heroes/{eid}.webp"
    card_abs_path = os.path.join(config.ASSETS_DIR, card_rel_path.replace("/", os.sep))
    if os.path.exists(card_abs_path):
        image_urls["card"] = f"/assets/{card_rel_path}"

    # Check abilities
    for ability_type in ["attack", "defense", "passive", "ultimate"]:
        ability_rel_path = f"heroes/abilities/{eid}_{ability_type}.webp"
        ability_abs_path = os.path.join(config.ASSETS_DIR, ability_rel_path.replace("/", os.sep))
        if os.path.exists(ability_abs_path):
            image_urls[ability_type] = f"/assets/{ability_rel_path}"

    if image_urls:
        entity["image_urls"] = image_urls


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

    # Load Game Config for Version
    game_config_path = os.path.join(DATA_DIR, "game_config.json")
    game_config = load_json(game_config_path)
    version = game_config.get("version", "0.0.1") if game_config else "0.0.1"

    all_data = {"build_info": {"version": version, "generated_at": datetime.now(UTC).isoformat()}}

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
            if content is not None:
                content = sanitize_recursive(content)
                collection.append(content)
            else:
                errors += 1

        # Inject stat changes from timeline
        tracked_fields = TRACKED_FIELDS.get(key, [])
        for entity in collection:
            eid = resolve_entity_id(entity)
            if eid:
                changes = build_entity_stat_changes(eid, TIMELINE_DIR, tracked_fields)
                if changes:
                    entity["stat_changes"] = changes

            if key == "heroes":
                inject_hero_image_urls(entity)

        # Save individual aggregation
        save_json(f"{key}.json", collection)
        all_data[key] = collection

    # Process Single Files
    for key, filename in SINGLE_FILES.items():
        print(f"Processing {key}...")
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            content = load_json(path)
            if content is not None:
                content = sanitize_recursive(content)
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
        "generated_at": datetime.now(UTC).isoformat(),
    }
    save_json("status.json", status_data)

    # Build Patch History Endpoints
    build_patch_history()

    print("Build Complete.")


def build_patch_history():
    """
    Copies changelog files and timeline snapshots from the project root
    into the API output directory so they are served as endpoints.
    """
    print("Building patch history endpoints...")
    copied = 0

    # 1. Copy changelog JSON files (e.g. changelog_index.json, changelog.json, changelog_latest.json)
    for filename in config.PATCH_HISTORY_FILES:
        src = os.path.join(config.BASE_DIR, filename)
        dst = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"[OK] Copied {filename} -> {OUTPUT_DIR}")
            copied += 1
        else:
            print(f"[WARN] Patch file not found: {src}")

    # 1a. Copy audit log
    audit_src = os.path.join(config.BASE_DIR, "audit.json")
    audit_dst = os.path.join(OUTPUT_DIR, "audit.json")
    if os.path.exists(audit_src):
        shutil.copy2(audit_src, audit_dst)
        print(f"[OK] Copied audit.json -> {OUTPUT_DIR}")
        copied += 1
    else:
        print("[WARN] audit.json not found at project root (run build_audit_log.py first)")

    # 1b. Copy paginated changelog pages (changelog_page_*.json)
    for page_file in glob.glob(os.path.join(config.BASE_DIR, "changelog_page_*.json")):
        filename = os.path.basename(page_file)
        dst = os.path.join(OUTPUT_DIR, filename)
        shutil.copy2(page_file, dst)
        print(f"[OK] Copied {filename} -> {OUTPUT_DIR}")
        copied += 1

    # 2. Copy timeline directory
    src_timeline = os.path.join(config.BASE_DIR, config.PATCH_HISTORY_DIR)
    dst_timeline = os.path.join(OUTPUT_DIR, config.PATCH_HISTORY_DIR)

    if os.path.isdir(src_timeline):
        # Clean stale files then ensure destination exists
        if os.path.isdir(dst_timeline):
            for stale in glob.glob(os.path.join(dst_timeline, "*.json")):
                os.remove(stale)
        os.makedirs(dst_timeline, exist_ok=True)

        for entry in os.listdir(src_timeline):
            if entry.startswith("."):
                continue  # skip dotfiles like .gitkeep
            src_file = os.path.join(src_timeline, entry)
            dst_file = os.path.join(dst_timeline, entry)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                copied += 1

        file_count = len([f for f in os.listdir(src_timeline) if not f.startswith(".")])
        print(f"[OK] Copied {file_count} timeline snapshots -> {dst_timeline}")
    else:
        print(f"[WARN] Timeline directory not found: {src_timeline}")

    print(f"Patch history: {copied} files copied.")


if __name__ == "__main__":
    main()
