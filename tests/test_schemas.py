import pytest
import jsonschema
import os
import sys

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import config

def test_json_schemas(data_loader, schema_loader):
    """
    Validates every JSON file in the data directories against its assigned schema.
    Collects all errors rather than stopping at the first failure.
    """
    errors = []

    for folder, folder_data in data_loader.items():
        schema_key = config.FOLDER_TO_SCHEMA.get(folder)
        if not schema_key:
            continue
        
        schema = schema_loader.get(schema_key)
        if not schema:
            errors.append(f"Missing schema '{schema_key}' for folder '{folder}'")
            continue

        for item in folder_data:
            clean_item = item.copy()
            filename = clean_item.pop("_filename", "unknown")
            clean_item.pop("_filepath", None)

            try:
                jsonschema.validate(instance=clean_item, schema=schema)
            except jsonschema.ValidationError as e:
                errors.append(f"[{folder}/{filename}] Schema Error: {e.message}")
            except Exception as e:
                errors.append(f"[{folder}/{filename}] Unexpected Error: {e}")

    assert len(errors) == 0, "\n".join(errors)
