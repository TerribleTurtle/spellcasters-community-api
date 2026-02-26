import glob
import json
import os
import subprocess
import sys
from datetime import UTC, datetime

import config
from patch_utils import compute_diff, get_file_content_at_commit, load_json, save_json

GAME_CONFIG_PATH = os.path.join(config.DATA_DIR, "game_config.json")
PATCHES_FILE = os.path.join(config.DATA_DIR, "patches.json")
TIMELINE_DIR = os.path.join(config.BASE_DIR, "timeline")


def discover_version_boundaries(current_version):
    """
    Walks git history of game_config.json to find the first commit of each version.
    Returns: list of dicts [{'version': '0.0.1', 'commit': 'abc1234'}, ...] oldest to newest.
    Only includes versions <= current_version to handle messy resets.
    """
    import subprocess

    boundaries = []
    seen_versions = set()

    try:
        from packaging.version import parse as parse_version

        curr_ver_parsed = parse_version(current_version)
        use_packaging = True
    except ImportError:
        use_packaging = False

    # Get all commits that touched game_config.json, oldest first
    try:
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%H", "data/game_config.json"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [c for c in result.stdout.strip().split("\n") if c]
    except subprocess.CalledProcessError:
        print("Warning: Could not read git history for game_config.json")
        return []

    for commit in commits:
        try:
            # Read game_config.json at that specific commit
            show = subprocess.run(
                ["git", "show", f"{commit}:data/game_config.json"], capture_output=True, text=True, check=True
            )
            data = json.loads(show.stdout)
            version = data.get("version")

            # Skip historical boundaries that are "ahead" of our current baseline
            if use_packaging:
                if parse_version(version) > curr_ver_parsed:
                    continue
            else:
                if version != current_version and version > current_version:
                    continue

            if version and version not in seen_versions:
                boundaries.append({"version": version, "commit": commit})
                seen_versions.add(version)
        except Exception:
            pass

    # Add a pseudo-boundary for the absolute initial commit (Big Bang) if we need a baseline before 0.0.1
    # Actually, 0.0.1 is our baseline. Changes in 0.0.1 are the baseline itself.
    return boundaries


def get_changed_files_between(before_sha, after_sha):
    """Gets all data/ files changed between two commits."""
    if not before_sha:
        return []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", before_sha, after_sha], capture_output=True, text=True, check=True
        )
        changed = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            status, filepath = parts[0], parts[1]
            if filepath.startswith("data/") and filepath.endswith(".json"):
                # Ignore core structural files
                if filepath not in (
                    "data/patches.json",
                    "data/game_config.json",
                    "data/queue.json",
                    "data/audit.jsonl",
                ):
                    changed.append((status, filepath))
        return changed
    except Exception as e:
        print(f"Git diff error: {e}")
        return []


def get_entity_files_at_commit(commit_hash):
    """Lists all entity data files (data/{folder}/*.json) at a specific git commit."""
    entity_files = []
    try:
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_hash, "data/"], capture_output=True, text=True, check=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line or not line.endswith(".json"):
                continue
            # Filter to entity folders only, skip structural files
            parts = line.split("/")
            if len(parts) >= 3 and parts[1] in config.FOLDER_TO_SCHEMA:
                entity_files.append(line)
    except Exception:
        pass
    return entity_files


def collect_timeline_snapshot(version, commit_hash, is_active):
    """Collects entity snapshots for a single version boundary.

    Returns a dict of {entity_id: {version, date, snapshot}} entries.
    For the active version, reads from disk. For historical versions, reads from git.
    """
    snapshots = {}
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    if is_active:
        # Active version: read from disk (most up-to-date)
        for folder in config.FOLDER_TO_SCHEMA.keys():
            src_dir = os.path.join(config.DATA_DIR, folder)
            if not os.path.exists(src_dir):
                continue
            for path in glob.glob(os.path.join(src_dir, "*.json")):
                data = load_json(path)
                if not data:
                    continue
                entity_id = os.path.splitext(os.path.basename(path))[0]
                snapshots[entity_id] = {"version": version, "date": date, "snapshot": data}
    else:
        # Historical version: read from git at the commit
        entity_files = get_entity_files_at_commit(commit_hash)
        for filepath in entity_files:
            data = get_file_content_at_commit(filepath, commit_hash)
            if not data:
                continue
            entity_id = os.path.splitext(os.path.basename(filepath))[0]
            snapshots[entity_id] = {"version": version, "date": date, "snapshot": data}

    return snapshots


def write_timeline_files(timeline_data):
    """Writes accumulated timeline data to disk.

    Args:
        timeline_data: dict of {entity_id: [snapshot_1, snapshot_2, ...]}
    """
    os.makedirs(TIMELINE_DIR, exist_ok=True)
    count = 0
    for entity_id, snapshots in timeline_data.items():
        timeline_path = os.path.join(TIMELINE_DIR, f"{entity_id}.json")
        save_json(timeline_path, snapshots)
        count += 1
    print(f"  Wrote {count} timeline files.")


