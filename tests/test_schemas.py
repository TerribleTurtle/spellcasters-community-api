import json
import os
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import validators

# Try to import referencing, if not available use legacy (but this project has it)
try:
    from referencing import Registry, Resource
except ImportError:
    pytest.skip("referencing library not installed", allow_module_level=True)

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import config  # noqa: E402


def load_json(filepath):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def registry_and_schemas():
    """Builds a registry of all schemas in the V2 schema directory."""
    registry = Registry()
    schemas_by_filename = {}

    # Walk schema directory
    for root, _, files in os.walk(config.SCHEMAS_DIR):
        for file in files:
            if not file.endswith(".schema.json"):
                continue
            filepath = os.path.join(root, file)
            schema = load_json(filepath)

            # Use absolute file URI as ID for robust local resolution
            abs_uri = Path(filepath).as_uri()
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(abs_uri, resource)

            # Map filename to full path uri for lookup
            # normalization for Windows paths
            rel_name = os.path.relpath(filepath, config.SCHEMAS_DIR).replace("\\", "/")
            schemas_by_filename[rel_name] = abs_uri
            schemas_by_filename[file] = abs_uri  # fallback

    return registry, schemas_by_filename


def test_json_schemas_robust(data_loader, registry_and_schemas):
    """
    Validates every JSON file in the data directories against its assigned schema
    using the referencing library for robust local resolution.
    """
    registry, schemas_map = registry_and_schemas
    errors = []

    for folder, folder_data in data_loader.items():
        # Get schema key from folder mapping
        schema_key = config.FOLDER_TO_SCHEMA.get(folder)
        if not schema_key:
            continue

        # Get filename from schema key
        schema_filename = config.SCHEMA_FILES.get(schema_key)
        if not schema_filename:
            errors.append(f"Missing schema filename in config for key '{schema_key}'")
            continue

        # Look up schema URI in our map
        # config.FOLDER_TO_SCHEMA values might be relative e.g. "units.schema.json"

        schema_uri = schemas_map.get(schema_filename)
        if not schema_uri:
            # Try searching keys that end with it
            found = False
            for k, v in schemas_map.items():
                if k.endswith(schema_filename):
                    schema_uri = v
                    found = True
                    break
            if not found:
                errors.append(f"Missing schema registration for '{schema_filename}'")
                continue

        # Get the schema resource from registry
        try:
            schema_resource = registry.get_or_retrieve(schema_uri).value
            schema_contents = schema_resource.contents

            # Create Validator
            ValidatorClass = validators.validator_for(schema_contents)
            validator = ValidatorClass(schema_contents, registry=registry)

        except Exception as e:
            errors.append(f"Failed to create validator for {schema_filename}: {e}")
            continue

        for item in folder_data:
            clean_item = item.copy()
            filename = clean_item.pop("_filename", "unknown")
            clean_item.pop("_filepath", None)

            try:
                validator.validate(clean_item)
            except jsonschema.ValidationError as e:
                path_str = ".".join([str(p) for p in e.path]) if e.path else "root"
                errors.append(f"[{folder}/{filename}] {path_str}: {e.message}")
            except Exception as e:
                errors.append(f"[{folder}/{filename}] Validation Exception: {e}")

    assert len(errors) == 0, "\n".join(errors[:20])  # Limit error output
