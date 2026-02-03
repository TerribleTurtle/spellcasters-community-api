import os
import json
import logging
import datetime

# Configuration
DATA_DIR = 'data'
OUTPUT_DIR = 'api/v1'
SCHEMA_DIR = 'schemas/v1'

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema library not found. Skipping strict schema validation. (pip install jsonschema)")

# Map categories to schema files
SCHEMA_MAP = {
    'creatures': 'creature.schema.json',
    'heroes': 'hero.schema.json',
    'buildings': 'building.schema.json',
    'spells': 'spell.schema.json',
    'titans': 'titan.schema.json',
    'items': 'item.schema.json',
    'upgrades': 'upgrade.schema.json',
    'decks': 'deck.schema.json',
    'game_info': 'game_info.schema.json'
}

def load_schema(schema_name):
    path = os.path.join(SCHEMA_DIR, schema_name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    aggregated_data = {}
    validation_failed = False

    logging.info(f"Starting build... Reading from {DATA_DIR}")

    # Walk through data folder
    for category in os.listdir(DATA_DIR):
        category_path = os.path.join(DATA_DIR, category)
        if not os.path.isdir(category_path):
            continue

        logging.info(f"Processing category: {category}")
        aggregated_data[category] = []
        
        # Load Schema if available
        schema_file = SCHEMA_MAP.get(category)
        schema = None
        if HAS_JSONSCHEMA and schema_file:
            schema = load_schema(schema_file)
            if schema:
                logging.info(f"  Loaded schema: {schema_file}")
            else:
                logging.warning(f"  Schema defined ({schema_file}) but not found for {category}")
        
        if not schema and schema_file and HAS_JSONSCHEMA:
             logging.error(f"  MISSING SCHEMA FILE: {schema_file}")
             validation_failed = True

        files = [f for f in os.listdir(category_path) if f.endswith('.json')]
        for file in files:
            file_path = os.path.join(category_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    # Validate
                    if schema:
                        try:
                            validate(instance=data, schema=schema)
                        except ValidationError as e:
                            logging.error(f"  Validation Error in {file}: {e.message}")
                            validation_failed = True
                            continue # Skip adding this to aggregate or fail build?

                    aggregated_data[category].append(data)
                except json.JSONDecodeError as e:
                    logging.error(f"  JSON Error in {file}: {e}")
                    validation_failed = True

    # Process Singleton Maps (files in root data dir)
    SINGLETONS = ['game_info.json']
    for singleton in SINGLETONS:
        file_path = os.path.join(DATA_DIR, singleton)
        if os.path.exists(file_path):
            logging.info(f"Processing singleton: {singleton}")
            key = singleton.replace('.json', '') # game_info
            
            # Load Schema
            schema_file = SCHEMA_MAP.get(key)
            schema = None
            if HAS_JSONSCHEMA and schema_file:
                schema = load_schema(schema_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if schema:
                        try:
                            validate(instance=data, schema=schema)
                        except ValidationError as e:
                            logging.error(f"  Validation Error in {singleton}: {e.message}")
                            validation_failed = True
                    
                    aggregated_data[key] = data # Add to master
                    
                    # Output individual file
                    output_file = os.path.join(OUTPUT_DIR, singleton)
                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        json.dump(data, out_f, indent=2)
                    logging.info(f"Generated {output_file}")
                    
                except json.JSONDecodeError as e:
                    logging.error(f"  JSON Error in {singleton}: {e}")
                    validation_failed = True

    if validation_failed:
        logging.error("Build Failed due to validation errors.")
        exit(1)

    # Output individual category files
    for category, data in aggregated_data.items():
        output_file = os.path.join(OUTPUT_DIR, f'all_{category}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Generated {output_file} ({len(data)} items)")

    # Output Master Data File
    master_file = os.path.join(OUTPUT_DIR, 'all_data.json')
    with open(master_file, 'w', encoding='utf-8') as f:
        # Wrap in a root object with metadata
        master_output = {
            "meta": {
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "version": "v1",
                "license": "MIT"
            },
            "data": aggregated_data
        }
        json.dump(master_output, f, indent=2)
    logging.info(f"Generated {master_file} (Master Archive)")

    logging.info("Build Complete.")

if __name__ == "__main__":
    main()
