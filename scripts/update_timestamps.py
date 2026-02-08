
import json
import sys
import os
import subprocess
from datetime import datetime, timezone

def get_git_modified_files():
    """Returns a list of modified JSON files from git status."""
    files = []
    try:
        # Check for modified (M) or added (A) files in porcelain mode
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            # line format: "XY path/to/file"
            # X = staged status, Y = unstaged status
            status = line[:2]
            path = line[3:].strip()
            
            # Use strict loose comparison for M/A in either staged or unstaged
            if path.endswith('.json') and any(c in 'MA' for c in status):
                 files.append(os.path.abspath(path))
    except Exception as e:
        print(f"[WARN] Could not check git status: {e}")
    return files

def update_timestamp(file_path):
    """Updates the last_modified field in the JSON file."""
    try:
        if not os.path.exists(file_path):
            print(f"[SKIPPING] File not found: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        now = datetime.now(timezone.utc).isoformat()
        
        # Check if last_modified is already up to date (minute precision check?)
        # Actually, just update it.
        
        # Only update if the file actually has the field or if we want to enforce it?
        # MIGRATION SPEC says game_version is removed, last_modified is standard.
        # But let's check if 'last_modified' usually exists.
        
        old_ts = data.get('last_modified')
        data['last_modified'] = now
        
        # Changelog Logic? 
        # The user's deploy.yml comment said: "update last_modified timestamps".
        # It did NOT say "add changelog entry".
        # So we only touch last_modified.

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            # Add trailing newline for git hygiene
            f.write('\n')
            
        print(f"[UPDATED] {file_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to update {file_path}: {e}")
        return False

def main():
    files = sys.argv[1:]
    
    if not files:
        print("No files provided. Checking git status for modified JSON files...")
        files = get_git_modified_files()
        if not files:
            print("No modified JSON files found.")
            return

    print(f"Updating timestamps for {len(files)} files...")
    count = 0
    for f in files:
        if update_timestamp(f):
            count += 1
            
    print(f"Done. Updated {count} files.")

if __name__ == "__main__":
    main()
