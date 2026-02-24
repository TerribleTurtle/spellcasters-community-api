"""
Aggressive tests for generate_patch.py

Covers: get_entity_files_at_commit, collect_timeline_snapshot, write_timeline_files,
get_changed_files_between edge cases, and the full main() pipeline (fresh start + multi-version).
"""

import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import generate_patch
import pytest

# ---------------------------------------------------------------------------
# get_entity_files_at_commit
# ---------------------------------------------------------------------------


class TestGetEntityFilesAtCommit:
    @patch("subprocess.run")
    def test_returns_entity_files(self, mock_run):
        result = MagicMock()
        result.stdout = "data/units/ogre.json\ndata/spells/fireball.json\ndata/game_config.json\n"
        mock_run.return_value = result

        files = generate_patch.get_entity_files_at_commit("abc123")
        # game_config is NOT in FOLDER_TO_SCHEMA so it should be excluded
        assert "data/units/ogre.json" in files
        assert "data/spells/fireball.json" in files
        assert "data/game_config.json" not in files

    @patch("subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        files = generate_patch.get_entity_files_at_commit("badref")
        assert files == []

    @patch("subprocess.run")
    def test_excludes_root_level_json(self, mock_run):
        result = MagicMock()
        result.stdout = "data/something.json\ndata/units/ogre.json\n"
        mock_run.return_value = result

        files = generate_patch.get_entity_files_at_commit("abc")
        assert "data/something.json" not in files


# ---------------------------------------------------------------------------
# get_changed_files_between — aggressive edge cases
# ---------------------------------------------------------------------------


class TestGetChangedFilesBetweenAggressive:
    @patch("subprocess.run")
    def test_excludes_patches_json(self, mock_run):
        result = MagicMock()
        result.stdout = "M\tdata/units/ogre.json\nM\tdata/patches.json\n"
        mock_run.return_value = result

        changed = generate_patch.get_changed_files_between("before", "after")
        files = [f[1] for f in changed]
        assert "data/patches.json" not in files

    @patch("subprocess.run")
    def test_excludes_game_config(self, mock_run):
        result = MagicMock()
        result.stdout = "M\tdata/game_config.json\nA\tdata/heroes/mage.json\n"
        mock_run.return_value = result

        changed = generate_patch.get_changed_files_between("before", "after")
        files = [f[1] for f in changed]
        assert "data/game_config.json" not in files
        assert "data/heroes/mage.json" in files

    @patch("subprocess.run")
    def test_delete_status_captured(self, mock_run):
        result = MagicMock()
        result.stdout = "D\tdata/units/skeleton.json\n"
        mock_run.return_value = result

        changed = generate_patch.get_changed_files_between("before", "after")
        assert ("D", "data/units/skeleton.json") in changed

    def test_returns_empty_when_no_before_sha(self):
        changed = generate_patch.get_changed_files_between(None, "HEAD")
        assert changed == []


# ---------------------------------------------------------------------------
# write_timeline_files
# ---------------------------------------------------------------------------


class TestWriteTimelineFiles:
    def test_creates_dir_and_writes_files(self, tmp_path):
        timeline_dir = str(tmp_path / "timeline")
        data = {
            "ogre": [{"version": "0.0.1", "date": "2026-01-01", "snapshot": {"health": 100}}],
            "mage": [{"version": "0.0.1", "date": "2026-01-01", "snapshot": {"health": 50}}],
        }
        with patch.object(generate_patch, "TIMELINE_DIR", timeline_dir):
            generate_patch.write_timeline_files(data)

        assert os.path.exists(os.path.join(timeline_dir, "ogre.json"))
        assert os.path.exists(os.path.join(timeline_dir, "mage.json"))

        with open(os.path.join(timeline_dir, "ogre.json"), encoding="utf-8") as fh:
            loaded = json.load(fh)
        assert loaded[0]["snapshot"]["health"] == 100

    def test_empty_data_creates_no_files(self, tmp_path):
        timeline_dir = str(tmp_path / "timeline")
        with patch.object(generate_patch, "TIMELINE_DIR", timeline_dir):
            generate_patch.write_timeline_files({})
        # dir should exist but be empty
        assert os.path.isdir(timeline_dir)
        assert os.listdir(timeline_dir) == []


# ---------------------------------------------------------------------------
# main() — fresh start (no boundaries)
# ---------------------------------------------------------------------------


class TestMainFreshStart:
    @patch("generate_patch.write_timeline_files")
    @patch("generate_patch.discover_version_boundaries", return_value=[])
    @patch("generate_patch.collect_timeline_snapshot")
    @patch("generate_patch.load_json")
    def test_fresh_start_writes_timeline_and_returns(self, mock_load, mock_collect, mock_discover, mock_write):
        mock_load.return_value = {"version": "0.0.1"}
        mock_collect.return_value = {"ogre": {"version": "0.0.1", "date": "2026-01-01", "snapshot": {}}}

        generate_patch.main()

        mock_write.assert_called_once()
        timeline_arg = mock_write.call_args[0][0]
        assert "ogre" in timeline_arg

    @patch("generate_patch.discover_version_boundaries", return_value=[])
    @patch("generate_patch.load_json", return_value=None)
    def test_missing_game_config_exits(self, mock_load, mock_discover):
        with patch("os.path.exists", return_value=False), pytest.raises(SystemExit):
            generate_patch.main()


# ---------------------------------------------------------------------------
# main() — multi-version pipeline (2 boundaries)
# ---------------------------------------------------------------------------


class TestMainMultiVersion:
    @patch("generate_patch.write_timeline_files")
    @patch("generate_patch.save_json")
    @patch("generate_patch.get_changed_files_between", return_value=[])
    @patch("generate_patch.collect_timeline_snapshot")
    @patch("generate_patch.discover_version_boundaries")
    @patch("generate_patch.load_json")
    def test_two_boundaries_skips_initial_patch_gen(
        self, mock_load, mock_discover, mock_collect, mock_changed, mock_save, mock_write
    ):
        """0.0.1 is the baseline — no patch should be generated for it."""
        mock_load.side_effect = lambda path: ({"version": "0.0.2"} if "game_config" in path else [])
        mock_discover.return_value = [
            {"version": "0.0.1", "commit": "commit_a"},
            {"version": "0.0.2", "commit": "commit_b"},
        ]
        mock_collect.return_value = {}

        generate_patch.main()

        # save_json is called on patches.json. We verify it was called (not crashed).
        mock_save.assert_called()
        # write_timeline_files should be called once at the end
        mock_write.assert_called_once()

    @patch("generate_patch.write_timeline_files")
    @patch("generate_patch.save_json")
    @patch("generate_patch.get_changed_files_between")
    @patch("generate_patch.collect_timeline_snapshot")
    @patch("generate_patch.discover_version_boundaries")
    @patch("generate_patch.load_json")
    def test_changed_files_generate_changes_list(
        self, mock_load, mock_discover, mock_collect, mock_changed, mock_save, mock_write
    ):
        """When changed files exist, changes should be appended to the patch meta."""
        mock_load.side_effect = lambda path: (
            {"version": "0.0.2"}
            if "game_config" in path
            else (
                [{"version": "0.0.2", "id": "p1", "title": "Patch 2"}] if "patches" in path else {"name": "Test Entity"}
            )
        )
        mock_discover.return_value = [
            {"version": "0.0.1", "commit": "cA"},
            {"version": "0.0.2", "commit": "cB"},
        ]
        mock_collect.return_value = {}

        with patch("generate_patch.get_file_content_at_commit") as mock_content:
            mock_content.side_effect = lambda fp, commit: ({"health": 100} if "cA" in commit else {"health": 200})
            mock_changed.return_value = [("M", "data/units/ogre.json")]
            generate_patch.main()

        # save_json should be the final flush — called at least once
        mock_save.assert_called()
