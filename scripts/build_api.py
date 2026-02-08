import json
import os
import glob
import sys
import hashlib
from datetime import datetime, timezone

# Configuration
VERSION_API = "v1"
OUTPUT_DIR = f"api/{VERSION_API}"
DATA_DIR = "data"

# Schema to Data Directory Map
# Output FilenameBase -> Source Directory
AGGREGATION_MAP = {
    "spellcasters": "spellcasters",
    "consumables": "consumables",
    "upgrades": "upgrades",
    "units": "units",
    "spells": "spells",
    "titans": "titans"
}

# Single File Copy
SINGLE_FILES = {
    "game_info": "game_info.json"
}

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        return None

def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"[OK] Generated {path} ({len(data)} items)")

def generate_checksum(data):
    """Generates a simple hash for versioning/checking."""
    s = json.dumps(data, sort_keys=True)
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def main():
    print(f"Building API {VERSION_API}...")
    ensure_output_dir()
    
    all_data = {
        "build_info": {
            "version": "0.0.1",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
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
            if content:
                collection.append(content)
            else:
                errors += 1
        
        # Save individual aggregation
        save_json(f"{key}.json", collection)
        all_data[key] = collection

    # Process Single Files
    for key, filename in SINGLE_FILES.items():
        print(f"Processing {key}...")
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            content = load_json(path)
            if content:
                save_json(f"{key}.json", content)
                all_data[key] = content
            else:
                errors += 1
        else:
            print(f"[WARN] File not found: {path}")
            # Optional file missing is not always a critical error depending on logic,
            # but usually single files are expected.
            # strict mode: errors += 1 (?) -> Let's keep it as warn for now unless critical.


    # Save Master File
    save_json("all_data.json", all_data)
    
    if errors > 0:
        print(f"[FAIL] Build failed with {errors} errors.")
        sys.exit(1)
        
    print("Build Complete.")

if __name__ == "__main__":
    main()
