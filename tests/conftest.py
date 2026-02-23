import glob
import json
import os
import sys

import pytest

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import config  # noqa: E402


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
def data_loader():
    """Loads all data files into a dictionary keyed by folder."""
    data_store = {}
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
                print(f"Failed to load {filepath}: {e}")
    return data_store
