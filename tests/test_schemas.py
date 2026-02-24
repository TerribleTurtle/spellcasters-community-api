import jsonschema
import pytest
from jsonschema import validators

# Try to import referencing, if not available use legacy (but this project has it)
try:
    from referencing import Registry, Resource  # noqa: F401
except ImportError:
    pytest.skip("referencing library not installed", allow_module_level=True)

import config


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


# ---------------------------------------------------------------------------
# Negative validation tests — schemas must REJECT invalid data
# ---------------------------------------------------------------------------


def _get_validator(registry_and_schemas, schema_filename):
    """Helper to build a validator for a given schema file."""
    registry, schemas_map = registry_and_schemas
    schema_uri = schemas_map[schema_filename]
    schema_resource = registry.get_or_retrieve(schema_uri).value
    schema_contents = schema_resource.contents
    ValidatorClass = validators.validator_for(schema_contents)
    return ValidatorClass(schema_contents, registry=registry)


def test_rejects_missing_entity_id(registry_and_schemas):
    """An empty object should fail validation against units.schema.json."""
    validator = _get_validator(registry_and_schemas, "units.schema.json")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({})


def test_rejects_wrong_type_for_health(registry_and_schemas):
    """A string value for a numeric field should fail validation."""
    validator = _get_validator(registry_and_schemas, "units.schema.json")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"entity_id": "test", "health": "not_a_number"})


def test_rejects_unknown_property_on_unit(registry_and_schemas):
    """An unknown top-level property should fail if schema uses additionalProperties/unevaluatedProperties: false."""
    validator = _get_validator(registry_and_schemas, "units.schema.json")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"entity_id": "test", "garbage_field": True})


def test_standalone_endpoints(registry_and_schemas):
    """
    Validates API endpoint files in api/v2/ against their specific schemas.
    """
    import os
    endpoints = {
        "api/v2/status.json": "status.schema.json",
        "api/v2/patches.json": "patches.schema.json",
        "api/v2/changelog_latest.json": "changelog_latest.schema.json",
        "api/v2/all_data.json": "all_data.schema.json",
        "audit.json": "audit.schema.json",
    }

    for relative_path, schema_filename in endpoints.items():
        data_path = os.path.join(config.BASE_DIR, relative_path)
        if not os.path.exists(data_path):
            continue  # Skip if the script hasn't generated them yet

        data = config.load_json(data_path)
        validator = _get_validator(registry_and_schemas, schema_filename)

        try:
            validator.validate(data)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Validation failed for {relative_path}:\n{e.message}")
