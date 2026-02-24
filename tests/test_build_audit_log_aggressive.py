"""
Aggressive tests for build_audit_log.py

Covers: rename/type-change handling, dual-None entity skip, missing git commit
errors, git log format edge cases, empty-commit filtering, and output file
structure.
"""

import json
import subprocess
from unittest.mock import mock_open, patch

import build_audit_log

# ---------------------------------------------------------------------------
# is_entity_file — exhaustive boundary cases
# ---------------------------------------------------------------------------


class TestIsEntityFileAggressive:
    def test_nested_subfolder_is_entity(self):
        # data/heroes/archmage.json → nested, valid entity
        assert build_audit_log.is_entity_file("data/heroes/archmage.json") is True

    def test_windows_backslash_excluded(self):
        # Exclusion list uses forward-slash normalisation
        assert build_audit_log.is_entity_file("data\\game_config.json") is False

    def test_queue_json_excluded(self):
        assert build_audit_log.is_entity_file("data/queue.json") is False

    def test_changelog_json_excluded(self):
        assert build_audit_log.is_entity_file("data/changelog.json") is False

    def test_changelog_index_excluded(self):
        assert build_audit_log.is_entity_file("data/changelog_index.json") is False

    def test_changelog_latest_excluded(self):
        assert build_audit_log.is_entity_file("data/changelog_latest.json") is False

    def test_non_json_excluded(self):
        assert build_audit_log.is_entity_file("data/units/readme.txt") is False

    def test_root_level_json_excluded(self):
        # data/something.json has only 2 parts — missing category folder
        assert build_audit_log.is_entity_file("data/something.json") is False

    def test_empty_string_excluded(self):
        assert build_audit_log.is_entity_file("") is False

    def test_scripts_file_excluded(self):
        assert build_audit_log.is_entity_file("scripts/build_api.py") is False


# ---------------------------------------------------------------------------
# parse_git_log — rename handling and edge cases
# ---------------------------------------------------------------------------


