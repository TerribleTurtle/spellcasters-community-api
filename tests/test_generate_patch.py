"""
Unit tests for generate_patch.py (Stateless Architecture)

Tests the pure utility functions and git-dependent functions (with mocked subprocess).
"""

from unittest.mock import MagicMock, patch

import generate_patch

# ---------------------------------------------------------------------------
# compute_diff — Pure function, no mocking needed
# ---------------------------------------------------------------------------


class TestComputeDiff:
    """Tests for the DeepDiff parser and formatter."""

    def test_item_added(self):
        old = {"stats": {"health": 100}}
        new = {"stats": {"health": 100, "attack": 50}}
        diffs = generate_patch.compute_diff(old, new)

        assert len(diffs) == 1
        assert diffs[0]["path"] == ["stats", "attack"]
        assert diffs[0]["new_value"] == 50

    def test_item_removed(self):
        old = {"stats": {"health": 100, "attack": 50}}
        new = {"stats": {"health": 100}}
        diffs = generate_patch.compute_diff(old, new)

        assert len(diffs) == 1
        assert diffs[0]["path"] == ["stats", "attack"]
        assert diffs[0].get("removed") is True

    def test_value_changed(self):
        old = {"stats": {"health": 100}}
        new = {"stats": {"health": 150}}
        diffs = generate_patch.compute_diff(old, new)

        assert len(diffs) == 1
        assert diffs[0]["path"] == ["stats", "health"]
        assert diffs[0]["old_value"] == 100
        assert diffs[0]["new_value"] == 150

    def test_iterable_item_added(self):
        old = {"tags": ["fire"]}
        new = {"tags": ["fire", "magic"]}
        diffs = generate_patch.compute_diff(old, new)

        assert len(diffs) == 1
        assert diffs[0]["path"] == ["tags", 1]
        assert diffs[0]["new_value"] == "magic"

    def test_ignores_last_modified(self):
        old = {"last_modified": "2024-01-01", "stats": {"health": 100}}
        new = {"last_modified": "2024-01-02", "stats": {"health": 100}}
        diffs = generate_patch.compute_diff(old, new)

        # Should be empty because last_modified is excluded
        assert len(diffs) == 0


# ---------------------------------------------------------------------------
# get_changed_files_between — requires subprocess mocking
# ---------------------------------------------------------------------------


class TestGetChangedFilesBetween:
    """Tests for git diff file listing."""

    @patch("subprocess.run")
    def test_parses_name_status_output(self, mock_run):
        """Should parse git diff --name-status output correctly."""
        result = MagicMock()
        result.stdout = "M\tdata/units/skeleton.json\nA\tdata/spells/fireball.json\n"
        mock_run.return_value = result

        changed = generate_patch.get_changed_files_between("before", "after")
        assert ("M", "data/units/skeleton.json") in changed
        assert ("A", "data/spells/fireball.json") in changed
        assert len(changed) == 2

    @patch("subprocess.run")
    def test_filters_non_data_files(self, mock_run):
        """Should only include files under data/ with .json extension."""
        result = MagicMock()
        result.stdout = "M\tdata/units/skeleton.json\nM\tscripts/build_api.py\nM\tREADME.md\n"
        mock_run.return_value = result

        changed = generate_patch.get_changed_files_between("before", "after")
        assert len(changed) == 1
        assert changed[0] == ("M", "data/units/skeleton.json")

    @patch("subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        """Should return empty list when git commands fail."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        changed = generate_patch.get_changed_files_between("before", "after")
        assert changed == []


# ---------------------------------------------------------------------------
# discover_version_boundaries — requires subprocess mocking
# ---------------------------------------------------------------------------


class TestDiscoverVersionBoundaries:
    @patch("subprocess.run")
    def test_parses_git_log_and_show(self, mock_run):
        # First call gets commit SHAs
        log_result = MagicMock()
        log_result.stdout = "commit1\ncommit2\n"

        # Second call gets game_config for commit1
        show1_result = MagicMock()
        show1_result.stdout = '{"version": "0.0.1"}'

        # Third call gets game_config for commit2
        show2_result = MagicMock()
        show2_result.stdout = '{"version": "0.0.2"}'

        mock_run.side_effect = [log_result, show1_result, show2_result]

        boundaries = generate_patch.discover_version_boundaries("1.0.0")
        assert len(boundaries) == 2
        assert boundaries[0] == {"version": "0.0.1", "commit": "commit1"}
        assert boundaries[1] == {"version": "0.0.2", "commit": "commit2"}

    @patch("subprocess.run")
    def test_ignores_commits_that_dont_change_version(self, mock_run):
        log_result = MagicMock()
        log_result.stdout = "commit1\ncommit1_fix\ncommit2\n"

        show1_result = MagicMock()
        show1_result.stdout = '{"version": "0.0.1"}'

        show1_fix_result = MagicMock()
        show1_fix_result.stdout = '{"version": "0.0.1"}'

        show2_result = MagicMock()
        show2_result.stdout = '{"version": "0.0.2"}'

        mock_run.side_effect = [log_result, show1_result, show1_fix_result, show2_result]

        boundaries = generate_patch.discover_version_boundaries("1.0.0")
        assert len(boundaries) == 2
        assert boundaries[0] == {"version": "0.0.1", "commit": "commit1"}  # Only first commit for 0.0.1
        assert boundaries[1] == {"version": "0.0.2", "commit": "commit2"}

    @patch("subprocess.run")
    def test_ignores_future_versions(self, mock_run):
        log_result = MagicMock()
        log_result.stdout = "commit1\ncommit2\n"

        show1_result = MagicMock()
        show1_result.stdout = '{"version": "0.0.1"}'

        show2_result = MagicMock()
        show2_result.stdout = '{"version": "0.0.4"}'

        mock_run.side_effect = [log_result, show1_result, show2_result]

        # Current version is 0.0.1, so it should ignore 0.0.4
        boundaries = generate_patch.discover_version_boundaries("0.0.1")
        assert len(boundaries) == 1
        assert boundaries[0] == {"version": "0.0.1", "commit": "commit1"}
