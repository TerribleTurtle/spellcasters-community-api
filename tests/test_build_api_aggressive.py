"""
Aggressive tests for build_api.py

Covers: sanitize_recursive (XSS), ensure_output_dir (cleanup),
build_patch_history, full pipeline with injected failures, and
the Safety Lock (validate_integrity gates the build).
"""

import json
import os
from unittest.mock import patch

import build_api

# ---------------------------------------------------------------------------
# sanitize_recursive — pure function, zero mocking
# ---------------------------------------------------------------------------


class TestSanitizeRecursive:
    def test_escapes_lt_in_string(self):
        assert build_api.sanitize_recursive("<script>") == "&lt;script>"

    def test_escapes_multiple_lt(self):
        result = build_api.sanitize_recursive("a<b<c")
        assert result == "a&lt;b&lt;c"

    def test_preserves_gt(self):
        # > is intentionally kept for readability / game math
        assert build_api.sanitize_recursive("5 > 3") == "5 > 3"

    def test_preserves_quotes(self):
        assert build_api.sanitize_recursive('"quoted"') == '"quoted"'

    def test_recursively_sanitizes_dict(self):
        data = {"name": "<Hero>", "level": 5}
        result = build_api.sanitize_recursive(data)
        assert result["name"] == "&lt;Hero>"
        assert result["level"] == 5  # integer untouched

    def test_recursively_sanitizes_list(self):
        data = ["<fireball>", "ice", 42]
        result = build_api.sanitize_recursive(data)
        assert result[0] == "&lt;fireball>"
        assert result[1] == "ice"
        assert result[2] == 42

    def test_nested_dict_in_list(self):
        data = [{"description": "<xss>"}]
        result = build_api.sanitize_recursive(data)
        assert result[0]["description"] == "&lt;xss>"

    def test_passthrough_non_string_types(self):
        assert build_api.sanitize_recursive(42) == 42
        assert build_api.sanitize_recursive(3.14) == 3.14
        assert build_api.sanitize_recursive(True) is True
        assert build_api.sanitize_recursive(None) is None

    def test_empty_string(self):
        assert build_api.sanitize_recursive("") == ""

    def test_no_special_chars_unchanged(self):
        s = "A perfectly safe string with no HTML injection."
        assert build_api.sanitize_recursive(s) == s

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": "<deepxss>"}}}}
        result = build_api.sanitize_recursive(data)
        assert result["a"]["b"]["c"]["d"] == "&lt;deepxss>"


# ---------------------------------------------------------------------------
# ensure_output_dir — creates & cleans correctly
# ---------------------------------------------------------------------------


class TestEnsureOutputDir:
    def test_creates_directory_if_missing(self, tmp_path):
        output = str(tmp_path / "api_out")
        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.AGGREGATION_MAP", {}),
            patch("build_api.SINGLE_FILES", {}),
        ):
            build_api.ensure_output_dir()
        assert os.path.isdir(output)

    def test_removes_stale_collection_files(self, tmp_path):
        output = str(tmp_path)
        stale = tmp_path / "units.json"
        stale.write_text("{}", encoding="utf-8")
        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.AGGREGATION_MAP", {"units": "units"}),
            patch("build_api.SINGLE_FILES", {}),
        ):
            build_api.ensure_output_dir()
        assert not stale.exists()

    def test_removes_all_data_and_status(self, tmp_path):
        output = str(tmp_path)
        for fname in ["all_data.json", "status.json"]:
            (tmp_path / fname).write_text("{}", encoding="utf-8")
        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.AGGREGATION_MAP", {}),
            patch("build_api.SINGLE_FILES", {}),
        ):
            build_api.ensure_output_dir()
        assert not (tmp_path / "all_data.json").exists()
        assert not (tmp_path / "status.json").exists()


# ---------------------------------------------------------------------------
# save_json — records item count in log
# ---------------------------------------------------------------------------


class TestSaveJson:
    def test_writes_valid_json(self, tmp_path):
        with patch("build_api.OUTPUT_DIR", str(tmp_path)):
            build_api.save_json("test.json", [{"id": 1}, {"id": 2}])
        out = tmp_path / "test.json"
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 2

    def test_save_json_dict(self, tmp_path):
        with patch("build_api.OUTPUT_DIR", str(tmp_path)):
            build_api.save_json("meta.json", {"key": "value"})
        data = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
        assert data == {"key": "value"}


# ---------------------------------------------------------------------------
# build_patch_history — file copy logic
# ---------------------------------------------------------------------------


