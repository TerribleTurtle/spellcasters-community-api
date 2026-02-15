import json
import os
import glob
import sys
from PIL import Image
import config
from pathlib import Path

# Try to import modern JSON schema libraries
try:
    from jsonschema import validators, ValidationError
    from referencing import Registry, Resource
except ImportError:
    print("CRITICAL: 'jsonschema' (>=4.18) or 'referencing' library not found.")
    sys.exit(1)

"""
Data Integrity Validator

This script performs strict validation on the project data:
1. Schema Validation: Checks all JSON files against schemas in `schemas/v2/`.
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

CACHE_FILE = ".asset_cache.json"

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[FATAL] Could not load JSON {filepath}: {e}")
        return None

def create_registry(schemas_dir):
    """
    Creates a referencing.Registry populated with all schemas from the directory.
    Returns: (registry, schemas_map) where schemas_map maps filename -> URI.
    """
    registry = Registry()
    schemas_map = {}
    
    # Walk all files, preserving structure
    for root, _, files in os.walk(schemas_dir):
        for file in files:
            if file.endswith(".json"): # simple and schema.json
                path = Path(os.path.join(root, file))
                try:
                    schema = load_json(path)
                    if not schema: continue
                    
                    resource = Resource.from_contents(schema)
                    
                    # Register by absolute URI (standard)
                    registry = registry.with_resource(path.as_uri(), resource)
                    
                    # Store filename lookup (e.g., "heroes.schema.json" -> URI)
                    schemas_map[file] = path.as_uri()
                    
                    # Store relative key lookup (e.g., "definitions/core.schema.json")
                    # This helps map config keys to URIs
                    rel_key = os.path.relpath(path, schemas_dir).replace(os.sep, '/')
                    schemas_map[rel_key] = path.as_uri()
                    
                except Exception as e:
                    print(f"Error loading schema {file}: {e}")
    
    return registry, schemas_map

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
                # Cache Hit - Return stored valid state
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
    if schema_key in ["unit", "spell", "titan", "consumable"]:
        obj_id = data.get("entity_id")
    elif schema_key == "hero":
        obj_id = data.get("entity_id", data.get("spellcaster_id")) 
    
    if obj_id:
        return check_asset_exists(folder, obj_id, True, cache)
    return 0



def validate_integrity():
    """
    Main validation routine.
    """
    print("Starting Integrity Validation (Robust Mode)...")
    errors = 0
    warnings = 0
    
    # 1. Load All Data
    db = {}
    cache = load_cache()
    
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
            db[folder][f] = data

    # 2. Build Schema Registry
    print("Building Schema Registry...")
    registry, schemas_map = create_registry(SCHEMAS_DIR)
    
    # 3. Pre-calculate Global Sets
    print("Building reference indices...")
    all_game_tags = set()
    if "units" in db:
        for f, u in db["units"].items():
            for t in u.get("tags", []): 
                all_game_tags.add(t)

    # 4. Iterate and Validate
    for folder, schema_key in FOLDER_TO_SCHEMA.items():
        print(f"Validating {folder}...")
        
        if folder not in db: continue
        
        # Get target schema URI
        # Config uses simple keys. We need to map them to filenames -> URIs.
        # SCHEMA_FILES maps 'hero' -> 'heroes.schema.json'
        filename = SCHEMA_FILES.get(schema_key)
        if not filename:
            print(f"[WARN] No schema config found for key {schema_key}")
            continue
            
        target_uri = schemas_map.get(filename)
        if not target_uri:
            print(f"[FATAL] Schema file {filename} not found in registry.")
            errors += 1
            continue

        # Prepare Validator
        resolver = registry.resolver()
        resolved_schema = resolver.lookup(target_uri)
        schema_obj = resolved_schema.contents
        
        # Inject $id if missing for relative resolution
        if "$id" not in schema_obj:
            schema_obj["$id"] = target_uri

        ValidatorClass = validators.validator_for(schema_obj)
        validator = ValidatorClass(schema_obj, registry=registry)

        for filepath, data in db[folder].items():
            # Schema Validation
            try:
                validator.validate(data)
            except ValidationError as e:
                print(f"[FAIL] Schema Error in {os.path.basename(filepath)}: {e.message}")
                print(f"  -> Path: {e.json_path}")
                errors += 1
            except Exception as e:
                print(f"[FAIL] validation exception {os.path.basename(filepath)}: {e}")
                errors += 1
            
            # Asset Check
            warnings += validate_entry_assets(data, schema_key, folder, cache)
            
            # Logic: Upgrade -> Tags
            if schema_key == "upgrade":
                targets = data.get("target_tags", [])
                for t in targets:
                    if t not in all_game_tags:
                        print(f"[WARN] Upgrade {os.path.basename(filepath)} targets tag '{t}' which no unit possesses.")
                        warnings += 1



    # Validate Game Config
    game_config_path = os.path.join(DATA_DIR, "game_config.json")
    if os.path.exists(game_config_path):
        data = load_json(game_config_path)
        if data:
            uri = schemas_map.get("game_config.schema.json")
            if uri:
                try:
                    resolved = registry.resolver().lookup(uri)
                    s_obj = resolved.contents
                    if "$id" not in s_obj: s_obj["$id"] = uri
                    v = validators.validator_for(s_obj)(s_obj, registry=registry)
                    v.validate(data)
                except ValidationError as e:
                     print(f"[FAIL] Game Config Schema Error: {e.message}")
                     errors += 1

    # Save Cache
    save_cache(cache)
    
    print(f"Validation Complete. Errors: {errors}, Warnings: {warnings}")
    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    validate_integrity()
