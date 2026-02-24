"""
Changelog Builder Script

Reads `data/patches.json` (the source of truth for all patch data) and generates
the following API-consumable files in the repository root:

- changelog.json           — Full array of all patch entries
- changelog_latest.json    — Single most-recent patch object
- changelog_index.json     — Pagination manifest
- changelog_page_N.json    — Paginated chunks

These root files are then copied into `api/v2/` by `build_api.py`.
"""

import json
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

PATCHES_FILE = os.path.join(config.DATA_DIR, "patches.json")
ROOT_DIR = config.BASE_DIR

# Number of patches per page — matches the existing page_size convention
PAGE_SIZE = 50


def load_json(path):
    """Safely loads a JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Could not parse {path}: {e}")
            return None


def save_json(path, data):
    """Writes data to a JSON file with consistent formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Generated {os.path.basename(path)}")


def clean_patches(patches):
    """Strips legacy keys that should not appear in the public API."""
    cleaned = []
    for patch in patches:
        entry = {k: v for k, v in patch.items() if k != "diff"}
        cleaned.append(entry)
    return cleaned


def main():
    """Builds all changelog files from data/patches.json."""
    print("Building changelogs from data/patches.json...")

    raw_patches = load_json(PATCHES_FILE)
    if raw_patches is None:
        print("[WARN] No patches.json found. Generating empty changelogs.")
        raw_patches = []

    # Strip legacy "diff" keys
    patches = clean_patches(raw_patches)

    # --- 1. changelog.json (full array) ---
    changelog_path = os.path.join(ROOT_DIR, "changelog.json")
    save_json(changelog_path, patches)

    # --- 2. changelog_latest.json (most recent patch) ---
    latest_path = os.path.join(ROOT_DIR, "changelog_latest.json")
    if patches:
        save_json(latest_path, patches[0])
    else:
        save_json(latest_path, None)

    # --- 3. Paginated changelog_page_N.json ---
    total_patches = len(patches)
    total_pages = max(1, math.ceil(total_patches / PAGE_SIZE))
    page_filenames = []

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_data = patches[start:end]

        page_filename = f"changelog_page_{page_num}.json"
        page_path = os.path.join(ROOT_DIR, page_filename)
        save_json(page_path, page_data)
        page_filenames.append(page_filename)

    # --- 4. changelog_index.json (pagination manifest) ---
    index_path = os.path.join(ROOT_DIR, "changelog_index.json")
    index_data = {
        "total_patches": total_patches,
        "page_size": PAGE_SIZE,
        "total_pages": total_pages,
        "pages": page_filenames,
    }
    save_json(index_path, index_data)

    print(f"Changelog build complete: {total_patches} patches across {total_pages} page(s).")


if __name__ == "__main__":
    main()
