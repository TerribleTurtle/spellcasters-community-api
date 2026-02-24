"""
Aggressive tests for build_changelogs.py

Extends the existing suite with: corrupt JSON handling, exact page content
correctness, index schema shape, diff-key aggregation across many patches,
and boundary arithmetic (exactly PAGE_SIZE patches = 1 page).
"""

import json
import math
import os
from unittest.mock import patch

import build_changelogs

PAGE_SIZE = build_changelogs.PAGE_SIZE


# ---------------------------------------------------------------------------
# clean_patches — aggressive edge cases
# ---------------------------------------------------------------------------


class TestCleanPatchesAggressive:
    def test_preserves_all_non_diff_keys(self):
        patch_data = {
            "version": "1.0.0",
            "title": "Big Update",
            "date": "2026-01-01",
            "tags": ["balance", "bug"],
            "changes": [{"field": "health", "old": 100, "new": 120}],
            "diff": {"legacy": "garbage"},
        }
        result = build_changelogs.clean_patches([patch_data])
        assert len(result) == 1
        assert "diff" not in result[0]
        assert result[0]["tags"] == ["balance", "bug"]
        assert result[0]["changes"] == [{"field": "health", "old": 100, "new": 120}]

    def test_handles_many_patches(self):
        patches = [{"version": f"1.0.{i}", "diff": {}} for i in range(200)]
        result = build_changelogs.clean_patches(patches)
        assert len(result) == 200
        assert all("diff" not in p for p in result)

    def test_does_not_mutate_input(self):
        original = [{"version": "1.0.0", "diff": {"x": 1}}]
        import copy

        original_copy = copy.deepcopy(original)
        build_changelogs.clean_patches(original)
        assert original == original_copy  # input untouched


# ---------------------------------------------------------------------------
# main — exact page content correctness
# ---------------------------------------------------------------------------


class TestPageContentCorrectness:
    def test_page_1_contains_first_n_patches(self, tmp_path):
        patches = [{"version": f"1.0.{i}", "date": "2026-01-01"} for i in range(PAGE_SIZE + 5)]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_page_1.json", encoding="utf-8") as fh:
            page1 = json.load(fh)
        with open(tmp_path / "changelog_page_2.json", encoding="utf-8") as fh:
            page2 = json.load(fh)

        assert len(page1) == PAGE_SIZE
        assert len(page2) == 5
        assert page1[0]["version"] == "1.0.0"
        assert page2[0]["version"] == f"1.0.{PAGE_SIZE}"

    def test_exactly_page_size_patches_is_one_page(self, tmp_path):
        patches = [{"version": f"0.0.{i}"} for i in range(PAGE_SIZE)]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_index.json", encoding="utf-8") as fh:
            index = json.load(fh)

        assert index["total_pages"] == 1
        assert not (tmp_path / "changelog_page_2.json").exists()

    def test_index_schema_shape(self, tmp_path):
        patches = [{"version": "1.0.0"}]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_index.json", encoding="utf-8") as fh:
            index = json.load(fh)

        assert "total_patches" in index
        assert "page_size" in index
        assert "total_pages" in index
        assert "pages" in index
        assert index["page_size"] == PAGE_SIZE
        assert isinstance(index["pages"], list)

    def test_changelog_json_is_full_array(self, tmp_path):
        patches = [{"version": f"0.{i}.0"} for i in range(10)]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog.json", encoding="utf-8") as fh:
            full = json.load(fh)

        assert len(full) == 10
        # Diff keys must have been stripped
        for entry in full:
            assert "diff" not in entry


# ---------------------------------------------------------------------------
# Corrupt / malformed patches.json
# ---------------------------------------------------------------------------


class TestCorruptPatchesJson:
    def test_corrupt_json_falls_back_to_empty(self, tmp_path, capsys):
        patches_file = tmp_path / "patches.json"
        patches_file.write_text("{{{not valid json}}}", encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        # Should have warned and generated empty files
        captured = capsys.readouterr()
        assert "ERROR" in captured.out or "WARN" in captured.out

        with open(tmp_path / "changelog.json", encoding="utf-8") as fh:
            assert json.load(fh) == []

    def test_zero_patches_produces_one_empty_page(self, tmp_path):
        patches_file = tmp_path / "patches.json"
        patches_file.write_text("[]", encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_index.json", encoding="utf-8") as fh:
            index = json.load(fh)

        # math.ceil(0/50) = 0, but max(1, 0) = 1 → 1 page always guaranteed
        assert index["total_pages"] == 1
        assert os.path.exists(tmp_path / "changelog_page_1.json")

    def test_large_patch_count_page_math(self, tmp_path):
        """Test with 101 patches to ensure page boundary math is correct."""
        count = 101
        patches = [{"version": f"0.0.{i}"} for i in range(count)]
        patches_file = tmp_path / "patches.json"
        patches_file.write_text(json.dumps(patches), encoding="utf-8")

        with (
            patch.object(build_changelogs, "PATCHES_FILE", str(patches_file)),
            patch.object(build_changelogs, "ROOT_DIR", str(tmp_path)),
        ):
            build_changelogs.main()

        with open(tmp_path / "changelog_index.json", encoding="utf-8") as fh:
            index = json.load(fh)

        expected_pages = math.ceil(count / PAGE_SIZE)
        assert index["total_pages"] == expected_pages
        assert len(index["pages"]) == expected_pages
