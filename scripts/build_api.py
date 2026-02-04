import json
import os
import glob
import sys
import hashlib

# Configuration
VERSION_API = "v1"
OUTPUT_DIR = f"api/{VERSION_API}"
DATA_DIR = "data"

# Schema to Data Directory Map
# Output FilenameBase -> Source Directory
AGGREGATION_MAP = {
    "units": "units",
    "heroes": "heroes",
    "consumables": "consumables",
    "upgrades": "upgrades"
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
            "generated_at": None # Could add timestamp
        }
    }

    # Aggregate Collections
    for key, folder in AGGREGATION_MAP.items():
        print(f"Aggregating {key} from data/{folder}...")
        collection = []
        source_path = os.path.join(DATA_DIR, folder)
        
        if not os.path.exists(source_path):
            print(f"[WARN] Directory not found: {source_path}")
            all_data[key] = []
            continue

        files = glob.glob(os.path.join(source_path, "*.json"))
        for file in files:
            content = load_json(file)
            if content:
                collection.append(content)
        
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
            print(f"[WARN] File not found: {path}")

    # Save Master File
    save_json("all_data.json", all_data)
    print("Build Complete.")

if __name__ == "__main__":
    main()
