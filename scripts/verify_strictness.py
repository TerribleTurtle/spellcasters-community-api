import sys
import copy
from jsonschema import validators, ValidationError
from validate_integrity import create_registry, SCHEMAS_DIR


def main():  # pylint: disable=too-many-locals
    print("--- Starting DoubleCheck Verification ---")

    # 1. Build Registry (Loads all schemas with correct IDs)
    try:
        registry, schemas_map = create_registry(SCHEMAS_DIR)
    except Exception as e:
        print(f"CRITICAL: Failed to create registry: {e}")
        sys.exit(1)

    # 2. Get Hero Schema
    schema_filename = "heroes.schema.json"
    if schema_filename not in schemas_map:
        print(f"CRITICAL: {schema_filename} not found in registry.")
        sys.exit(1)

    hero_uri = schemas_map[schema_filename]
    resolver = registry.resolver()
    resolved = resolver.lookup(hero_uri)
    schema = resolved.contents

    # 3. Setup Validator
    ValidatorClass = validators.validator_for(schema)
    validator = ValidatorClass(schema, registry=registry)

    def validate(data):
        try:
            validator.validate(data)
            return True, "Valid"
        except ValidationError as e:
            return False, e.message

    # Create a valid minimal hero payload based on the schema example
    valid_hero = {
        "entity_id": "test_hero",
        "name": "Test Hero",
        "category": "Spellcaster",
        "class": "Conqueror",
        "difficulty": 1,
        "health": 100,
        "movement_speed": 5,
        "movement_type": "Ground",
        "population": 0,
        "image_required": False,
        "description": "A test hero.",
        "tags": ["test"],
        "abilities": {
            "passive": [],
            "primary": {"name": "Hit", "description": "Hits stuff", "damage": 10},
            "defense": {"name": "Block", "description": "Blocks stuff"},
            "ultimate": {"name": "Win", "description": "Wins game"}
        },
        "last_modified": "2026-01-01T00:00:00Z",
        "changelog": []
    }

    # Test 1: Baseline Validity
    is_valid, msg = validate(valid_hero)
    print(f"Test 1 (Baseline Valid): {'PASS' if is_valid else 'FAIL'} - {msg}")
    if not is_valid:
        sys.exit(1)

    # Test 2: Check Property Shadowing Fix (Unknown Property)
    # If we add a garbage property, it should FAIL because unevaluatedProperties: false (or additionalProperties: false)
    invalid_prop = copy.deepcopy(valid_hero)
    invalid_prop["abilities"]["primary"]["garbage_stat"] = 999
    is_valid, msg = validate(invalid_prop)
    print(f"Test 2 (Strictness - Unknown Prop): {'PASS' if not is_valid else 'FAIL'} - Expected Failure, Got: {msg}")

    # Test 3: Check String Strictness (Empty Name)
    # core.schema.json should now enforce minLength: 1
    invalid_string = copy.deepcopy(valid_hero)
    invalid_string["name"] = ""
    is_valid, msg = validate(invalid_string)
    print(f"Test 3 (Strictness - Empty Name): {'PASS' if not is_valid else 'FAIL'} - Expected Failure, Got: {msg}")

    # Test 4: Check Pattern Strictness (Bad ID)
    # core.schema.json should enforce snake_case
    invalid_id = copy.deepcopy(valid_hero)
    invalid_id["entity_id"] = "Bad ID with Spaces"
    is_valid, msg = validate(invalid_id)
    print(f"Test 4 (Strictness - Bad ID Pattern): {'PASS' if not is_valid else 'FAIL'} - Expected Failure, Got: {msg}")

    print("--- Double Check Complete ---")


if __name__ == "__main__":
    main()
