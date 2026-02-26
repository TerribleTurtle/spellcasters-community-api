import json
import os
from unittest.mock import patch

import jsonschema
import pytest

import validate_schemas
import config


# ---------------------------------------------------------------------------
# load_json
# ---------------------------------------------------------------------------

class TestLoadJson:
    def test_loads_valid_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"a": 1}', encoding="utf-8")
        result = validate_schemas.load_json(str(f))
        assert result == {"a": 1}

    def test_evil_unparsable_json(self, tmp_path):
        """Should raise json.JSONDecodeError."""
        f = tmp_path / "bad.json"
        f.write_text('{a: 1, "trailing_comma": },', encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            validate_schemas.load_json(str(f))


# ---------------------------------------------------------------------------
# create_registry
# ---------------------------------------------------------------------------

class TestCreateRegistry:
    def test_creates_registry(self, registry_and_schemas):
        # registry_and_schemas is a fixture using real directory, but let's test the function directly
        schema_dir = config.SCHEMAS_DIR
        registry, schemas_map = validate_schemas.create_registry(schema_dir)
        
        assert len(schemas_map) > 0
        assert "units.schema.json" in schemas_map
        assert "core.schema.json" in schemas_map

    def test_evil_corrupted_schema(self, tmp_path):
        """Corrupt schemas should be logged and skipped, not crashing the registry creation."""
        schema_dir = tmp_path / "schemas"
        schema_dir.mkdir()
        
        valid = schema_dir / "valid.schema.json"
        valid.write_text('{"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "valid", "type": "string"}', encoding="utf-8")
        
        corrupted = schema_dir / "corrupted.schema.json"
        corrupted.write_text('{invalid_json', encoding="utf-8")
        
        # Capture stdout to verify error logging
        import sys
        from io import StringIO
        captured = StringIO()
        
        with patch('sys.stdout', captured):
            registry, schemas_map = validate_schemas.create_registry(str(schema_dir))

        # Test that the valid schema was kept and corrupted skipped
        assert "valid.schema.json" in schemas_map
        assert "corrupted.schema.json" not in schemas_map
        assert "Error loading schema corrupted.schema.json" in captured.getvalue()


# ---------------------------------------------------------------------------
# get_schema_for_file
# ---------------------------------------------------------------------------

class TestGetSchemaForFile:
    @pytest.fixture
    def mock_map(self):
        return {
            "heroes.schema.json": "uri:heroes",
            "spells.schema.json": "uri:spells",
            "infusions.schema.json": "uri:infusions"
        }

    def test_explicit_schema(self, mock_map):
        data = {"$schema": "../../schemas/v2/heroes.schema.json"}
        uri = validate_schemas.get_schema_for_file("some/path/file.json", data, mock_map)
        assert uri == "uri:heroes"

    def test_folder_heuristic(self, mock_map):
        data = {"name": "Fireball"}
        uri = validate_schemas.get_schema_for_file("data/spells/fireball.json", data, mock_map)
        assert uri == "uri:spells"

    def test_filename_heuristic(self, mock_map):
        data = {"name": "Infusion"}
        # For root level files like data/infusions.json
        uri = validate_schemas.get_schema_for_file("data/infusions.json", data, mock_map)
        assert uri == "uri:infusions"
        
    def test_no_match(self, mock_map):
        data = {"data": "unknown"}
        uri = validate_schemas.get_schema_for_file("data/unknown/data.json", data, mock_map)
        assert uri is None

    def test_evil_nonexistent_explicit_schema(self, mock_map):
        """Should fall back to heuristics if explicit $schema filename is unknown."""
        data = {"$schema": "../../schemas/v2/does_not_exist.schema.json"}
        # But it happens to be in a known folder
        uri = validate_schemas.get_schema_for_file("data/spells/fireball.json", data, mock_map)
        # It checked $schema, failed to find does_not_exist in map, fell back to 'spells' heuristic
        assert uri == "uri:spells"


# ---------------------------------------------------------------------------
# main (Integration)
# ---------------------------------------------------------------------------

class TestMainIntegration:
    def test_evil_validation_failures_do_not_crash(self, tmp_path):
        """Should catch ValidationErrors and Exception cleanly, sum them up, and sys.exit(1)."""
        project_root = tmp_path / "project"
        data_dir = project_root / "data"
        schemas_dir = project_root / "schemas" / "v2"
        
        schemas_dir.mkdir(parents=True)
        data_dir.mkdir()
        
        # 1. Create a schema
        schema = {
            "type": "object",
            "properties": {"val": {"type": "integer"}},
            "required": ["val"]
        }
        (schemas_dir / "test.schema.json").write_text(json.dumps(schema), encoding="utf-8")
        
        # 2. Create data matching heuristics: folder 'test' matches 'test.schema.json'
        test_data_dir = data_dir / "test"
        test_data_dir.mkdir()
        
        # Data 1: Pass
        (test_data_dir / "pass.json").write_text('{"val": 123}', encoding="utf-8")
        
        # Data 2: Fail (ValidationError)
        (test_data_dir / "fail.json").write_text('{"val": "string_instead_of_int"}', encoding="utf-8")
        
        # Data 3: Unparsable (Exception inside loop -> handles gracefully?)
        # Wait, the load_json throws json.JSONDecodeError before it even gets to validate, 
        # which isn't caught by the try-except in main, it's thrown from load_json.
        # Actually load_json in validate_schemas does NOT have try/except, it raises.
        # But `json.load` raising inside main() *is* caught by `except Exception as e:` in the main loop!
        (test_data_dir / "crash.json").write_text('{bad', encoding="utf-8")

        with patch("validate_schemas.SCHEMAS_DIR", str(schemas_dir)), \
             patch("validate_schemas.DATA_DIR", str(data_dir)), \
             patch("sys.exit") as mock_exit:
            
            validate_schemas.main()
            
            # Should have exited with 1 due to errors
            mock_exit.assert_called_once_with(1)

    def test_all_pass_success(self, tmp_path):
        """If all files pass, sys.exit(0)."""
        project_root = tmp_path / "project"
        data_dir = project_root / "data"
        schemas_dir = project_root / "schemas" / "v2"
        
        schemas_dir.mkdir(parents=True)
        data_dir.mkdir()
        
        schema = {
            "type": "object",
            "properties": {"val": {"type": "integer"}},
            "required": ["val"]
        }
        (schemas_dir / "test.schema.json").write_text(json.dumps(schema), encoding="utf-8")
        
        test_data_dir = data_dir / "test"
        test_data_dir.mkdir()
        (test_data_dir / "pass.json").write_text('{"val": 123}', encoding="utf-8")

        with patch("validate_schemas.SCHEMAS_DIR", str(schemas_dir)), \
             patch("validate_schemas.DATA_DIR", str(data_dir)), \
             patch("sys.exit") as mock_exit:
            
            validate_schemas.main()
            mock_exit.assert_called_once_with(0)
