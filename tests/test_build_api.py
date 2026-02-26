import json
from unittest.mock import patch

import build_api
import pytest

# ---------------------------------------------------------------------------
# sanitize_recursive
# ---------------------------------------------------------------------------


class TestSanitizeRecursive:
    def test_string_escapes_less_than(self):
        """Should escape `<` to `&lt;` to prevent XSS."""
        assert build_api.sanitize_recursive("<script>") == "&lt;script>"
        assert build_api.sanitize_recursive("1 < 2") == "1 &lt; 2"

    def test_preserves_safe_strings(self):
        """Should preserve strings without `<`."""
        assert build_api.sanitize_recursive("Safe String 123 !@#") == "Safe String 123 !@#"

    def test_preserves_non_strings(self):
        """Should preserve integers, floats, booleans, and None."""
        assert build_api.sanitize_recursive(123) == 123
        assert build_api.sanitize_recursive(45.67) == 45.67
        assert build_api.sanitize_recursive(True) is True
        assert build_api.sanitize_recursive(None) is None

    def test_recurses_dict(self):
        """Should recursively sanitize dictionary values."""
        data = {"safe": "value", "unsafe": "<img src=x onerror=prompt(1)>", "nested": {"key": "<b>bold</b>"}}
        expected = {
            "safe": "value",
            "unsafe": "&lt;img src=x onerror=prompt(1)>",
            "nested": {"key": "&lt;b>bold&lt;/b>"},
        }
        assert build_api.sanitize_recursive(data) == expected

    def test_recurses_list(self):
        """Should recursively sanitize list elements."""
        data = ["safe", "<i>italic</i>", ["<nested>"]]
        expected = ["safe", "&lt;i>italic&lt;/i>", ["&lt;nested>"]]
        assert build_api.sanitize_recursive(data) == expected

    def test_evil_extreme_nesting(self):
        """Should handle extreme nesting depth up to recursion limit."""
        # Create a dict 500 levels deep
        deep_data = {"level": 0}
        current = deep_data
        for i in range(1, 500):
            current["next"] = {"level": i}
            current = current["next"]
        current["unsafe"] = "<evil>"

        result = build_api.sanitize_recursive(deep_data)

        # Traverse expected result
        res_current = result
        for _ in range(1, 500):
            res_current = res_current["next"]

        assert res_current["unsafe"] == "&lt;evil>"


# ---------------------------------------------------------------------------
# inject_hero_image_urls
# ---------------------------------------------------------------------------


class TestInjectHeroImageUrls:
    def test_missing_entity_id(self):
        """Should no-op if entity_id is missing."""
        entity = {"name": "No ID"}
        build_api.inject_hero_image_urls(entity)
        assert "image_urls" not in entity

    def test_injects_existing_art(self, tmp_path):
        """Should inject URLs for existing .webp files only."""
        # Mock assets directory
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        heroes_dir = assets_dir / "heroes"
        heroes_dir.mkdir()
        (heroes_dir / "test_hero.webp").touch()  # Card exists

        abilities_dir = heroes_dir / "abilities"
        abilities_dir.mkdir()
        (abilities_dir / "test_hero_attack.webp").touch()  # Only attack ability exists

        entity = {"entity_id": "test_hero"}

        with patch("config.ASSETS_DIR", str(assets_dir)):
            build_api.inject_hero_image_urls(entity)

        assert "image_urls" in entity
        assert entity["image_urls"]["card"] == "/assets/heroes/test_hero.webp"
        assert entity["image_urls"]["attack"] == "/assets/heroes/abilities/test_hero_attack.webp"

        # Missing abilities should not be injected
        assert "passive" not in entity["image_urls"]
        assert "defense" not in entity["image_urls"]
        assert "ultimate" not in entity["image_urls"]


# ---------------------------------------------------------------------------
# ensure_output_dir & save_json
# ---------------------------------------------------------------------------


class TestFileOperations:
    def test_ensure_output_dir_creates_and_cleans(self, tmp_path):
        """Should create dir if missing, and remove stale files."""
        # Pre-populate directory with a stale file
        output_dir = tmp_path / "api_out"
        output_dir.mkdir()

        stale_file = output_dir / "units.json"
        stale_file.touch()

        # A file not in the cleanup lists should survive
        survivor_file = output_dir / "survivor.txt"
        survivor_file.touch()

        with patch("build_api.OUTPUT_DIR", str(output_dir)):
            build_api.ensure_output_dir()

        assert output_dir.exists()
        assert not stale_file.exists()
        assert survivor_file.exists()

    def test_save_json(self, tmp_path):
        """Should write valid JSON payload."""
        output_dir = tmp_path / "api_out"
        output_dir.mkdir()

        data = {"key": "value", "list": [1, 2, 3]}

        with patch("build_api.OUTPUT_DIR", str(output_dir)):
            build_api.save_json("test.json", data)

        written_file = output_dir / "test.json"
        assert written_file.exists()

        with open(written_file, encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded == data

    def test_evil_save_invalid_json_types(self, tmp_path):
        """Should crash on non-serializable objects (expected behavior of json.dump)."""
        output_dir = tmp_path / "api_out"
        output_dir.mkdir()

        class Unserializable:
            pass

        with patch("build_api.OUTPUT_DIR", str(output_dir)):
            with pytest.raises(TypeError):
                build_api.save_json("test.json", {"obj": Unserializable()})


# ---------------------------------------------------------------------------
# build_patch_history
# ---------------------------------------------------------------------------


class TestBuildPatchHistory:
    def test_build_patch_history_copies_files(self, tmp_path):
        root_dir = tmp_path / "root"
        root_dir.mkdir()

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        # Create some source files
        (root_dir / "changelog.json").touch()
        (root_dir / "audit.json").touch()
        (root_dir / "changelog_page_1.json").touch()

        timeline_src = root_dir / "timeline"
        timeline_src.mkdir()
        (timeline_src / "snap1.json").touch()
        (timeline_src / "snap2.json").touch()
        (timeline_src / ".gitkeep").touch()  # Should skip dotfiles

        with patch("config.BASE_DIR", str(root_dir)), patch("build_api.OUTPUT_DIR", str(out_dir)):
            build_api.build_patch_history()

        assert (out_dir / "changelog.json").exists()
        assert (out_dir / "audit.json").exists()
        assert (out_dir / "changelog_page_1.json").exists()

        assert (out_dir / "timeline" / "snap1.json").exists()
        assert (out_dir / "timeline" / "snap2.json").exists()
        assert not (out_dir / "timeline" / ".gitkeep").exists()

    def test_evil_missing_history_directories(self, tmp_path):
        """Should not crash if source files or directories are completely missing."""
        root_dir = tmp_path / "empty_root"
        root_dir.mkdir()

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch("config.BASE_DIR", str(root_dir)), patch("build_api.OUTPUT_DIR", str(out_dir)):
            build_api.build_patch_history()  # Should run without Exception

        assert not (out_dir / "timeline").exists()
