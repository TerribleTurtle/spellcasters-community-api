import json
import os


def load_json(path):
    """Safely loads a JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None


def load_timeline(entity_id, timeline_dir):
    """
    Loads timeline data for an entity.
    Returns a list of snapshot dicts sorted by version (assumes existing timelines are sorted),
    or an empty list if no timeline exists.
    """
    path = os.path.join(timeline_dir, f"{entity_id}.json")
    data = load_json(path)
    if isinstance(data, list):
        return data
    return []


def resolve_entity_id(entity_data):
    """
    Returns the unique identifier for an entity dict.
    Upgrades use 'upgrade_id', everything else uses 'entity_id'.
    """
    if not isinstance(entity_data, dict):
        return None
    return entity_data.get("entity_id") or entity_data.get("upgrade_id")


def extract_field(snapshot, dotted_path):
    """
    Safely resolves a nested field path like 'abilities.primary.damage' from a snapshot.
    Returns None if any step in the path is missing.
    """
    current = snapshot
    parts = dotted_path.split(".")
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def compute_stat_diff(old_snap, new_snap, tracked_fields):
    """
    Compares two snapshots based on a strict whitelist of tracked fields.
    Returns a list of dicts: [{'field': 'health', 'old': 100, 'new': 120}, ...]
    Omits fields that have not changed.
    """
    changes = []

    # We diff the actual entity payload stored under 'snapshot' key
    old_data = old_snap.get("snapshot", {})
    new_data = new_snap.get("snapshot", {})

    for field in tracked_fields:
        old_val = extract_field(old_data, field)
        new_val = extract_field(new_data, field)

        if old_val != new_val:
            changes.append({"field": field, "old": old_val, "new": new_val})

    return changes


def build_entity_stat_changes(entity_id, timeline_dir, tracked_fields):
    """
    Orchestrates diff generation across a full timeline.
    Returns a list of version diffs: [{'version': '0.0.2', 'date': '...', 'changes': [...]}]
    Returns an empty list if there are < 2 versions, or if no tracked changes occurred.
    """
    timeline = load_timeline(entity_id, timeline_dir)
    if not timeline or len(timeline) < 2:
        return []

    version_diffs = []

    # Compare consecutive pairs (start from second version)
    for i in range(1, len(timeline)):
        old_snap = timeline[i - 1]
        new_snap = timeline[i]

        changes = compute_stat_diff(old_snap, new_snap, tracked_fields)
        if changes:
            version_diffs.append({"version": new_snap.get("version"), "date": new_snap.get("date"), "changes": changes})

    return version_diffs