class TestParseGitLogAggressive:
    @patch("subprocess.run")
    def test_rename_entry_is_included(self, mock_run):
        """A Rxx rename status line should be captured as a file change."""
        log = """\
COMMIT|ren_commit|2024-01-01T00:00:00Z|Dev|Rename unit
R100\tdata/units/old_name.json\tdata/units/new_name.json
"""

        class MockProc:
            stdout = log

        mock_run.return_value = MockProc()
        commits = build_audit_log.parse_git_log()
        assert len(commits) == 1
        # The last path token is what we care about, matching is_entity_file
        statuses = [f[0] for f in commits[0]["files"]]
        assert any("R" in s for s in statuses)

    @patch("subprocess.run")
    def test_empty_log_returns_empty_list(self, mock_run):
        class MockProc:
            stdout = ""

        mock_run.return_value = MockProc()
        assert build_audit_log.parse_git_log() == []

    @patch("subprocess.run")
    def test_commit_with_no_entity_files_is_filtered(self, mock_run):
        """A commit that only touches non-entity files should not appear."""
        log = """\
COMMIT|abc123|2024-01-01T00:00:00Z|Dev|Change config only
M\tdata/game_config.json
"""

        class MockProc:
            stdout = log

        mock_run.return_value = MockProc()
        commits = build_audit_log.parse_git_log()
        assert commits == []

    @patch("subprocess.run")
    def test_git_error_returns_empty_list(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        commits = build_audit_log.parse_git_log()
        assert commits == []

    @patch("subprocess.run")
    def test_malformed_commit_line_is_ignored(self, mock_run):
        """A COMMIT line with fewer than 5 pipe-delimited fields should be skipped."""
        log = """\
COMMIT|short|line
M\tdata/units/ogre.json
"""

        class MockProc:
            stdout = log

        mock_run.return_value = MockProc()
        commits = build_audit_log.parse_git_log()
        assert commits == []


# ---------------------------------------------------------------------------
# build_audit_log — logical / output correctness
# ---------------------------------------------------------------------------


class TestBuildAuditLogLogic:
    @patch("build_audit_log.parse_git_log")
    @patch("build_audit_log.get_file_content_at_commit")
    @patch("builtins.open", new_callable=mock_open)
    def test_rename_treated_as_rename_type(self, mock_file, mock_get_content, mock_parse):
        """A file with R status should produce change_type='rename'."""
        mock_parse.return_value = [
            {
                "commit": "ren_hash",
                "timestamp": "2024-01-01T00:00:00Z",
                "author": "Dev",
                "message": "Rename",
                "files": [("R100", "data/units/new_name.json")],
            }
        ]

        def content_side_effect(filepath, commit):
            if "ren_hash~1" in commit:
                return {"name": "Old Name", "health": 100}
            return {"name": "New Name", "health": 100}

        mock_get_content.side_effect = content_side_effect

        build_audit_log.build_audit_log()

        written = "".join(c.args[0] for c in mock_file().write.call_args_list)
        data = json.loads(written)
        assert data[0]["changes"][0]["change_type"] == "rename"

    @patch("build_audit_log.parse_git_log")
    @patch("build_audit_log.get_file_content_at_commit")
    @patch("builtins.open", new_callable=mock_open)
    def test_both_none_content_is_skipped(self, mock_file, mock_get_content, mock_parse):
        """If both old and new content are None, that entity should not appear in the output."""
        mock_parse.return_value = [
            {
                "commit": "ghost_commit",
                "timestamp": "2024-01-01T00:00:00Z",
                "author": "Dev",
                "message": "Ghost",
                "files": [("M", "data/units/ghost.json")],
            }
        ]
        mock_get_content.return_value = None  # Always None → skip

        build_audit_log.build_audit_log()

        written = "".join(c.args[0] for c in mock_file().write.call_args_list)
        data = json.loads(written)
        # Ghost entity should produce 0 audit entries (no valid diff)
        assert data == []

    @patch("build_audit_log.parse_git_log")
    @patch("build_audit_log.get_file_content_at_commit")
    @patch("builtins.open", new_callable=mock_open)
    def test_output_json_is_minified(self, mock_file, mock_get_content, mock_parse):
        """Output JSON should be compact (separators=(',', ':')) to save space."""
        mock_parse.return_value = [
            {
                "commit": "c1",
                "timestamp": "2024-01-01T00:00:00Z",
                "author": "Dev",
                "message": "Add",
                "files": [("A", "data/units/ogre.json")],
            }
        ]
        mock_get_content.return_value = {"name": "Ogre", "health": 500}

        build_audit_log.build_audit_log()

        written = "".join(c.args[0] for c in mock_file().write.call_args_list)
        # Minified JSON has no spaces after : or ,
        assert ": " not in written, "Output JSON should be minified, not pretty-printed"

    @patch("build_audit_log.parse_git_log")
    @patch("build_audit_log.get_file_content_at_commit")
    @patch("builtins.open", new_callable=mock_open)
    def test_audit_entry_contains_required_fields(self, mock_file, mock_get_content, mock_parse):
        """Every audit entry must contain commit, timestamp, author, message, changes."""
        mock_parse.return_value = [
            {
                "commit": "abc",
                "timestamp": "2024-06-01T00:00:00Z",
                "author": "Wizard",
                "message": "Buff ogre",
                "files": [("M", "data/units/ogre.json")],
            }
        ]

        def content(fp, commit):
            if "~1" in commit:
                return {"health": 100}
            return {"health": 200}

        mock_get_content.side_effect = content
        build_audit_log.build_audit_log()

        written = "".join(c.args[0] for c in mock_file().write.call_args_list)
        data = json.loads(written)
        entry = data[0]

        for field in ("commit", "timestamp", "author", "message", "changes"):
            assert field in entry, f"Required field '{field}' missing from audit entry"

    @patch("build_audit_log.parse_git_log")
    @patch("build_audit_log.get_file_content_at_commit")
    @patch("builtins.open", new_callable=mock_open)
    def test_change_entry_contains_required_fields(self, mock_file, mock_get_content, mock_parse):
        """Each change inside an entry must have entity_id, file, category, change_type, diffs."""
        mock_parse.return_value = [
            {
                "commit": "abc",
                "timestamp": "2024-06-01T00:00:00Z",
                "author": "Dev",
                "message": "Edit",
                "files": [("M", "data/titans/kraken.json")],
            }
        ]

        def content(fp, commit):
            return {"health": 100} if "~1" in commit else {"health": 999}

        mock_get_content.side_effect = content
        build_audit_log.build_audit_log()

        written = "".join(c.args[0] for c in mock_file().write.call_args_list)
        data = json.loads(written)
        change = data[0]["changes"][0]

        for field in ("entity_id", "file", "category", "change_type", "diffs"):
            assert field in change, f"Required field '{field}' missing from change entry"

        assert change["entity_id"] == "kraken"
        assert change["category"] == "titans"
        assert change["change_type"] == "edit"
