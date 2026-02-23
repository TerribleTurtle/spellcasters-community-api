import glob
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import config  # noqa: E402

try:
    from referencing import Registry, Resource
except ImportError:
    pass


def _load_json_file(filepath):
    """Helper to load a JSON file for fixtures."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def schema_loader():
    """Loads all JSON schemas from the schemas directory."""
    schemas = {}
    for name, filename in config.SCHEMA_FILES.items():
        path = os.path.join(config.SCHEMAS_DIR, filename)
        with open(path, encoding="utf-8") as f:
            schemas[name] = json.load(f)
    return schemas


@pytest.fixture(scope="session")
def registry_and_schemas():
    """Builds a registry of all schemas in the V2 schema directory."""
    registry = Registry()
    schemas_by_filename = {}

    for root, _, files in os.walk(config.SCHEMAS_DIR):
        for file in files:
            if not file.endswith(".schema.json"):
                continue
            filepath = os.path.join(root, file)
            schema = _load_json_file(filepath)

            abs_uri = Path(filepath).as_uri()
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(abs_uri, resource)

            rel_name = os.path.relpath(filepath, config.SCHEMAS_DIR).replace("\\", "/")
            schemas_by_filename[rel_name] = abs_uri
            schemas_by_filename[file] = abs_uri  # fallback

    return registry, schemas_by_filename


@pytest.fixture(scope="session")
def data_loader():
    """Loads all data files into a dictionary keyed by folder."""
    data_store = {}
    load_errors = []
    for folder in config.FOLDER_TO_SCHEMA:
        data_store[folder] = []
        path_pattern = os.path.join(config.DATA_DIR, folder, "*.json")
        for filepath in glob.glob(path_pattern):
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = json.load(f)
                    # Add metadata for easier debugging in tests
                    content["_filepath"] = filepath
                    content["_filename"] = os.path.basename(filepath)
                    data_store[folder].append(content)
            except Exception as e:
                load_errors.append(f"Failed to load {filepath}: {e}")

    if load_errors:
        pytest.fail("Data loading errors:\n" + "\n".join(load_errors))

    return data_store
