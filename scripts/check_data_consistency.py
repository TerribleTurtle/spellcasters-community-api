"""
V1 to V2 Data Consistency Checker

Audits the granular V2 JSON data against the legacy monolithic V1_all_data.json
file. Identifies discrepancies and mapped field regressions during migration.
"""

import json
import os

V1_FILE = r"c:\Projects\spellcasters-community-api\V1_all_data.json"
DATA_DIR = r"c:\Projects\spellcasters-community-api\data"
REPORT_FILE = r"c:\Projects\spellcasters-community-api\scripts\consistency_report.txt"

MAPPINGS = {
    "spellcasters": "heroes",
    "consumables": "consumables",
    "units": "units",
    "spells": "spells",
    "titans": "titans",
}

# Special field mappings: V1 key -> V2 key
FIELD_MAPPINGS = {
    "spellcaster_id": "entity_id",  # V1 spellcaster_id -> V2 entity_id
    "entity_id": "entity_id",  # V1 entity_id -> V2 entity_id
    "heal_amount": "value",  # For non-titans
    "stagger_modifier": "stagger_modifier",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_v2_path(category, item_id):
    path = os.path.join(DATA_DIR, category, f"{item_id}.json")
    return path


def compare_values(v1_val, v2_val, path_context):
    if path_context.endswith("stagger_modifier"):
        if isinstance(v1_val, str) and isinstance(v2_val, bool):
            return bool(v1_val) == v2_val

    if path_context.endswith("target_type") and isinstance(v2_val, list) and isinstance(v1_val, str):
        if v1_val in v2_val:
            return True

    if v1_val == v2_val:
        return True

    if isinstance(v1_val, (int, float)) and isinstance(v2_val, (int, float)):
        return abs(v1_val - v2_val) < 0.001

    return False


def check_item(v1_item, v2_item, category, item_id, path_prefix=""):
    errors = []

    for key, v1_val in v1_item.items():
        if key in ["$schema", "last_modified", "changelog", "image_required"]:
            continue

        # Handle stats flattening
        if key == "stats" and isinstance(v1_val, dict):
            sub_errors = check_item(v1_val, v2_item, category, item_id, path_prefix + "stats/")
            errors.extend(sub_errors)
            continue

        v2_key = key
        # Apply field mappings
        if category == "heroes" and key == "spellcaster_id":
            v2_key = "entity_id"
        elif key == "heal_amount" and category != "titans":
            v2_key = "value"

        # Check for presence
        if v2_key not in v2_item:
            errors.append(f"Missing field in V2: {v2_key} (V1: {path_prefix}{key})")
            continue

        v2_val = v2_item[v2_key]

        if isinstance(v1_val, dict):
            if not compare_complex(v1_val, v2_val, f"{category}/{item_id}/{path_prefix}{key}"):
                errors.append(f"Mismatch in {path_prefix}{key}: V1={v1_val} != V2={v2_val}")
        elif isinstance(v1_val, list):
            if not compare_complex(v1_val, v2_val, f"{category}/{item_id}/{path_prefix}{key}"):
                errors.append(f"Mismatch in {path_prefix}{key}: V1={v1_val} != V2={v2_val}")
        else:
            if not compare_values(v1_val, v2_val, f"{category}/{item_id}/{path_prefix}{key}"):
                errors.append(f"Value mismatch for {path_prefix}{key}: V1={v1_val} != V2={v2_val}")

    return errors


def compare_complex(v1, v2, path):
    if not isinstance(v1, type(v2)):
        if isinstance(v2, list) and isinstance(v1, str) and path.endswith("target_type"):
            return v1 in v2
        return False

    if isinstance(v1, dict):
        for k, v in v1.items():
            if k not in v2:
                if k == "target_type" and "target_types" in v2:
                    return compare_complex(v, v2["target_types"], f"{path}/{k}")
                return False
            if not compare_complex(v, v2[k], f"{path}/{k}"):
                return False
        return True

    if isinstance(v1, list):
        if len(v1) != len(v2):
            return False
        for i in range(len(v1)):
            if not compare_complex(v1[i], v2[i], f"{path}[{i}]"):
                return False
        return True

    return compare_values(v1, v2, path)


def main():
    print("Loading V1 data...")
    try:
        v1_data = load_json(V1_FILE)
    except Exception as e:
        print(f"Error loading V1 data: {e}")
        return

    report = []

    for v1_cat, v2_dir in MAPPINGS.items():
        if v1_cat not in v1_data:
            continue
        items = v1_data[v1_cat]

        for item in items:
            if "spellcaster_id" in item:
                item_id = item["spellcaster_id"]
            elif "entity_id" in item:
                item_id = item["entity_id"]
            else:
                continue

            v2_path = get_v2_path(v2_dir, item_id)
            if not os.path.exists(v2_path):
                report.append(f"[MISSING] {v1_cat}/{item_id}: File not found at {v2_path}")
                continue

            try:
                v2_item = load_json(v2_path)
            except Exception as e:
                report.append(f"[ERROR] {v1_cat}/{item_id}: Error loading V2 file: {e}")
                continue

            errors = check_item(item, v2_item, v2_dir, item_id)
            for err in errors:
                report.append(f"[MISMATCH] {v1_cat}/{item_id}: {err}")

    if "game_info" in v1_data:
        v2_path = os.path.join(DATA_DIR, "game_config.json")
        if os.path.exists(v2_path):
            v2_item = load_json(v2_path)
            errors = check_item(v1_data["game_info"], v2_item, "game_config", "game_config")
            for err in errors:
                report.append(f"[MISMATCH] game_info: {err}")

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 30 + "\n")
        f.write("COMPARISON REPORT\n")
        f.write("=" * 30 + "\n")
        if not report:
            f.write("SUCCESS: V2 data matches V1 data!\n")
        else:
            for line in report:
                f.write(line + "\n")
            f.write(f"\nTotal discrepancies: {len(report)}\n")
    print(f"Report written to {REPORT_FILE}")


if __name__ == "__main__":
    main()
