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
    "unit": "unit.schema.json",
    "card": "card.schema.json",
    "hero": "hero.schema.json",
    "consumable": "consumable.schema.json",
    "upgrade": "upgrade.schema.json",
    "deck": "deck.schema.json",
    "game_info": "game_info.schema.json"
}

# Data Folder Mapping (Source -> Schema Type)
FOLDER_TO_SCHEMA = {
    "units": "unit",
    "cards": "card",
    "heroes": "hero",
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
    """Checks if assets/[category]/[entity_id].png exists and validates hygiene."""
    path = os.path.join(ASSETS_DIR, category, f"{entity_id}.png")
    
    if not os.path.exists(path):
        if is_required:
            print(f"[WARN] Missing Asset: {path}")
        return False # Missing
        
    # Asset Exists - Perform Hygiene Check
    try:
        # Check File Size
        size_kb = os.path.getsize(path) / 1024
        if size_kb > MAX_IMG_SIZE_KB:
            print(f"[WARN] Hygiene: {path} is {size_kb:.1f}KB (Max: {MAX_IMG_SIZE_KB}KB)")
            
        # Check Dimensions
        with Image.open(path) as img:
            width, height = img.size
            if width > MAX_IMG_DIMENSION or height > MAX_IMG_DIMENSION:
                 print(f"[WARN] Hygiene: {path} is {width}x{height} (Max: {MAX_IMG_DIMENSION}x{MAX_IMG_DIMENSION})")
                 
    except Exception as e:
        print(f"[WARN] Could not validate image {path}: {e}")
        
    return True

def validate_decks(db):
    """
    Validates all deck files in data/decks.
    Returns a list of error strings.
    """
    errors = []
    deck_files = glob.glob(os.path.join(DATA_DIR, "decks", "*.json"))
    
    for f in deck_files:
        data = load_json(f)
        if not data:
            errors.append(f"[FAIL] Could not load deck {f}")
            continue

        hero_id = data.get("hero_id")
        titan_id = data.get("titan_id")
        card_ids = data.get("cards", [])

        # Hero Check
        if hero_id and hero_id not in db["heroes"]:
            errors.append(f"[FAIL] Deck {f} references missing hero_id '{hero_id}'")
        
        # Titan Check
        if titan_id:
            if titan_id not in db["cards"]:
                errors.append(f"[FAIL] Deck {f} references missing titan_id '{titan_id}' (Card not found)")
            else:
                # Deep Check: Is it actually a Titan?
                titan_card = db["cards"][titan_id]
                titan_entity_id = titan_card.get("entity_id")
                
                if titan_entity_id not in db["units"]:
                        errors.append(f"[FAIL] Titan Card '{titan_id}' references missing entity '{titan_entity_id}'")
                else:
                    unit = db["units"][titan_entity_id]
                    if unit.get("category") != "Titan":
                        errors.append(f"[FAIL] Deck {f} titan_id '{titan_id}' is NOT a Titan (Category: {unit.get('category')})")
        
        # Cards Check
        for cid in card_ids:
            if cid not in db["cards"]:
                    errors.append(f"[FAIL] Deck {f} references missing card_id '{cid}'")
                    
    return errors

def validate_integrity():
    print("Starting Integrity Validation...")
    errors = 0
    warnings = 0
    
    # 1. Load All Data for Cross-Reference
    db = {
        "units": {},
        "cards": {},
        "heroes": {},
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
            if key == "units": id_field = "entity_id"
            elif key == "cards": id_field = "card_id"
            elif key == "heroes": id_field = "hero_id"
            elif key == "consumables": id_field = "consumable_id"
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
            # Mappings for asset folders: units->units, cards->cards, etc.
            if data.get("image_required", True):
                # deduce ID
                obj_id = ""
                if schema_key == "unit": obj_id = data.get("entity_id")
                elif schema_key == "card": obj_id = data.get("card_id")
                elif schema_key == "hero": obj_id = data.get("hero_id")
                elif schema_key == "consumable": obj_id = data.get("consumable_id")
                
                if obj_id:
                    check_asset_exists(folder, obj_id, True)

            # Logic: Card -> Unit Reference
            if schema_key == "card":
                entity_id = data.get("entity_id")
                if entity_id not in db["units"]:
                    # Is it a Neutral/Token/Spell? unit.schema handles all.
                    print(f"[FAIL] Orphan Card: {f} points to missing entity_id '{entity_id}'")
                    errors += 1
            
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
