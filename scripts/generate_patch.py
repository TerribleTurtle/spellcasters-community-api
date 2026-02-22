"""
Automated Patch Generation Script

This script computes differences for JSON files changed in the current git commit
(or staging area) and automatically merges them into the current active patch block
in patches.json.

Requires: `deepdiff` library for computing structured JSON diffs.

It then integrates with build_api.py to generate updated static timeline and changelog files.
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime

from deepdiff import DeepDiff

# Import local modules safely
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import build_changelogs  # noqa: E402
import config  # noqa: E402

DATA_DIR = config.DATA_DIR
PATCHES_FILE = os.path.join(DATA_DIR, "patches.json")
GAME_CONFIG_PATH = os.path.join(DATA_DIR, "game_config.json")


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_git_diff_files():
    """Gets the list of changed files from git.
    Dynamically determines the BEFORE_SHA based on the last commit that
    modified data/patches.json, to ensure no changes are missed if
    multiple PRs merge concurrently."""
    try:
        after_sha = os.environ.get("AFTER_SHA")
        if not after_sha:
            after_sha = "HEAD"

        try:
            # Find the last commit where data/patches.json was modified.
            # This is our reliable "last processed state" baseline.
            result_last_patch = subprocess.run(
                ["git", "log", "-1", "--format=%H", "data/patches.json"], capture_output=True, text=True, check=True
            )
            before_sha = result_last_patch.stdout.strip()
        except subprocess.CalledProcessError:
            before_sha = None

        # Fallback if something went wrong finding BEFORE_SHA
        if not before_sha:
            before_sha = os.environ.get("BEFORE_SHA")

        if not before_sha or before_sha.startswith("0000000"):
            before_sha = "HEAD~1"

        print(f"Comparing diff between {before_sha} and {after_sha}")

        # Get files changed in the specified range
        result = subprocess.run(
            ["git", "diff", "--name-status", before_sha, after_sha], capture_output=True, text=True, check=True
        )
        changed_files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            status = parts[0]
            filepath = parts[1]

            # Only care about data/ json files
            if filepath.startswith("data/") and filepath.endswith(".json"):
                changed_files.append((status, filepath))

        return changed_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return []


def get_file_content_at_commit(filepath, commit_hash="HEAD~1"):
    """Reads the content of a file at a specific commit."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit_hash}:{filepath}"], capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return None  # File didn't exist in that commit
    except json.JSONDecodeError:
        return None


