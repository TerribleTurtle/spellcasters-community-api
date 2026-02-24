"""
Shared utility functions for patch and audit generation scripts.
"""

import json
import os
import re
import subprocess

from deepdiff import DeepDiff


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


def get_file_content_at_commit(filepath, commit_hash):
    """Fetches the JSON content of a file at a specific Git commit."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit_hash}:{filepath}"], capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except Exception:
        return None


def _parse_deepdiff_path(path):
    """Parses a DeepDiff path string like root['stats']['attack'] or root['tags'][0]
    into a clean list of keys: ['stats', 'attack'] or ['tags', 0]."""
    matches = re.findall(r"\['([^']+)'\]|\[(\d+)\]", path)
    return [m[0] if m[0] else int(m[1]) for m in matches]


def compute_diff(old_data, new_data):
    """Computes a DeepDiff and formats it."""
    if old_data is None and new_data is None:
        return []

    # Exclude last_modified from diffing so we don't get noisy patch notes just for timestamp bumps
    diff = DeepDiff(old_data or {}, new_data or {}, ignore_order=True, exclude_paths=["root['last_modified']"])
    diffs = []

    if "dictionary_item_added" in diff:
        for path in diff["dictionary_item_added"]:
            keys = _parse_deepdiff_path(path)
            try:
                val = eval("new_data" + path.replace("root", ""))
            except Exception:
                val = "[Complex Value]"
            diffs.append({"path": keys, "new_value": val})

    if "dictionary_item_removed" in diff:
        for path in diff["dictionary_item_removed"]:
            keys = _parse_deepdiff_path(path)
            diffs.append({"path": keys, "removed": True})

    if "values_changed" in diff:
        for path, change in diff["values_changed"].items():
            keys = _parse_deepdiff_path(path)
            if not keys:
                # Root-level change (e.g. {} -> {full dict}). Decompose into per-key diffs.
                old_val = change.get("old_value", {})
                new_val = change.get("new_value", {})
                if isinstance(new_val, dict) and isinstance(old_val, dict):
                    # Recursively diff the actual content
                    for k in set(list(new_val.keys()) + list(old_val.keys())):
                        if k == "last_modified":
                            continue
                        if k in new_val and k not in old_val:
                            diffs.append({"path": [k], "new_value": new_val[k]})
                        elif k in old_val and k not in new_val:
                            diffs.append({"path": [k], "removed": True})
                        elif old_val.get(k) != new_val.get(k):
                            diffs.append({"path": [k], "old_value": old_val[k], "new_value": new_val[k]})
                else:
                    diffs.append({"path": keys, "old_value": change["old_value"], "new_value": change["new_value"]})
            else:
                diffs.append({"path": keys, "old_value": change["old_value"], "new_value": change["new_value"]})

    if "type_changes" in diff:
        for path, change in diff["type_changes"].items():
            keys = _parse_deepdiff_path(path)
            diffs.append({"path": keys, "old_value": change["old_value"], "new_value": change["new_value"]})

    if "iterable_item_added" in diff:
        for path, val in diff["iterable_item_added"].items():
            keys = _parse_deepdiff_path(path)
            diffs.append({"path": keys, "new_value": val})

    if "iterable_item_removed" in diff:
        for path, val in diff["iterable_item_removed"].items():
            keys = _parse_deepdiff_path(path)
            diffs.append({"path": keys, "removed": True, "old_value": val})

    return diffs
