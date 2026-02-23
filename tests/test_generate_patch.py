"""
Unit tests for generate_patch.py

Tests the pure utility functions and git-dependent functions (with mocked subprocess).
"""

from unittest.mock import MagicMock, patch

import generate_patch

# ---------------------------------------------------------------------------
# _map_path_to_array — Pure function, no mocking needed
# ---------------------------------------------------------------------------


class TestMapPathToArray:
    """Tests for the DeepDiff path-string parser."""

    def test_simple_key(self):
        result = generate_patch._map_path_to_array("root['mechanics']")
        assert result == ["mechanics"]

    def test_nested_keys(self):
        result = generate_patch._map_path_to_array("root['mechanics']['damage_modifiers']")
        assert result == ["mechanics", "damage_modifiers"]

    def test_integer_index(self):
        result = generate_patch._map_path_to_array("root['mechanics']['spawner'][0]")
        assert result == ["mechanics", "spawner", 0]

    def test_multiple_integer_indices(self):
        result = generate_patch._map_path_to_array("root['list'][2]['nested'][0]")
        assert result == ["list", 2, "nested", 0]

    def test_root_only(self):
        result = generate_patch._map_path_to_array("root")
        assert result == []

    def test_deep_path(self):
        result = generate_patch._map_path_to_array("root['a']['b']['c']['d'][10]")
        assert result == ["a", "b", "c", "d", 10]


# ---------------------------------------------------------------------------
# get_commit_author — requires subprocess mocking
# ---------------------------------------------------------------------------


class TestGetCommitAuthor:
    """Tests for git commit author extraction."""

    def test_returns_human_co_author(self):
        """Should prefer Co-authored-by over commit author."""
        body_result = MagicMock()
        body_result.stdout = "Some commit message\n\nCo-authored-by: Jane Doe <jane@example.com>"

        with patch("generate_patch.subprocess.run", return_value=body_result):
            assert generate_patch.get_commit_author() == "Jane Doe"

    def test_filters_bot_authors(self):
        """Should skip bot co-authors and fall back to commit author."""
        body_result = MagicMock()
        body_result.stdout = "Co-authored-by: dependabot[bot] <dependabot@github.com>"

        author_result = MagicMock()
        author_result.stdout = "Human Dev"

        with patch("generate_patch.subprocess.run", side_effect=[body_result, author_result]):
            assert generate_patch.get_commit_author() == "Human Dev"

    def test_fallback_to_commit_author(self):
        """When no Co-authored-by found, should use git commit author."""
        body_result = MagicMock()
        body_result.stdout = "Just a plain commit message"

        author_result = MagicMock()
        author_result.stdout = "Commit Author"

        with patch("generate_patch.subprocess.run", side_effect=[body_result, author_result]):
            assert generate_patch.get_commit_author() == "Commit Author"

    def test_returns_none_on_error(self):
        """Should return None when git commands fail."""
        import subprocess

        with patch("generate_patch.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            assert generate_patch.get_commit_author() is None


# ---------------------------------------------------------------------------
# get_git_diff_files — requires subprocess + env mocking
# ---------------------------------------------------------------------------


class TestGetGitDiffFiles:
    """Tests for git diff file listing."""

    def test_parses_name_status_output(self):
        """Should parse git diff --name-status output correctly."""
        # Mock the two subprocess calls:
        # 1. git log -1 --format=%H data/patches.json (for before_sha)
        # 2. git diff --name-status before_sha after_sha
        log_result = MagicMock()
        log_result.stdout = "abc123"

        diff_result = MagicMock()
        diff_result.stdout = "M\tdata/units/skeleton.json\nA\tdata/spells/fireball.json\n"

        with (
            patch("generate_patch.subprocess.run", side_effect=[log_result, diff_result]),
            patch.dict("os.environ", {"AFTER_SHA": "def456"}, clear=False),
        ):
            result = generate_patch.get_git_diff_files()
            assert ("M", "data/units/skeleton.json") in result
            assert ("A", "data/spells/fireball.json") in result
            assert len(result) == 2

    def test_filters_non_data_files(self):
        """Should only include files under data/ with .json extension."""
        log_result = MagicMock()
        log_result.stdout = "abc123"

        diff_result = MagicMock()
        diff_result.stdout = "M\tdata/units/skeleton.json\nM\tscripts/build_api.py\nM\tREADME.md\n"

        with (
            patch("generate_patch.subprocess.run", side_effect=[log_result, diff_result]),
            patch.dict("os.environ", {"AFTER_SHA": "def456"}, clear=False),
        ):
            result = generate_patch.get_git_diff_files()
            assert len(result) == 1
            assert result[0] == ("M", "data/units/skeleton.json")

    def test_returns_empty_on_error(self):
        """Should return empty list when git commands fail."""
        import subprocess

        with patch("generate_patch.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = generate_patch.get_git_diff_files()
            assert result == []