class TestBuildPatchHistory:
    def test_copies_changelog_files(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "api" / "v2"
        dst.mkdir(parents=True)

        # Create phony changelog files
        for fname in ["changelog.json", "changelog_index.json", "changelog_latest.json"]:
            (src / fname).write_text("[]", encoding="utf-8")

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", str(dst)),
            patch.object(cfg, "BASE_DIR", str(src)),
            patch.object(cfg, "OUTPUT_DIR", str(dst)),
            patch.object(
                cfg, "PATCH_HISTORY_FILES", ["changelog.json", "changelog_index.json", "changelog_latest.json"]
            ),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
        ):
            build_api.build_patch_history()

        assert (dst / "changelog.json").exists()
        assert (dst / "changelog_index.json").exists()

    def test_warns_on_missing_changelog_file(self, tmp_path, capsys):
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "api" / "v2"
        dst.mkdir(parents=True)

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", str(dst)),
            patch.object(cfg, "BASE_DIR", str(src)),
            patch.object(cfg, "OUTPUT_DIR", str(dst)),
            patch.object(cfg, "PATCH_HISTORY_FILES", ["missing_changelog.json"]),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
        ):
            build_api.build_patch_history()

        captured = capsys.readouterr()
        assert "WARN" in captured.out or "not found" in captured.out.lower()

    def test_copies_timeline_snapshots(self, tmp_path):
        src = tmp_path / "src"
        (src / "timeline").mkdir(parents=True)
        dst = tmp_path / "api" / "v2"
        dst.mkdir(parents=True)

        # Create a phony timeline snapshot
        (src / "timeline" / "ogre.json").write_text('{"snapshot": true}', encoding="utf-8")

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", str(dst)),
            patch.object(cfg, "BASE_DIR", str(src)),
            patch.object(cfg, "OUTPUT_DIR", str(dst)),
            patch.object(cfg, "PATCH_HISTORY_FILES", []),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
        ):
            build_api.build_patch_history()

        assert (dst / "timeline" / "ogre.json").exists()

    def test_skips_dotfiles_in_timeline(self, tmp_path):
        src = tmp_path / "src"
        (src / "timeline").mkdir(parents=True)
        dst = tmp_path / "api" / "v2"
        dst.mkdir(parents=True)

        (src / "timeline" / ".gitkeep").write_text("", encoding="utf-8")
        (src / "timeline" / "hero.json").write_text("{}", encoding="utf-8")

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", str(dst)),
            patch.object(cfg, "BASE_DIR", str(src)),
            patch.object(cfg, "OUTPUT_DIR", str(dst)),
            patch.object(cfg, "PATCH_HISTORY_FILES", []),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
        ):
            build_api.build_patch_history()

        assert not (dst / "timeline" / ".gitkeep").exists()
        assert (dst / "timeline" / "hero.json").exists()


# ---------------------------------------------------------------------------
# main — Safety Lock: validate_integrity must gate the build
# ---------------------------------------------------------------------------


class TestBuildApiSafetyLock:
    def test_aborts_when_validation_fails(self, tmp_path):
        """If validate_integrity raises SystemExit(1), build must not proceed."""
        output = str(tmp_path / "api_out")
        os.makedirs(output)

        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.validate_integrity", side_effect=SystemExit(1)),
            patch("sys.exit") as mock_exit,
        ):
            build_api.main()

        mock_exit.assert_called_with(1)

    def test_all_collection_keys_present_in_all_data(self, tmp_path):
        """all_data.json should contain every AGGREGATION_MAP key."""
        output = str(tmp_path / "api")
        os.makedirs(output)

        # Create minimal data dirs
        data_root = tmp_path / "data"
        for folder in ["units", "spells", "heroes", "consumables", "upgrades", "titans"]:
            (data_root / folder).mkdir(parents=True, exist_ok=True)

        # Write a single entity
        (data_root / "units" / "test_unit.json").write_text('{"entity_id": "test_unit"}', encoding="utf-8")

        game_cfg = data_root / "game_config.json"
        game_cfg.write_text('{"version": "0.0.1"}', encoding="utf-8")

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.DATA_DIR", str(data_root)),
            patch.object(cfg, "OUTPUT_DIR", output),
            patch.object(cfg, "DATA_DIR", str(data_root)),
            patch.object(cfg, "BASE_DIR", str(tmp_path)),
            patch.object(cfg, "PATCH_HISTORY_FILES", []),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
            patch("build_api.validate_integrity"),
        ):
            build_api.main()

        all_data_path = os.path.join(output, "all_data.json")
        assert os.path.exists(all_data_path)
        with open(all_data_path, encoding="utf-8") as fh:
            all_data = json.load(fh)

        for key in build_api.AGGREGATION_MAP:
            assert key in all_data, f"'{key}' missing from all_data.json"


# ---------------------------------------------------------------------------
# status.json shape
# ---------------------------------------------------------------------------


class TestStatusJson:
    def test_status_json_has_required_fields(self, tmp_path):
        output = str(tmp_path / "api")
        os.makedirs(output)
        data_root = tmp_path / "data"
        data_root.mkdir()
        (data_root / "game_config.json").write_text('{"version": "1.2.3"}', encoding="utf-8")

        import config as cfg

        with (
            patch("build_api.OUTPUT_DIR", output),
            patch("build_api.DATA_DIR", str(data_root)),
            patch.object(cfg, "OUTPUT_DIR", output),
            patch.object(cfg, "DATA_DIR", str(data_root)),
            patch.object(cfg, "BASE_DIR", str(tmp_path)),
            patch.object(cfg, "PATCH_HISTORY_FILES", []),
            patch.object(cfg, "PATCH_HISTORY_DIR", "timeline"),
            patch("build_api.validate_integrity"),
            patch("build_api.AGGREGATION_MAP", {}),
            patch("build_api.SINGLE_FILES", {}),
        ):
            build_api.main()

        status_path = os.path.join(output, "status.json")
        assert os.path.exists(status_path)
        with open(status_path, encoding="utf-8") as fh:
            status = json.load(fh)

        for key in ["status", "environment", "maintenance", "valid_versions", "generated_at"]:
            assert key in status, f"Missing key '{key}' in status.json"

        assert "1.2.3" in status["valid_versions"]
