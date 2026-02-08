import json
import os
import glob
import sys
import jsonschema
from PIL import Image

# Configuration
SCHEMAS_DIR = "schemas/v1"
DATA_DIR = "data"
ASSETS_DIR = "assets"

# Asset Hygiene Limits
MAX_IMG_DIMENSION = 512
MAX_IMG_SIZE_KB = 100

# Schema Filenames
SCHEMA_FILES = {
    "incantation": "incantation.schema.json",
    "spellcaster": "spellcaster.schema.json",
    "consumable": "consumable.schema.json",
    "upgrade": "upgrade.schema.json",
    "deck": "deck.schema.json",
    "game_info": "game_info.schema.json",
    "titan": "titan.schema.json"
}

# Data Folder Mapping (Source -> Schema Type)
FOLDER_TO_SCHEMA = {
    "units": "incantation",
    "spells": "incantation",
    "titans": "titan",
    "spellcasters": "spellcaster",
    "consumables": "consumable",
    "upgrades": "upgrade",
    "decks": "deck" # if decks existed
}

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Invalid JSON in {path}: {e}")
        return None

def load_schema(name):
    path = os.path.join(SCHEMAS_DIR, SCHEMA_FILES[name])
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[FATAL] Could not load schema {name}: {e}")
        sys.exit(1)

def check_asset_exists(category, entity_id, is_required):
    """Checks if assets/[category]/[entity_id].png exists and validates hygiene. Returns warning count."""
    # Special handling for units/spells/titans/spellcasters
    # filename = f"{entity_id}.png"
    # if category in ["units", "spells", "titans", "spellcasters"]:
    #    filename = f"{entity_id}_card.png"
    
    # Unified Model - All assets are just {entity_id}.png or {entity_id}.webp
    # Prioritize WebP for production, but PNG is also valid.
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
    path = final_path
        
    # Asset Exists - Perform Hygiene Check
    try:
        # Check File Size
        size_kb = os.path.getsize(path) / 1024
        if size_kb > MAX_IMG_SIZE_KB:
            print(f"[WARN] Hygiene: {path} is {size_kb:.1f}KB (Max: {MAX_IMG_SIZE_KB}KB)")
            warnings += 1
            
        # Check Dimensions
        with Image.open(path) as img:
            width, height = img.size
            if width > MAX_IMG_DIMENSION or height > MAX_IMG_DIMENSION:
                 print(f"[WARN] Hygiene: {path} is {width}x{height} (Max: {MAX_IMG_DIMENSION}x{MAX_IMG_DIMENSION})")
                 warnings += 1
                 
    except Exception as e:
        print(f"[WARN] Could not validate image {path}: {e}")
        warnings += 1
        
    return warnings

def validate_decks(db):
    """
    Validates all deck files in data/decks.
    Returns a list of error strings.
    """
    errors = []
    # Support both data/decks.json and data/decks/*.json
    deck_files = glob.glob(os.path.join(DATA_DIR, "decks", "*.json"))
    if os.path.exists(os.path.join(DATA_DIR, "decks.json")):
        deck_files.append(os.path.join(DATA_DIR, "decks.json"))
    
    for f in deck_files:
        data = load_json(f)
        if not data:
            errors.append(f"[FAIL] Could not load deck {f}")
            continue

        spellcaster_id = data.get("spellcaster_id") or data.get("hero_id") # Support migration
        titan_id = data.get("titan_id")
        # In Unified Model, cards list contains unit_ids
        unit_ids = data.get("cards", [])

        # Spellcaster Check
        if spellcaster_id and spellcaster_id not in db["spellcasters"]:
            errors.append(f"[FAIL] Deck {f} references missing spellcaster_id '{spellcaster_id}'")
        
        # Titan Check
        if titan_id:
            if titan_id not in db["titans"]:
                errors.append(f"[FAIL] Deck {f} references missing titan_id '{titan_id}'")
            else:
                titan = db["titans"][titan_id]
                # Titan validation is implicit by being in titans DB

        # Cards Check (Units/Spells)
        has_rank_1_or_2_creature = False
        for uid in unit_ids:
            # Check in Units or Spells
            found = False
            entity = None
            
            if uid in db["units"]:
                entity = db["units"][uid]
                found = True
            elif uid in db["spells"]:
                entity = db["spells"][uid]
                found = True
            
            if not found:
                errors.append(f"[FAIL] Deck {f} references missing card '{uid}'")
            else:
                rank = entity.get("rank")
                category = entity.get("category")
                if category == "Creature" and rank in ["I", "II"]:
                    has_rank_1_or_2_creature = True

        if not has_rank_1_or_2_creature:
            errors.append(f"[FAIL] Deck {f} must contain at least one Rank I or Rank II CREATURE card.")

    return errors

