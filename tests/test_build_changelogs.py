"""
Unit tests for build_changelogs.py

Tests the patch cleaning logic, pagination math, and edge cases.
"""

import json
import os
from unittest.mock import patch

import build_changelogs

# ---------------------------------------------------------------------------
# clean_patches — Pure function
# ---------------------------------------------------------------------------


class TestCleanPatches:
    """Tests for the legacy key stripping function."""

    def test_strips_diff_key(self):
        """Should remove 'diff' key while preserving all other keys."""
        patches = [
            {"version": "1.0.0", "date": "2026-01-01", "changes": ["Added units"], "diff": {"some": "data"}},
            {"version": "1.0.1", "date": "2026-01-15", "changes": ["Bug fix"], "diff": {"other": "data"}},
        ]
        result = build_changelogs.clean_patches(patches)
        assert len(result) == 2
        for entry in result:
            assert "diff" not in entry
            assert "version" in entry
            assert "date" in entry
            assert "changes" in entry

    def test_empty_list(self):
        """Should return empty list for empty input."""
        result = build_changelogs.clean_patches([])
        assert result == []

    def test_no_diff_key_passthrough(self):
        """Patches without 'diff' key should pass through unchanged."""
        patches = [{"version": "1.0.0", "date": "2026-01-01"}]
        result = build_changelogs.clean_patches(patches)
        assert result == [{"version": "1.0.0", "date": "2026-01-01"}]


# ---------------------------------------------------------------------------
# main — Integration test with tmp_path
# ---------------------------------------------------------------------------


class TestMainBuild:
    """Tests for the full changelog build pipeline."""

    def test_generates_all_files(self, tmp_path):
        """Should generate changelog.json, changelog_latest.json, changelog_index.json, and page files."""
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(
            json.dumps(
                [
                    {"version": "1.0.0", "date": "2026-01-01", "changes": ["Init"]},
                    {"version": "1.0.1", "date": "2026-01-15", "changes": ["Fix"]},
                ]
            ),
            encoding="utf-8",
        )

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        assert os.path.exists(tmp_path / "changelog.json")
        assert os.path.exists(tmp_path / "changelog_latest.json")
        assert os.path.exists(tmp_path / "changelog_index.json")
        assert os.path.exists(tmp_path / "changelog_page_1.json")

        # Verify latest is the first entry
        with open(tmp_path / "changelog_latest.json", encoding="utf-8") as f:
            latest = json.load(f)
        assert latest["version"] == "1.0.0"

    def test_pagination_boundary(self, tmp_path):
        """51 patches should produce 2 page files."""
        patches = [{"version": f"0.0.{i}", "date": "2026-01-01"} for i in range(51)]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_index.json", encoding="utf-8") as f:
            index = json.load(f)

        assert index["total_patches"] == 51
        assert index["total_pages"] == 2
        assert len(index["pages"]) == 2
        assert os.path.exists(tmp_path / "changelog_page_1.json")
        assert os.path.exists(tmp_path / "changelog_page_2.json")

    def test_empty_patches(self, tmp_path):
        """Empty patches should generate valid empty JSON files."""
        patches_file = tmp_path / "patches.json"
        patches_file.write_text("[]", encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog.json", encoding="utf-8") as f:
            assert json.load(f) == []
        with open(tmp_path / "changelog_latest.json", encoding="utf-8") as f:
            assert json.load(f) is None

    def test_missing_patches_file(self, tmp_path):
        """Should handle missing patches.json gracefully."""
        missing = tmp_path / "nonexistent.json"

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(missing)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog.json", encoding="utf-8") as f:
            assert json.load(f) == []
