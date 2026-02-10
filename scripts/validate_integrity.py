import json
import os
import glob
import sys
import jsonschema
from PIL import Image
import config
from config import load_json

"""
Data Integrity Validator

This script performs strict validation on the project data:
1. Schema Validation: Checks all JSON files against schemas in `schemas/v1/`.
2. Asset Hygiene: checks if required images exist and meet size/dimension limits.
3. Reference Integrity: Ensures logical consistency (e.g., Upgrade tags exist).
"""


# Configuration
SCHEMAS_DIR = config.SCHEMAS_DIR
DATA_DIR = config.DATA_DIR
ASSETS_DIR = config.ASSETS_DIR

# Asset Hygiene Limits
MAX_IMG_DIMENSION = config.MAX_IMG_DIMENSION
MAX_IMG_SIZE_KB = config.MAX_IMG_SIZE_KB

# Schema Filenames
SCHEMA_FILES = config.SCHEMA_FILES

# Data Folder Mapping (Source -> Schema Type)
FOLDER_TO_SCHEMA = config.FOLDER_TO_SCHEMA



def load_schema(name):
    """
    Loads a JSON schema by its friendly name key (e.g., 'incantation').

    Args:
        name (str): Key matching an entry in config.SCHEMA_FILES.

    Returns:
        dict: The parsed JSON schema.
    """
    path = os.path.join(SCHEMAS_DIR, SCHEMA_FILES[name])
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[FATAL] Could not load schema {name}: {e}")
        sys.exit(1)

CACHE_FILE = ".asset_cache.json"

def load_cache():
    """Loads the asset validation cache."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    """Saves the asset validation cache."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=0)
    except Exception as e:
        print(f"[WARN] Could not save cache: {e}")

def check_asset_exists(category, entity_id, is_required, cache):
    """Checks if assets/[category]/[entity_id].png exists and validates hygiene. Returns warning count."""
    warnings = 0
    
    path_webp = os.path.join(ASSETS_DIR, category, f"{entity_id}.webp")
    path_png = os.path.join(ASSETS_DIR, category, f"{entity_id}.png")
    
    final_path = None
    if os.path.exists(path_webp):
        final_path = path_webp
    elif os.path.exists(path_png):
        final_path = path_png
    
    if not final_path:
        if is_required:
            print(f"[WARN] Missing Asset: {path_webp} (or .png)")
            return 1
        return 0
        
    # Asset Exists - Perform Hygiene Check
    try:
        stat = os.stat(final_path)
        mtime = stat.st_mtime
        size = stat.st_size
        
        # Check Cache
        if final_path in cache:
            entry = cache[final_path]
            if entry.get("mtime") == mtime and entry.get("size") == size:
                # Cache Hit - Return stored valid state (assuming 0 warnings if cached)
                return 0

        # Cache Miss - Validate
        size_kb = size / 1024
        if size_kb > MAX_IMG_SIZE_KB:
            print(f"[WARN] Hygiene: {final_path} is {size_kb:.1f}KB (Max: {MAX_IMG_SIZE_KB}KB)")
            warnings += 1
            
        with Image.open(final_path) as img:
            width, height = img.size
            if width > MAX_IMG_DIMENSION or height > MAX_IMG_DIMENSION:
                 print(f"[WARN] Hygiene: {final_path} is {width}x{height} (Max: {MAX_IMG_DIMENSION}x{MAX_IMG_DIMENSION})")
                 warnings += 1

        # Update Cache only if valid (no warnings)
        if warnings == 0:
            cache[final_path] = {"mtime": mtime, "size": size}

    except Exception as e:
        print(f"[WARN] Could not validate image {final_path}: {e}")
        warnings += 1
        
    return warnings


def validate_entry_assets(data, schema_key, folder, cache):
    """Checks if required assets exist for a data entry. Returns warning count."""
    if not data.get("image_required", True):
        return 0

    # Deduce ID based on schema key
    obj_id = ""
    if schema_key == "incantation": obj_id = data.get("entity_id")
    elif schema_key == "titan": obj_id = data.get("entity_id")
    elif schema_key == "spellcaster": obj_id = data.get("spellcaster_id")
    elif schema_key == "consumable": obj_id = data.get("entity_id")
    
    if obj_id:
        return check_asset_exists(folder, obj_id, True, cache)
    return 0

def validate_integrity():
    """
    Main validation routine.
    
    Orchestrates the validation process:
    1. Loads all data into a memory DB for cross-reference.
    2. Validates each file against its JSON schema.
    3. Checks for missing or invalid assets.
    """
    print("Starting Integrity Validation...")
    errors = 0
    warnings = 0
    
    # 1. Load All Data for Cross-Reference & Validation
    db = {}
    cache = load_cache()
    
    # Pre-load DB dynamically based on config
    print("Loading data into memory...")
    for folder, schema_key in FOLDER_TO_SCHEMA.items():
        if folder not in db:
            db[folder] = {}
            
        path_pattern = os.path.join(DATA_DIR, folder, "*.json")
        files = glob.glob(path_pattern)
        
        for f in files:
            data = load_json(f)
            if not data: 
                errors += 1
                continue
            
            # Store with filename as key for easy reference logic, or ID?
            # Storing by filename for now to match old logic's ability to identify source
            db[folder][f] = data

    # 2. Pre-calculate Global Sets for O(1) Lookups
    print("Building reference indices...")
    all_game_tags = set()
    if "units" in db:
        for f, u in db["units"].items():
            for t in u.get("tags", []): 
                all_game_tags.add(t)

    # 3. Iterate and Validate (InMemory)
    schemas = {}
    for k, v in SCHEMA_FILES.items():
        schemas[k] = load_schema(k)

    # Validate Folders
    for folder, schema_key in FOLDER_TO_SCHEMA.items():
        print(f"Validating {folder}...")
        
        if folder not in db: continue
        
        for filepath, data in db[folder].items():
            # Schema Validation
            try:
                jsonschema.validate(instance=data, schema=schemas[schema_key])
            except jsonschema.ValidationError as e:
                print(f"[FAIL] Schema Error in {filepath}: {e.message}")
                errors += 1
                continue
            
            # Asset Check
            warnings += validate_entry_assets(data, schema_key, folder, cache)
            
            # Logic: Upgrade -> Tags (Optimized O(N))
            if schema_key == "upgrade":
                targets = data.get("target_tags", [])
                for t in targets:
                    if t not in all_game_tags:
                        print(f"[WARN] Upgrade {os.path.basename(filepath)} targets tag '{t}' which no unit possesses.")
                        warnings += 1


    # Validate Game Info
    game_info_path = os.path.join(DATA_DIR, "game_info.json")
    if os.path.exists(game_info_path):
        data = load_json(game_info_path)
        try:
            jsonschema.validate(instance=data, schema=schemas["game_info"])
        except jsonschema.ValidationError as e:
            print(f"[FAIL] Game Info Schema Error: {e.message}")
            errors += 1
            
    # Save Cache
    save_cache(cache)
    
    print(f"Validation Complete. Errors: {errors}, Warnings: {warnings}")
    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    validate_integrity()
