import json
from unittest.mock import mock_open, patch

import build_audit_log

# Sample mocked git log output
MOCKED_GIT_LOG = """COMMIT|commit3_delete|2023-01-03T12:00:00Z|Dev|Delete skeleton
D\tdata/units/skeleton.json
COMMIT|commit2_edit|2023-01-02T12:00:00Z|Dev|Update skeleton
M\tdata/units/skeleton.json
A\tdata/spells/fireball.json
COMMIT|commit1_add_first|2023-01-01T12:00:00Z|Dev|Initial commit
A\tdata/units/skeleton.json
"""


@patch("subprocess.run")
def test_parse_git_log(mock_run):
    """Verifies that parse_git_log correctly parses the output of git log."""

    class MockProcess:
        stdout = MOCKED_GIT_LOG

    mock_run.return_value = MockProcess()

    commits = build_audit_log.parse_git_log()

    # We should have 3 commits parsed
    assert len(commits) == 3

    # Newest commit first
    assert commits[0]["commit"] == "commit3_delete"
    assert commits[0]["author"] == "Dev"
    assert len(commits[0]["files"]) == 1
    assert commits[0]["files"][0] == ("D", "data/units/skeleton.json")

    # Second commit
    assert commits[1]["commit"] == "commit2_edit"
    assert len(commits[1]["files"]) == 2
    assert commits[1]["files"][0] == ("M", "data/units/skeleton.json")
    assert commits[1]["files"][1] == ("A", "data/spells/fireball.json")

    # First commit
    assert commits[2]["commit"] == "commit1_add_first"
    assert len(commits[2]["files"]) == 1


@patch("build_audit_log.parse_git_log")
@patch("build_audit_log.get_file_content_at_commit")
@patch("builtins.open", new_callable=mock_open)
def test_build_audit_log_end_to_end(mock_file, mock_get_content, mock_parse):
    """Verifies that build_audit_log orchestrates diffing and outputs correctly."""

    # Setup the mock parsed commits (already tested above)
    mock_parse.return_value = [
        {
            "commit": "commit3_delete",
            "timestamp": "2023-01-03T12:00:00Z",
            "author": "Dev",
            "message": "Delete",
            "files": [("D", "data/units/skeleton.json")],
        },
        {
            "commit": "commit2_edit",
            "timestamp": "2023-01-02T12:00:00Z",
            "author": "Dev",
            "message": "Edit",
            "files": [("M", "data/units/skeleton.json"), ("A", "data/spells/fireball.json")],
        },
        {
            "commit": "commit1_add",
            "timestamp": "2023-01-01T12:00:00Z",
            "author": "Dev",
            "message": "First",
            "files": [("A", "data/units/skeleton.json")],
        },
    ]

    # Mock the file contents at specific commits
    # commit3: delete skeleton (content is None) -- old content is fetched from commit3~1
    # commit2: edit skeleton (health: 200), add fireball -- old skeleton is health: 100
    # commit1: add skeleton (health: 100) -- old content is None

    def side_effect_get_content(filepath, commit_hash):
        # commit3_delete
        if commit_hash == "commit3_delete~1" and "skeleton" in filepath:
            return {"health": 200}

        # commit2_edit
        if commit_hash == "commit2_edit" and "skeleton" in filepath:
            return {"health": 200}
        if commit_hash == "commit2_edit~1" and "skeleton" in filepath:
            return {"health": 100}

        if commit_hash == "commit2_edit" and "fireball" in filepath:
            return {"damage": 50}

        # commit1_add
        if commit_hash == "commit1_add" and "skeleton" in filepath:
            return {"health": 100}

        return None

    mock_get_content.side_effect = side_effect_get_content

    # Run the builder
    build_audit_log.build_audit_log()

    # Capture what was written to the file
    written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
    audit_json = json.loads(written_data)

    assert len(audit_json) == 3

    # Check commit 3 (Delete)
    c3 = audit_json[0]
    assert c3["commit"] == "commit3_delete"
    assert len(c3["changes"]) == 1
    assert c3["changes"][0]["entity_id"] == "skeleton"
    assert c3["changes"][0]["change_type"] == "delete"

    # Check commit 2 (Edit and Add)
    c2 = audit_json[1]
    assert c2["commit"] == "commit2_edit"
    assert len(c2["changes"]) == 2

    skeleton_change = next(c for c in c2["changes"] if c["entity_id"] == "skeleton")
    assert skeleton_change["change_type"] == "edit"
    assert skeleton_change["diffs"][0]["path"] == ["health"]
    assert skeleton_change["diffs"][0]["old_value"] == 100
    assert skeleton_change["diffs"][0]["new_value"] == 200

    fireball_change = next(c for c in c2["changes"] if c["entity_id"] == "fireball")
    assert fireball_change["change_type"] == "add"

    # Check commit 1 (First Add)
    c1 = audit_json[2]
    assert c1["commit"] == "commit1_add"
    assert len(c1["changes"]) == 1
    assert c1["changes"][0]["entity_id"] == "skeleton"
    assert c1["changes"][0]["change_type"] == "add"


def test_is_entity_file_exclusions():
    """Verifies that non-entity data files are properly ignored."""
    assert build_audit_log.is_entity_file("data/units/ogre.json") is True

    # Exclusions
    assert build_audit_log.is_entity_file("data/game_config.json") is False
    assert build_audit_log.is_entity_file("data/patches.json") is False
    assert build_audit_log.is_entity_file("data/audit.json") is False
    assert build_audit_log.is_entity_file("data/changelog.json") is False

    # Not JSON
    assert build_audit_log.is_entity_file("data/units/readme.md") is False

    # Not in data/
    assert build_audit_log.is_entity_file("src/index.js") is False

    # Root data folder files (even if JSON)
    assert build_audit_log.is_entity_file("data/something.json") is False
