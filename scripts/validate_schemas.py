"""
Lightweight Schema Validator

Validates all JSON data files against schemas in `schemas/v2/` using standard
`jsonschema` library. Does not perform cross-file referential integrity checks.
"""

import json
import os
import sys
from pathlib import Path

try:
    from jsonschema import ValidationError, validators
    from referencing import Registry, Resource
except ImportError:
    print("CRITICAL: 'jsonschema' (>=4.18) or 'referencing' library not found.")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCHEMAS_DIR = os.path.join(PROJECT_ROOT, "schemas", "v2")


def load_json(filepath):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def create_registry(schemas_dir):
    """
    Creates a referencing.Registry pre-loaded with all schema files.
    Returns: (registry, schemas_map[filename -> uri])
    """
    registry = Registry()
    schemas_map = {}

    for root, _, files in os.walk(schemas_dir):
        for file in files:
            if file.endswith(".schema.json"):
                path = Path(os.path.join(root, file))
                try:
                    schema = load_json(path)
                    resource = Resource.from_contents(schema)

                    # Register by absolute URI
                    registry = registry.with_resource(path.as_uri(), resource)

                    # Store for filename lookup
                    schemas_map[file] = path.as_uri()
                except Exception as e:
                    print(f"Error loading schema {file}: {e}")

    return registry, schemas_map


def get_schema_for_file(filepath, data, schemas_map):
    """
    Heuristically determines the correct schema URI for a given JSON file
    by checking explicit $schema properties or folder name conventions.
    """
    # 1. Check explicit $schema
    if "$schema" in data:
        ref = data["$schema"]
        # Extract filename from reference
        fname = os.path.basename(ref)
        if fname in schemas_map:
            return schemas_map[fname]

    # 2. Heuristic based on directory
    folder = os.path.basename(os.path.dirname(filepath))
    candidate = f"{folder}.schema.json"
    if candidate in schemas_map:
        return schemas_map[candidate]

    return None


def main():
    print("Initializing Schema Registry...")
    registry, schemas_map = create_registry(SCHEMAS_DIR)
    print(f"Loaded {len(schemas_map)} schemas.")

    errors = []
    passed = 0

    print("\nValidating Data...")
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)

            try:
                data = load_json(filepath)
                schema_uri = get_schema_for_file(filepath, data, schemas_map)

                if not schema_uri:
                    print(f"SKIP: {rel_path} (No matching schema found)")
                    continue

                # Retrieve schema resource to get the actual schema object
                resolver = registry.resolver()
                resolved = resolver.lookup(schema_uri)
                schema = resolved.contents

                # CRITICAL: If the schema doesn't have an $id, we must inject one so relative refs resolve against it
                if "$id" not in schema:
                    schema["$id"] = schema_uri

                # Instantiate Validator with registry
                ValidatorClass = validators.validator_for(schema)
                validator = ValidatorClass(schema, registry=registry)

                validator.validate(data)
                print(f"PASS: {rel_path}")
                passed += 1

            except ValidationError as e:
                print(f"FAIL: {rel_path}")
                print(f"  -> Path: {e.json_path}")
                print(f"  -> Error: {e.message}")
                errors.append(f"{rel_path}: {e.message}")
            except Exception as e:
                print(f"ERROR: {rel_path}: {e}")
                errors.append(f"{rel_path}: Runtime Error - {e}")

    print("\n" + "=" * 30)
    print(f"Summary: {passed} passed, {len(errors)} failed.")

    if errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
