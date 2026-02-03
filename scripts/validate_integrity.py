import os
import json
import logging
import sys

# Configuration
DATA_DIR = 'data'
ASSETS_DIR = 'assets'
LOG_LEVEL = logging.INFO

# Setup Logging
# Configure logging to output to stdout to avoid buffering/interleaving issues
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def load_all_data():
    """Loads all JSON data into a dictionary keyed by category."""
    all_data = {}
    id_map = {} # Global map of "category:id" -> True for quick lookup
    
    if not os.path.exists(DATA_DIR):
        logging.error(f"Data directory '{DATA_DIR}' not found.")
        sys.exit(1)

    for category in os.listdir(DATA_DIR):
        category_path = os.path.join(DATA_DIR, category)
        if not os.path.isdir(category_path):
            continue

        all_data[category] = []
        files = [f for f in os.listdir(category_path) if f.endswith('.json')]
        
        for file in files:
            file_path = os.path.join(category_path, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data[category].append(data)
                    
                    # Add to ID Map
                    if 'id' in data:
                        # Map both specific category and generic lookup if needed
                        id_map[f"{category}:{data['id']}"] = True
                        
                        # Also handy to have just ID -> Category mapping for strict uniqueness checks if desired
                        # but for now we just want availability.
            except Exception as e:
                logging.error(f"Failed to load {file_path}: {e}")

    return all_data, id_map

def validate_integrity(all_data, id_map):
    """Checks for broken references."""
    errors = []

    # Helper to check existence
    def reference_exists(category, target_id):
        # Optimistic check: is it in the specific category?
        if f"{category}:{target_id}" in id_map:
            return True
        return False

    # 1. Validate Creatures
    for creature in all_data.get('creatures', []):
        cid = creature.get('id')
        
        # Check Drops
        for drop in creature.get('drops', []):
            item_id = drop.get('item_id')
            if item_id and not reference_exists('items', item_id):
                 errors.append(f"[Creature: {cid}] Drops unknown item: '{item_id}'")

    # 2. Validate Heroes
    for hero in all_data.get('heroes', []):
        hid = hero.get('id')
        
        # Check Abilities (Spells)
        for spell_id in hero.get('abilities', []):
            if not reference_exists('spells', spell_id):
                errors.append(f"[Hero: {hid}] Has unknown ability: '{spell_id}'")

        # Check Passive Skills (could be spells or upgrades, assumes upgrades for now based on context, or generic text)
        # If it's just text, we skip. If it matches an ID format, we warn? 
        # For now, let's assume strict checking if it looks like an ID.
        # skipping textual descriptions.

    # 3. Validate Upgrades
    for upgrade in all_data.get('upgrades', []):
        uid = upgrade.get('id')
        target = upgrade.get('target', '')
        
        # Parse Target: "Unit:orc_grunt" or "Spell:fireball"
        if ':' in target:
            t_type, t_id = target.split(':', 1)
            t_type = t_type.lower()
            
            valid_target = False
            if t_type == 'unit' or t_type == 'creature':
                 valid_target = reference_exists('creatures', t_id)
            elif t_type == 'spell':
                 valid_target = reference_exists('spells', t_id)
            elif t_type == 'hero':
                 valid_target = reference_exists('heroes', t_id)
            elif t_type == 'global':
                valid_target = True # Always valid
            else:
                 errors.append(f"[Upgrade: {uid}] Unknown target type: '{t_type}'")
                 continue

            if not valid_target and t_type != 'global':
                 errors.append(f"[Upgrade: {uid}] Targets unknown {t_type}: '{t_id}'")

    # 4. Check for Duplicate IDs globally (Optional but good practice)
    # This might be noisy if IDs are shared across categories (e.g. "fireball" spell and "fireball" scroll item)
    # So we skip global uniqueness for now, relying on category uniqueness.

    return errors

def validate_titans(all_data, id_map):
    """Specific validations for Titans."""
    errors = []
    for titan in all_data.get('titans', []):
        tid = titan.get('id')
        
        # Check Abilities (Strings for now, but if they reference spells later, we check here)
        # Current schema says abilities are strings. If they become IDs, we'd check spells.
        # For now, just a placeholder or basic check if needed.
        pass
    return errors

def validate_decks(all_data, id_map):
    """Specific validations for Decks."""
    errors = []
    
    # Helper to check existence
    def reference_exists(category, target_id):
        return f"{category}:{target_id}" in id_map

    for deck in all_data.get('decks', []):
        did = deck.get('id')
        
        # 1. Check Hero
        hero_id = deck.get('hero_id')
        if hero_id and not reference_exists('heroes', hero_id):
            errors.append(f"[Deck: {did}] Unknown Hero: '{hero_id}'")
            
        # 2. Check Titan
        titan_id = deck.get('titan_id')
        if titan_id and not reference_exists('titans', titan_id):
            errors.append(f"[Deck: {did}] Unknown Titan: '{titan_id}'")
            
        # 3. Check Cards (Creatures, Spells, Buildings)
        # Note: Cards can be from multiple categories. We need to check all unit/spell types.
        for card_id in deck.get('cards', []):
            found = False
            for cat in ['creatures', 'spells', 'buildings']:
                if reference_exists(cat, card_id):
                    found = True
                    break
            
            if not found:
                 errors.append(f"[Deck: {did}] Unknown Card (Unit/Spell/Building): '{card_id}'")

    return errors

def validate_assets(all_data):
    """Checks for missing or orphaned assets."""
    warnings = []
    
    # We expect assets/[category]/[id].png
    # 1. Check Missing Assets (Data exists -> Asset should exist)
    for category, items in all_data.items():
        asset_cat_dir = os.path.join(ASSETS_DIR, category)
        
        for item in items:
            item_id = item.get('id')
            if not item_id: continue
            
            # Check for PNG
            if item.get('image_required', False):
                png_path = os.path.join(asset_cat_dir, f"{item_id}.png")
                if not os.path.exists(png_path):
                    warnings.append(f"[Missing Asset] {category}/{item_id}.json has no corresponding image at {png_path}")

    return warnings

def validate_names(all_data):
    """Ensures no two items in the same category have the same name."""
    errors = []
    
    for category, items in all_data.items():
        seen_names = {}
        for item in items:
            name = item.get('name')
            item_id = item.get('id')
            if not name: continue
            
            if name in seen_names:
                prev_id = seen_names[name]
                errors.append(f"[Duplicate Name] '{name}' used by both {category}:{prev_id} and {category}:{item_id}")
            else:
                seen_names[name] = item_id
    
    return errors

def main():
    logging.info("Starting Integrity Validation...")
    
    all_data, id_map = load_all_data()
    logging.info(f"Loaded {sum(len(v) for v in all_data.values())} assets.")

    # 1. Integrity Checks (References)
    integrity_errors = validate_integrity(all_data, id_map)
    
    # 2. Name Uniqueness (Strict)
    name_errors = validate_names(all_data)
    
    all_errors = integrity_errors + name_errors + validate_titans(all_data, id_map) + validate_decks(all_data, id_map)

    # 3. Asset Checks (Warnings Only)
    asset_warnings = validate_assets(all_data)

    if asset_warnings:
        print("\nAsset Warnings (Non-Critical):")
        for w in asset_warnings:
            print(f" - {w}")
        sys.stdout.flush()

    if all_errors:
        logging.error("Validation Errors Found:")
        for e in all_errors:
            logging.error(f" - {e}")
        sys.exit(1)
    else:
        logging.info("Validation Complete. No critical issues found.")
        sys.exit(0)

if __name__ == "__main__":
    main()