def validate_integrity():
    print("Starting Integrity Validation...")
    errors = 0
    warnings = 0
    
    # 1. Load All Data for Cross-Reference
    db = {
        "units": {},
        "spells": {},
        "titans": {},
        "spellcasters": {},
        "consumables": {},
        "upgrades": {}
    }
    
    # Pre-load DB
    for key in db.keys():
        files = glob.glob(os.path.join(DATA_DIR, key, "*.json"))
        for f in files:
            data = load_json(f)
            if not data: continue
            
            # Identify ID field based on type
            id_field = "id" # default fallback
            if key in ["units", "spells", "titans"]: id_field = "entity_id"
            elif key == "spellcasters": id_field = "spellcaster_id"
            elif key == "consumables": id_field = "entity_id"
            elif key == "upgrades": id_field = "upgrade_id"
            
            if id_field in data:
                db[key][data[id_field]] = data

    # 2. Iterate and Validate
    schemas = {}
    for k, v in SCHEMA_FILES.items():
        schemas[k] = load_schema(k)

    # Validate Folders
    for folder, schema_key in FOLDER_TO_SCHEMA.items():
        print(f"Validating {folder}...")
        files = glob.glob(os.path.join(DATA_DIR, folder, "*.json"))
        
        for f in files:
            data = load_json(f)
            if not data:
                errors += 1
                continue

            # Schema Validation
            try:
                jsonschema.validate(instance=data, schema=schemas[schema_key])
            except jsonschema.ValidationError as e:
                print(f"[FAIL] Schema Error in {f}: {e.message}")
                errors += 1
                continue
            
            # Asset Check
            if data.get("image_required", True):
                # deduce ID
                obj_id = ""
                if schema_key == "incantation": obj_id = data.get("entity_id")
                elif schema_key == "titan": obj_id = data.get("entity_id")
                elif schema_key == "spellcaster": obj_id = data.get("spellcaster_id")
                elif schema_key == "consumable": obj_id = data.get("entity_id")
                
                if obj_id:
                    warnings += check_asset_exists(folder, obj_id, True)
            
            # Logic: Upgrade -> Tags
            if schema_key == "upgrade":
                targets = data.get("target_tags", [])
                # Collect all unique tags in DB
                all_tags = set()
                for u in db["units"].values():
                    for t in u.get("tags", []): all_tags.add(t)
                
                for t in targets:
                    if t not in all_tags:
                        print(f"[WARN] Upgrade {f} targets tag '{t}' which no unit possesses.")
                        warnings += 1

    # 3. Dedicated Deck Validation
    deck_errors = validate_decks(db)
    for e in deck_errors:
        print(e)
    errors += len(deck_errors)

    # Validate Game Info
    game_info_path = os.path.join(DATA_DIR, "game_info.json")
    if os.path.exists(game_info_path):
        data = load_json(game_info_path)
        try:
            jsonschema.validate(instance=data, schema=schemas["game_info"])
        except jsonschema.ValidationError as e:
            print(f"[FAIL] Game Info Schema Error: {e.message}")
            errors += 1
            
    print(f"Validation Complete. Errors: {errors}, Warnings: {warnings}")
    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    validate_integrity()
