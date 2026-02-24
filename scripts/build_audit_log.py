import json
import os
import subprocess
import sys

from patch_utils import get_file_content_at_commit, compute_diff
import config

# Strict exclusion list for data files that aren't "entities"
EXCLUDED_FILES = {
    "data/game_config.json",
    "data/patches.json",
    "data/queue.json",
    "data/audit.json",
    "data/changelog.json",
    "data/changelog_index.json",
    "data/changelog_latest.json",
}

def is_entity_file(filepath):
    if not filepath.startswith("data/"):
        return False
    if not filepath.endswith(".json"):
        return False
    if filepath.replace("\\", "/") in EXCLUDED_FILES:
        return False
    
    # Must be in a category folder, like data/units/ogre.json
    parts = filepath.replace("\\", "/").split('/')
    if len(parts) < 3:
        return False
    return True

def parse_git_log():
    """
    Runs git log to get all commits touching the data/ folder, newest first.
    Returns a list of commit dicts:
    [{'commit': hash, 'timestamp': ts, 'author': name, 'message': msg, 'files': [(status, path), ...]}, ...]
    """
    cmd = [
        "git", "log", "--no-merges", 
        "--name-status", "--format=COMMIT|%H|%aI|%aN|%s", "--", "data/"
    ]
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=config.BASE_DIR)
        output = process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git log: {e}")
        return []

    commits = []
    current_commit = None

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("COMMIT|"):
            parts = line.split("|", 4)
            if len(parts) == 5:
                current_commit = {
                    "commit": parts[1],
                    "timestamp": parts[2],
                    "author": parts[3],
                    "message": parts[4],
                    "files": []
                }
                commits.append(current_commit)
        elif current_commit:
            # File status line, e.g. "M\tdata/units/ogre.json"
            parts = line.split("\t")
            if len(parts) >= 2:
                status = parts[0]
                filepath = parts[-1]  # Renames have 3 parts (status, old, new), we just want the latest path
                if is_entity_file(filepath):
                    current_commit["files"].append((status, filepath))
                    
    # Filter out commits that only touched excluded files (files list is empty)
    return [c for c in commits if c["files"]]

def build_audit_log():
    print("Building commit-level audit log...")
    commits = parse_git_log()
    print(f"Found {len(commits)} data commits to process.")
    
    audit_entries = []
    
    for c in commits:
        commit_hash = c["commit"]
        changes = []
        
        for status, filepath in c["files"]:
            status_char = status[0].upper()
            
            # Extract category and entity
            parts = filepath.split('/')
            category = parts[1]
            entity_id = os.path.splitext(os.path.basename(filepath))[0]
            
            # Fetch old and new data
            if status_char == 'A':
                # Added file, no old data
                old_data = None
                new_data = get_file_content_at_commit(filepath, commit_hash)
                change_type = "add"
            elif status_char == 'D':
                # Deleted file, no new data
                old_data = get_file_content_at_commit(filepath, f"{commit_hash}~1")
                new_data = None
                change_type = "delete"
            else:
                # Modified or Renamed, need both (using robust parent ~1)
                # Note: If this modifies a file in the FIRST commit of a repo, ~1 will fail, 
                # get_file_content_at_commit swallows the error and returns None.
                old_data = get_file_content_at_commit(filepath, f"{commit_hash}~1")
                new_data = get_file_content_at_commit(filepath, commit_hash)
                change_type = "edit" if status_char == 'M' else "rename"
                
            # If both are None, skip (maybe file deletion was actually a folder or corrupted json)
            if old_data is None and new_data is None:
                continue
                
            # Compute granular diff
            diffs = compute_diff(old_data, new_data)
            
            if diffs or change_type in ("add", "delete"):
                changes.append({
                    "entity_id": entity_id,
                    "file": filepath,
                    "category": category,
                    "change_type": change_type,
                    "diffs": diffs
                })
                
        # Only add the commit to the audit log if there are actual entity changes
        if changes:
            entry = {
                "commit": commit_hash,
                "timestamp": c["timestamp"],
                "author": c["author"],
                "message": c["message"],
                "changes": changes
            }
            audit_entries.append(entry)
            
    # Output to flat audit.json in repo root (minified)
    output_path = os.path.join(config.BASE_DIR, "audit.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audit_entries, f, separators=(',', ':'))
        
    print(f"Audit log generated: {output_path} ({len(audit_entries)} commits)")

def main():
    build_audit_log()

if __name__ == "__main__":
    main()
