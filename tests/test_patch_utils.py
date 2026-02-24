"""
Aggressive tests for patch_utils.py

Covers: compute_diff, _parse_deepdiff_path, get_file_content_at_commit,
load_json, save_json — including every diff category, edge cases, and error paths.
"""

import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import patch_utils

# ---------------------------------------------------------------------------
# _parse_deepdiff_path — pure function
# ---------------------------------------------------------------------------


class TestParseDeepdiffPath:
    def test_simple_string_key(self):
        assert patch_utils._parse_deepdiff_path("root['health']") == ["health"]

    def test_nested_string_keys(self):
        assert patch_utils._parse_deepdiff_path("root['stats']['attack']") == ["stats", "attack"]

    def test_integer_index(self):
        assert patch_utils._parse_deepdiff_path("root['tags'][0]") == ["tags", 0]

    def test_mixed_path(self):
        assert patch_utils._parse_deepdiff_path("root['abilities']['passive'][2]") == ["abilities", "passive", 2]

    def test_empty_root(self):
        # A bare "root" with no keys should produce []
        result = patch_utils._parse_deepdiff_path("root")
        assert result == []

    def test_high_index(self):
        result = patch_utils._parse_deepdiff_path("root['list'][99]")
        assert result == ["list", 99]


# ---------------------------------------------------------------------------
# compute_diff — pure function (via patch_utils, not generate_patch)
# ---------------------------------------------------------------------------


class TestComputeDiff:
    def test_returns_empty_for_identical(self):
        data = {"health": 100, "name": "Test"}
        assert patch_utils.compute_diff(data, data) == []

    def test_both_none_returns_empty(self):
        assert patch_utils.compute_diff(None, None) == []

    def test_old_none_new_dict_adds_keys(self):
        diffs = patch_utils.compute_diff(None, {"health": 100})
        assert any(d.get("new_value") == 100 for d in diffs)

    def test_old_dict_new_none_removes_keys(self):
        diffs = patch_utils.compute_diff({"health": 100}, None)
        assert len(diffs) > 0

    def test_value_changed_scalar(self):
        diffs = patch_utils.compute_diff({"health": 100}, {"health": 200})
        assert len(diffs) == 1
        d = diffs[0]
        assert d["path"] == ["health"]
        assert d["old_value"] == 100
        assert d["new_value"] == 200

    def test_key_added(self):
        diffs = patch_utils.compute_diff({"health": 100}, {"health": 100, "attack": 50})
        assert len(diffs) == 1
        assert diffs[0]["path"] == ["attack"]
        assert diffs[0]["new_value"] == 50
        assert "old_value" not in diffs[0]

    def test_key_removed(self):
        diffs = patch_utils.compute_diff({"health": 100, "attack": 50}, {"health": 100})
        assert len(diffs) == 1
        assert diffs[0]["path"] == ["attack"]
        assert diffs[0].get("removed") is True

    def test_nested_value_changed(self):
        old = {"stats": {"health": 100, "attack": 10}}
        new = {"stats": {"health": 150, "attack": 10}}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["path"] == ["stats", "health"]
        assert diffs[0]["old_value"] == 100
        assert diffs[0]["new_value"] == 150

    def test_list_item_added(self):
        old = {"tags": ["fire"]}
        new = {"tags": ["fire", "magic"]}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert "magic" == diffs[0]["new_value"]

    def test_list_item_removed(self):
        old = {"tags": ["fire", "magic"]}
        new = {"tags": ["fire"]}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0].get("removed") is True
        assert diffs[0].get("old_value") == "magic"

    def test_last_modified_is_excluded(self):
        old = {"last_modified": "2024-01-01", "health": 100}
        new = {"last_modified": "2026-01-01", "health": 100}
        diffs = patch_utils.compute_diff(old, new)
        assert diffs == [], "last_modified change must produce no diffs"

    def test_type_change_int_to_string(self):
        old = {"level": 1}
        new = {"level": "one"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["old_value"] == 1
        assert diffs[0]["new_value"] == "one"

    def test_multiple_simultaneous_changes(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "b": 2, "d": 4}
        diffs = patch_utils.compute_diff(old, new)
        paths = [d["path"] for d in diffs]
        assert ["a"] in paths  # value changed
        assert ["c"] in paths  # removed
        assert ["d"] in paths  # added

    def test_deeply_nested_list_in_dict(self):
        old = {"abilities": {"passive": [{"name": "Regen"}]}}
        new = {"abilities": {"passive": [{"name": "Regen"}, {"name": "Shield"}]}}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1

    def test_large_unchanged_data_returns_empty(self):
        data = {f"key_{i}": i * 10 for i in range(100)}
        assert patch_utils.compute_diff(data, data) == []


# ---------------------------------------------------------------------------
# get_file_content_at_commit — subprocess mock
# ---------------------------------------------------------------------------


class TestGetFileContentAtCommit:
    @patch("subprocess.run")
    def test_returns_parsed_json_on_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"health": 100}')
        result = patch_utils.get_file_content_at_commit("data/units/ogre.json", "abc123")
        assert result == {"health": 100}

    @patch("subprocess.run")
    def test_returns_none_on_git_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        result = patch_utils.get_file_content_at_commit("data/units/ogre.json", "deadbeef")
        assert result is None

    @patch("subprocess.run")
    def test_returns_none_on_invalid_json(self, mock_run):
        mock_run.return_value = MagicMock(stdout="not json {{{")
        result = patch_utils.get_file_content_at_commit("data/units/ogre.json", "abc123")
        assert result is None

    @patch("subprocess.run")
    def test_calls_git_show_correctly(self, mock_run):
        mock_run.return_value = MagicMock(stdout="{}")
        patch_utils.get_file_content_at_commit("data/units/skeleton.json", "deadbeef")
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "show" in args
        assert "deadbeef:data/units/skeleton.json" in args


# ---------------------------------------------------------------------------
# load_json / save_json — filesystem
# ---------------------------------------------------------------------------


class TestLoadSaveJson:
    def test_load_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = patch_utils.load_json(str(f))
        assert result == {"key": "value"}

    def test_load_returns_none_for_missing_file(self, tmp_path):
        result = patch_utils.load_json(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_returns_none_for_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{bad json}", encoding="utf-8")
        result = patch_utils.load_json(str(f))
        assert result is None

    def test_save_and_reload(self, tmp_path):
        data = {"version": "1.2.3", "tags": ["a", "b"]}
        out = str(tmp_path / "out.json")
        patch_utils.save_json(out, data)
        assert os.path.exists(out)
        with open(out, encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded == data

    def test_save_uses_indent_2(self, tmp_path):
        data = {"a": 1}
        out = str(tmp_path / "out.json")
        patch_utils.save_json(out, data)
        raw = open(out, encoding="utf-8").read()
        # indent=2 means second line starts with two spaces
        assert "  " in raw