def main():
    print("Stateless Patch Generation Pipeline")

    if not os.path.exists(GAME_CONFIG_PATH):
        print("Error: game_config.json not found.")
        sys.exit(1)

    game_config = load_json(GAME_CONFIG_PATH)
    current_version = game_config.get("version", "0.0.1")

    # Only recognize versions that exist in the official changelog
    official_versions = {entry["version"] for entry in game_config.get("changelog", [])}
    all_boundaries = discover_version_boundaries(current_version)
    boundaries = [b for b in all_boundaries if b["version"] in official_versions]

    # Timeline accumulator: {entity_id: [{version, date, snapshot}, ...]}
    timeline_data = {}

    if not boundaries:
        print("No version boundaries found in git. Assuming fresh start.")
        # Fresh start: snapshot current disk state as the only timeline entry
        snapshots = collect_timeline_snapshot(current_version, "HEAD", is_active=True)
        for entity_id, snap in snapshots.items():
            timeline_data[entity_id] = [snap]
        write_timeline_files(timeline_data)
        return

    print(f"Found {len(boundaries)} version boundaries in git logs.")

    patches = load_json(PATCHES_FILE) or []

    # Process each version from oldest to newest
    for i in range(len(boundaries)):
        version = boundaries[i]["version"]
        start_commit = boundaries[i]["commit"]

        # The end commit for this version is the start of the NEXT version,
        # or HEAD if it's the current active version.
        if i + 1 < len(boundaries):
            end_commit = boundaries[i + 1]["commit"] + "~1"
            is_active = False
        else:
            end_commit = "HEAD"
            is_active = True

        print(f"\nEvaluating Version {version} (Baseline: {start_commit} -> {end_commit})")

        # --- Timeline: Capture entity snapshots at every version (including 0.0.1 baseline) ---
        # Always use start_commit — it's the commit that introduced this version
        version_snapshots = collect_timeline_snapshot(version, start_commit, is_active)
        for entity_id, snap in version_snapshots.items():
            if entity_id not in timeline_data:
                timeline_data[entity_id] = []
            timeline_data[entity_id].append(snap)

        # --- Patch Generation: Skip 0.0.1 baseline and future versions ---
        patch_meta = next((p for p in patches if p.get("version") == version), None)
        if not patch_meta:
            if version == "0.0.1":
                print(f"  Skipping patch generation for {version} (initial baseline)")
                continue

            try:
                from packaging.version import parse as parse_version

                if parse_version(version) > parse_version(current_version):
                    print(f"  Skipping patch generation for {version} (ahead of current baseline {current_version})")
                    continue
            except ImportError:
                if version != current_version and version > current_version:
                    print(f"  Skipping patch generation for {version} (ahead of current baseline {current_version})")
                    continue

            patch_meta = {
                "id": f"patch_{version.replace('.', '_')}",
                "version": version,
                "date": datetime.now(UTC).isoformat()[:10],
                "type": "Patch",
                "title": f"Patch {version}",
                "tags": [],
            }
            patches.insert(0, patch_meta)

        # Compute dynamic diffs from baseline
        if i == 0:
            before_sha = None
        else:
            before_sha = boundaries[i - 1]["commit"]

        if not is_active and "changes" in patch_meta and len(patch_meta["changes"]) > 0:
            print(f"  Historical changes already exist for {version}, skipping computation.")
            continue

        if not before_sha:
            continue

        changed_files = get_changed_files_between(before_sha, end_commit)
        changes = []

        for status, filepath in changed_files:
            filename = os.path.basename(filepath)

            if status == "D":
                old_data = get_file_content_at_commit(filepath, before_sha)
                new_data = {}
                change_type = "delete"
            elif status == "A":
                old_data = {}
                if is_active:
                    new_data = load_json(os.path.join(config.BASE_DIR, filepath))
                else:
                    new_data = get_file_content_at_commit(filepath, end_commit)
                change_type = "add"
            else:
                old_data = get_file_content_at_commit(filepath, before_sha)
                if is_active:
                    new_data = load_json(os.path.join(config.BASE_DIR, filepath))
                else:
                    new_data = get_file_content_at_commit(filepath, end_commit)
                change_type = "edit"

            if not old_data and not new_data:
                continue

            diffs = compute_diff(old_data, new_data)
            if not diffs:
                continue

            source = new_data or old_data
            name = source.get("name", filename) if isinstance(source, dict) else filename
            cat = filepath.split("/")[1] if "data/" in filepath else "misc"

            changes.append(
                {
                    "target_id": filename,
                    "name": name,
                    "field": "entity",
                    "change_type": change_type,
                    "category": cat,
                    "diffs": diffs,
                }
            )

        patch_meta["changes"] = changes
        print(f"  Computed {len(changes)} changes for {version}")

    # Flush all outputs
    save_json(PATCHES_FILE, patches)
    print("\n  Writing timeline snapshots...")
    write_timeline_files(timeline_data)
    print("\nPatch generation complete.")


if __name__ == "__main__":
    main()
