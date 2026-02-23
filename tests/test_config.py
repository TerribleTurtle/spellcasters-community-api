"""
Unit tests for config.py

Tests the shared load_json utility function with various edge cases.
"""

import json

import config


class TestLoadJson:
    """Tests for the safe JSON loader."""

    def test_loads_valid_json(self, tmp_path):
        """Should return parsed dict for valid JSON file."""
        f = tmp_path / "valid.json"
        f.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = config.load_json(str(f))
        assert result == {"key": "value"}

    def test_returns_none_for_missing_file(self, tmp_path):
        """Should return None when file doesn't exist."""
        result = config.load_json(str(tmp_path / "missing.json"))
        assert result is None

    def test_returns_none_for_corrupt_json(self, tmp_path):
        """Should return None for malformed JSON."""
        f = tmp_path / "corrupt.json"
        f.write_text("{not valid json!!!", encoding="utf-8")
        result = config.load_json(str(f))
        assert result is None

    def test_loads_json_list(self, tmp_path):
        """Should handle JSON arrays as well as objects."""
        f = tmp_path / "list.json"
        f.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        result = config.load_json(str(f))
        assert result == [1, 2, 3]