def get_commit_author():
    """Gets the author name of the most recent commit."""
    try:
        result = subprocess.run(["git", "log", "-1", "--format=%an"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _map_path_to_array(path_str):
    """
    Converts a deepdiff path string "root['mechanics']['damage_modifiers'][1]"
    to a list ["mechanics", "damage_modifiers", 1]
    """
    # Remove "root" prefix
    if path_str.startswith("root"):
        path_str = path_str[4:]

    parts = []
    # Find all tokens inside brackets, e.g. 'mechanics' or 1
    # This regex matches either single-quoted strings or digits
    matches = re.findall(r"\[(?:'([^']+)'|(\d+))\]", path_str)

    for string_match, int_match in matches:
        if string_match:
            parts.append(string_match)
        elif int_match:
            parts.append(int(int_match))

    return parts


def _get_timeline_baseline(filepath, current_version):
    """
    Attempts to fetch the entity's state from the timeline for the PREVIOUS version.
    Since timeline snapshots represent the state *after* a version is applied,
    we must compare against the snapshot from the previous version to get a cumulative diff.
    """
    filename = os.path.basename(filepath)
    entity_id = os.path.splitext(filename)[0]
    timeline_path = os.path.join(config.BASE_DIR, config.PATCH_HISTORY_DIR, f"{entity_id}.json")

    if not os.path.exists(timeline_path):
        return None

    timeline = load_json(timeline_path)
    if not timeline:
        return None

    # We want the snapshot immediately preceding current_version, or the latest available
    # Assuming timeline is sorted chronologically or we just take the last one that isn't current_version
    # In practice, comparing against the most recent snapshot that isn't current_version
    valid_snapshots = [entry for entry in timeline if entry.get("version") != current_version]
    if valid_snapshots:
        # Take the most recent valid snapshot (last in list if appended chronologically)
        return valid_snapshots[-1].get("snapshot")

    return None


def _create_timeline_baseline(filepath, current_version, entity_data):
    """
    Creates a timeline snapshot for a newly added entity.
    Follows the same format as snapshot_baseline.py: [{version, date, snapshot}]
    Idempotent: skips if the current version already has an entry.
    """
    filename = os.path.basename(filepath)
    entity_id = os.path.splitext(filename)[0]
    timeline_dir = os.path.join(config.BASE_DIR, config.PATCH_HISTORY_DIR)
    timeline_path = os.path.join(timeline_dir, f"{entity_id}.json")

    os.makedirs(timeline_dir, exist_ok=True)

    # Load existing timeline or start fresh
    timeline = []
    if os.path.exists(timeline_path):
        timeline = load_json(timeline_path) or []
        # Idempotency: skip if version already exists
        if any(entry.get("version") == current_version for entry in timeline):
            print(f"  Timeline already has {current_version} for {entity_id}, skipping.")
            return

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    snapshot_entry = {"version": current_version, "date": today, "snapshot": entity_data}
    timeline.append(snapshot_entry)
    save_json(timeline_path, timeline)
    print(f"  Created timeline baseline for {entity_id} at {current_version}")


def generate_slim_change(filepath, status, current_version):
    """Generates a slim diff representing the change in patches.json format.

    For additions (status 'A'), old_data is set to {} so DeepDiff produces
    full-object 'N' diffs, and a timeline baseline snapshot is created.
    For deletions (status 'D'), new_data is set to {} so DeepDiff produces
    full-object 'D' diffs.
    """
    parts = filepath.split("/")
    if len(parts) < 3:
        return None

    category = parts[1]  # e.g. heroes
    filename = parts[-1]

    old_data = None
    new_data = None

    if status == "A":
        # Addition: diff against empty dict to capture all fields as new
        full_path = os.path.join(config.BASE_DIR, filepath)
        new_data = load_json(full_path)
        old_data = {}
    elif status == "D":
        # Deletion: diff old state against empty dict to capture all fields as removed
        old_data = _get_timeline_baseline(filepath, current_version)
        if old_data is None:
            old_data = get_file_content_at_commit(filepath)
        new_data = {}
    elif status == "M":
        # Modification: standard diff logic
        old_data = _get_timeline_baseline(filepath, current_version)
        if old_data is None:
            old_data = get_file_content_at_commit(filepath)
        full_path = os.path.join(config.BASE_DIR, filepath)
        new_data = load_json(full_path)

    change_type = "edit"
    if status == "A":
        change_type = "add"
    elif status == "D":
        change_type = "delete"

    entity_name = filename
    if new_data and "name" in new_data:
        entity_name = new_data["name"]
    elif old_data and "name" in old_data:
        entity_name = old_data["name"]

    diffs = []
    if old_data is not None and new_data is not None:
        ddiff = DeepDiff(old_data, new_data, ignore_order=True)

        # Map DeepDiff output to The Grimoire's slim patch format
        if "dictionary_item_added" in ddiff:
            items_added = ddiff["dictionary_item_added"]
            # Depending on DeepDiff version, this might be a set of paths or a dict of path:value
            if isinstance(items_added, dict):
                for path, val in items_added.items():
                    diffs.append({"kind": "N", "path": _map_path_to_array(path), "rhs": val})
            else:
                for path in items_added:
                    # We have to extract the value from new_data using the mapped path
                    mapped_path = _map_path_to_array(path)
                    val = new_data
                    for key in mapped_path:
                        val = val[key]
                    diffs.append({"kind": "N", "path": mapped_path, "rhs": val})

        if "dictionary_item_removed" in ddiff:
            items_removed = ddiff["dictionary_item_removed"]
            if isinstance(items_removed, dict):
                for path, val in items_removed.items():
                    diffs.append({"kind": "D", "path": _map_path_to_array(path), "lhs": val})
            else:
                for path in items_removed:
                    mapped_path = _map_path_to_array(path)
                    val = old_data
                    for key in mapped_path:
                        val = val[key]
                    diffs.append({"kind": "D", "path": mapped_path, "lhs": val})

        if "values_changed" in ddiff:
            for path, change in ddiff["values_changed"].items():
                # Sometimes comparing full dict to empty dict causes values_changed for the whole root
                if path in ("root", ""):
                    # If this happens, it means the whole object was added/deleted/changed.
                    # We should handle it at the dictionary level above, but if it surfaces here:
                    if status == "A":
                        for k, v in change["new_value"].items():
                            diffs.append({"kind": "N", "path": [k], "rhs": v})
                    elif status == "D":
                        for k, v in change["old_value"].items():
                            diffs.append({"kind": "D", "path": [k], "lhs": v})
                    continue

                diffs.append(
                    {
                        "kind": "E",
                        "path": _map_path_to_array(path),
                        "lhs": change["old_value"],
                        "rhs": change["new_value"],
                    }
                )
        if "iterable_item_added" in ddiff:
            for path, val in ddiff["iterable_item_added"].items():
                diff_path = _map_path_to_array(path)
                # For arrays, The Grimoire expects {kind: 'A', path: array_path, index: idx, item: {}}
                idx = diff_path.pop()  # Last item is the index
                diffs.append({"kind": "A", "path": diff_path, "index": idx, "item": {"kind": "N", "rhs": val}})
        if "iterable_item_removed" in ddiff:
            for path, val in ddiff["iterable_item_removed"].items():
                diff_path = _map_path_to_array(path)
                idx = diff_path.pop()
                diffs.append({"kind": "A", "path": diff_path, "index": idx, "item": {"kind": "D", "lhs": val}})

    # For additions and modifications, create/update timeline baseline snapshot
    if status in ("A", "M") and new_data:
        _create_timeline_baseline(filepath, current_version, new_data)

    return {
        "name": entity_name,
        "category": category,
        "change_type": change_type,
        "diffs": diffs,
        "field": "entity",
        "target_id": filename,
    }


def main():
    print("Generating patches from recent changes...")

    # Run Schema Validation First
    try:
        print("Running schema validation...")
        # validate_schemas checks everything and calls sys.exit(1) on failure
        # To avoid the script dying here, we run it as a subprocess
        res = subprocess.run(
            [sys.executable, os.path.join(config.BASE_DIR, "scripts", "validate_schemas.py")], check=False
        )
        if res.returncode != 0:
            print("Validation failed. Aborting patch generation.")
            sys.exit(1)
    except Exception as e:
        print(f"Validation error: {e}")
        sys.exit(1)

    # Get changes
    changed = get_git_diff_files()
    if not changed:
        print("No data files changed.")
        return

    # Read game config for current version
    game_config = load_json(GAME_CONFIG_PATH)
    if not game_config:
        print("Error reading game config.")
        return

    current_version = game_config.get("version", "0.0.1")

    # Load patches
    patches = load_json(PATCHES_FILE) or []

    # Legacy strip: remove "diff" key from all patches (one-time migration)
    _dirty = False
    for p in patches:
        if "diff" in p:
            del p["diff"]
            _dirty = True
    if _dirty:
        save_json(PATCHES_FILE, patches)
        print("Stripped legacy 'diff' keys from patches.json")

    # Get commit author for contributor attribution
    author = get_commit_author()
    contributor_tag = f"contributor:{author}" if author else None
    if author:
        print(f"Contributor: {author}")

    # Process changes
    new_changes = []
    for status, filepath in changed:
        # Ignore patches.json, game_config.json, queue.json
        exclude = ("data/patches.json", "data/game_config.json", "data/queue.json", "data/audit.jsonl")
        if filepath in exclude:
            continue

        change = generate_slim_change(filepath, status, current_version)
        if change:
            new_changes.append(change)

    if not new_changes:
        print("No patchable entity changes found.")
        return

    # Find existing patch block for this version, or create new
    target_patch = next((p for p in patches if p.get("version") == current_version), None)

    if target_patch:
        print(f"Appending {len(new_changes)} changes to existing patch {current_version}...")

        for c in new_changes:
            # Check for duplicate target (if someone edited same file multiple times)
            existing_idx = next(
                (i for i, existing in enumerate(target_patch["changes"]) if existing["target_id"] == c["target_id"]), -1
            )

            if existing_idx >= 0:
                target_patch["changes"][existing_idx] = c
            else:
                target_patch["changes"].append(c)

        target_patch["date"] = datetime.now(UTC).isoformat()

        # Add contributor tag if not already present
        if contributor_tag:
            existing_tags = set(target_patch.get("tags", []))
            existing_tags.add(contributor_tag)
            target_patch["tags"] = sorted(existing_tags)
    else:
        print(f"Creating new patch block for {current_version}...")
        target_patch = {
            "id": f"patch_{current_version.replace('.', '_')}",
            "version": current_version,
            "date": datetime.now(UTC).isoformat(),
            "type": "Content",  # Default
            "changes": new_changes,
            "tags": [contributor_tag] if contributor_tag else [],
            "title": f"Update {current_version}",
        }
        patches.insert(0, target_patch)

    save_json(PATCHES_FILE, patches)
    print("Saved patches.json")

    # Trigger static file builds
    print("Generating paginated changelogs...")
    try:
        build_changelogs.main()
    except Exception as e:
        print(f"Error building changelogs: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
