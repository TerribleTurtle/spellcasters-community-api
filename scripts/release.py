import json
import os
import sys
import re
from datetime import datetime, timezone
import config

DATA_DIR = config.DATA_DIR
GAME_CONFIG_PATH = os.path.join(DATA_DIR, "game_config.json")
CHANGELOG_PATH = os.path.join(config.BASE_DIR, "CHANGELOG.md")


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def bump_version(current_version, bump_type):
    parts = current_version.split('.')
    if len(parts) != 3:
        print(f"Warning: Current version '{current_version}' doesn't follow SemVer X.Y.Z. "
              "Resetting to 0.0.1 if failed.")
        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            major, minor, patch = 0, 0, 0
    else:
        major, minor, patch = map(int, parts)

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1

    return f"{major}.{minor}.{patch}"


def main():  # pylint: disable=too-many-statements
    if not os.path.exists(GAME_CONFIG_PATH):
        print(f"Error: {GAME_CONFIG_PATH} not found.")
        sys.exit(1)

    data = load_json(GAME_CONFIG_PATH)
    current_version = data.get("version", "0.0.1")
    print(f"Current Version: {current_version}")

    bump_type = input("Bump type (major/minor/patch): ").strip().lower()
    if bump_type not in ['major', 'minor', 'patch']:
        print("Invalid bump type. Aborting.")
        sys.exit(1)

    new_version = bump_version(current_version, bump_type)
    print(f"New Version: {new_version}")

    print("Enter release notes (multiline, press Ctrl+Z then Enter on Windows to finish):")
    try:
        notes_lines = sys.stdin.readlines()
    except EOFError:
        notes_lines = []

    notes = "".join(notes_lines).strip()

    if not notes:
        print("Release notes cannot be empty. Aborting.")
        sys.exit(1)

    # 1. Update Game Config JSON
    data["version"] = new_version

    new_entry = {
        "version": new_version,
        "date": datetime.now(timezone.utc).isoformat(),
        "description": notes
    }

    if "changelog" not in data:
        data["changelog"] = []

    # Prepend new entry
    data["changelog"].insert(0, new_entry)
    save_json(GAME_CONFIG_PATH, data)
    print(f"\n[OK] Updated {GAME_CONFIG_PATH}")

    # 2. Update CHANGELOG.md
    today = datetime.now().strftime("%Y-%m-%d")
    changelog_entry = f"## [{new_version}] - {today}\n\n{notes}\n\n"

    content = ""
    if os.path.exists(CHANGELOG_PATH):
        with open(CHANGELOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        print(f"[INFO] Creating new {CHANGELOG_PATH}")

    # Insert logic: Find first version header "## [", insert before it.
    match = re.search(r'^## \[', content, re.MULTILINE)

    new_content = ""
    if match:
        new_content = content[:match.start()] + changelog_entry + content[match.start():]
    else:
        # If no versions exist yet, append after header or at end
        header_match = re.search(r'^# Changelog.*$', content, re.MULTILINE)
        if header_match:
            end_pos = header_match.end()
            # Ensure proper spacing
            new_content = content[:end_pos] + "\n\n" + changelog_entry + content[end_pos:].lstrip()
        else:
            # Just append if structure is unrecognizable
            new_content = content + "\n\n" + changelog_entry

    with open(CHANGELOG_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Updated {CHANGELOG_PATH}")
    print(f"Release {new_version} completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
