"""
Integration Tests for generate_patch.py — Testing the Contract

These tests verify that the COMPLETE pipeline (main function) produces the correct
observable output given a controlled git history. They don't test individual functions;
they test that the assembled machine produces the right artifacts.

Design pattern: "Testing the Contract"
- We mock the git subprocess layer to simulate a multi-version history
- We use tmp_path for all file I/O
- We assert the CONTRACT of the output, not the implementation details

Simulated history:
  0.0.1 (baseline) → 0.0.2 (skeleton buffed) → 0.0.3 (fireball added, skeleton nerfed)
"""

import json
import os
from unittest.mock import MagicMock, patch

import generate_patch
import pytest

# ---------------------------------------------------------------------------
# Fixtures: Simulated game world
# ---------------------------------------------------------------------------

SKELETON_V1 = {"entity_id": "skeleton", "name": "Skeleton", "health": 100, "damage": 20}
SKELETON_V2 = {"entity_id": "skeleton", "name": "Skeleton", "health": 150, "damage": 25}  # buffed
SKELETON_V3 = {"entity_id": "skeleton", "name": "Skeleton", "health": 120, "damage": 30}  # rebalanced
FIREBALL_V3 = {"entity_id": "fireball", "name": "Fireball", "mana_cost": 5, "damage": 100}  # added in 0.0.3

GAME_CONFIG_V1 = {"version": "0.0.1"}
GAME_CONFIG_V2 = {"version": "0.0.2"}
GAME_CONFIG_V3 = {"version": "0.0.3"}


def make_git_show_response(data):
    """Creates a MagicMock for subprocess.run that returns JSON."""
    m = MagicMock()
    m.stdout = json.dumps(data)
    m.returncode = 0
    return m


def make_git_diff_response(lines):
    """Creates a MagicMock for git diff --name-status output."""
    m = MagicMock()
    m.stdout = "\n".join(lines) + "\n"
    m.returncode = 0
    return m


def make_git_log_response(commits):
    """Creates a MagicMock for git log output."""
    m = MagicMock()
    m.stdout = "\n".join(commits) + "\n"
    m.returncode = 0
    return m


def make_ls_tree_response(files):
    """Creates a MagicMock for git ls-tree output."""
    m = MagicMock()
    m.stdout = "\n".join(files) + "\n"
    m.returncode = 0
    return m


@pytest.fixture
def pipeline_env(tmp_path):
    """Sets up a complete isolated environment for running main()."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    units_dir = data_dir / "units"
    units_dir.mkdir()
    spells_dir = data_dir / "spells"
    spells_dir.mkdir()
    timeline_dir = tmp_path / "timeline"

    # Write the "current" game_config (version 0.0.3)
    game_config_path = data_dir / "game_config.json"
    game_config_path.write_text(json.dumps(GAME_CONFIG_V3), encoding="utf-8")

    # Write the "current" entity files on disk (as they appear at HEAD)
    (units_dir / "skeleton.json").write_text(json.dumps(SKELETON_V3), encoding="utf-8")
    (spells_dir / "fireball.json").write_text(json.dumps(FIREBALL_V3), encoding="utf-8")

    # Write empty patches.json
    patches_path = data_dir / "patches.json"
    patches_path.write_text("[]", encoding="utf-8")

    return {
        "tmp_path": tmp_path,
        "data_dir": str(data_dir),
        "game_config_path": str(game_config_path),
        "patches_path": str(patches_path),
        "timeline_dir": str(timeline_dir),
    }


def build_subprocess_router(pipeline_env):
    """Builds a side_effect function that routes subprocess.run calls to the correct mock.

    This simulates a 3-version git history:
      commit_a = 0.0.1 (skeleton exists)
      commit_b = 0.0.2 (skeleton buffed)
      commit_c = 0.0.3 (skeleton rebalanced, fireball added)
    """
    call_log = []

    def router(cmd, **kwargs):
        cmd_str = " ".join(cmd)
        call_log.append(cmd_str)

        # git log --reverse --format=%H data/game_config.json
        if "git log" in cmd_str and "game_config.json" in cmd_str:
            return make_git_log_response(["commit_a", "commit_b", "commit_c"])

        # git show {commit}:data/game_config.json
        if "git show" in cmd_str and "game_config.json" in cmd_str:
            if "commit_a:" in cmd_str:
                return make_git_show_response(GAME_CONFIG_V1)
            elif "commit_b:" in cmd_str:
                return make_git_show_response(GAME_CONFIG_V2)
            elif "commit_c:" in cmd_str:
                return make_git_show_response(GAME_CONFIG_V3)

        # git show {commit}:data/units/skeleton.json
        if "git show" in cmd_str and "skeleton.json" in cmd_str:
            if "commit_a:" in cmd_str:
                return make_git_show_response(SKELETON_V1)
            elif "commit_b:" in cmd_str or "commit_b~1:" in cmd_str:
                return make_git_show_response(SKELETON_V2)
            elif "commit_c:" in cmd_str:
                return make_git_show_response(SKELETON_V3)

        # git show {commit}:data/spells/fireball.json
        if "git show" in cmd_str and "fireball.json" in cmd_str:
            if "commit_a:" in cmd_str or "commit_b:" in cmd_str:
                # Fireball doesn't exist in v1 or v2
                raise __import__("subprocess").CalledProcessError(128, "git")
            elif "commit_c:" in cmd_str:
                return make_git_show_response(FIREBALL_V3)

        # git diff --name-status commit_a commit_b~1
        if "git diff" in cmd_str and "commit_a" in cmd_str:
            return make_git_diff_response(["M\tdata/units/skeleton.json"])

        # git diff --name-status commit_b HEAD
        if "git diff" in cmd_str and "commit_b" in cmd_str:
            return make_git_diff_response(
                [
                    "M\tdata/units/skeleton.json",
                    "A\tdata/spells/fireball.json",
                ]
            )

        # git ls-tree -r --name-only {commit} data/
        if "git ls-tree" in cmd_str:
            if "commit_a" in cmd_str:
                return make_ls_tree_response(["data/units/skeleton.json"])
            elif "commit_b" in cmd_str:
                return make_ls_tree_response(["data/units/skeleton.json"])
            elif "commit_c" in cmd_str:
                return make_ls_tree_response(
                    [
                        "data/units/skeleton.json",
                        "data/spells/fireball.json",
                    ]
                )

        # Default: empty response
        m = MagicMock()
        m.stdout = ""
        m.returncode = 0
        return m

    return router, call_log


# ===========================================================================
# Integration Tests: Full Pipeline Contract
# ===========================================================================


class TestMainPipelineContract:
    """Tests the complete pipeline's observable output."""

    def _run_pipeline(self, pipeline_env):
        """Runs main() with all paths patched to use tmp_path."""
        router, call_log = build_subprocess_router(pipeline_env)

        with (
            patch("subprocess.run", side_effect=router),
            patch.object(generate_patch, "GAME_CONFIG_PATH", pipeline_env["game_config_path"]),
            patch.object(generate_patch, "PATCHES_FILE", pipeline_env["patches_path"]),
            patch.object(generate_patch, "TIMELINE_DIR", pipeline_env["timeline_dir"]),
            patch.object(generate_patch.config, "DATA_DIR", pipeline_env["data_dir"]),
            patch.object(generate_patch.config, "BASE_DIR", str(pipeline_env["tmp_path"])),
        ):
            generate_patch.main()

        return call_log

    def test_patches_json_has_correct_version_entries(self, pipeline_env):
        """patches.json should have entries for 0.0.2 and 0.0.3, NOT 0.0.1."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        versions = [p["version"] for p in patches]

        assert "0.0.1" not in versions, "0.0.1 baseline should NEVER appear in patches"
        assert "0.0.2" in versions, "0.0.2 should have a patch entry"
        assert "0.0.3" in versions, "0.0.3 should have a patch entry"

    def test_patch_002_has_skeleton_buff(self, pipeline_env):
        """The 0.0.2 patch should contain the skeleton health/damage buff."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        patch_002 = next(p for p in patches if p["version"] == "0.0.2")

        assert "changes" in patch_002
        assert len(patch_002["changes"]) > 0

        skeleton_change = next((c for c in patch_002["changes"] if c["target_id"] == "skeleton.json"), None)
        assert skeleton_change is not None, "Skeleton should be in 0.0.2 changes"
        assert skeleton_change["change_type"] == "edit"
        assert skeleton_change["category"] == "units"

        # Verify diffs contain health and damage changes
        diff_paths = [tuple(d["path"]) for d in skeleton_change["diffs"]]
        assert ("health",) in diff_paths
        assert ("damage",) in diff_paths

    def test_patch_003_has_fireball_addition(self, pipeline_env):
        """The 0.0.3 patch should contain the fireball addition."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        patch_003 = next(p for p in patches if p["version"] == "0.0.3")

        fireball_change = next((c for c in patch_003["changes"] if c["target_id"] == "fireball.json"), None)
        assert fireball_change is not None, "Fireball should be in 0.0.3 changes"
        assert fireball_change["change_type"] == "add"
        assert fireball_change["category"] == "spells"

    def test_patch_003_has_skeleton_rebalance(self, pipeline_env):
        """The 0.0.3 patch should also contain skeleton rebalance."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        patch_003 = next(p for p in patches if p["version"] == "0.0.3")

        skeleton_change = next((c for c in patch_003["changes"] if c["target_id"] == "skeleton.json"), None)
        assert skeleton_change is not None

    def test_patch_entries_have_required_metadata(self, pipeline_env):
        """Each patch entry should have id, version, date, type, title, tags, changes."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        for p in patches:
            assert "id" in p
            assert "version" in p
            assert "date" in p
            assert "type" in p
            assert "title" in p
            assert "tags" in p
            assert "changes" in p
            assert isinstance(p["changes"], list)

    def test_timeline_skeleton_has_all_versions(self, pipeline_env):
        """timeline/skeleton.json should have snapshots for 0.0.1, 0.0.2, and 0.0.3."""
        self._run_pipeline(pipeline_env)

        timeline_path = os.path.join(pipeline_env["timeline_dir"], "skeleton.json")
        assert os.path.exists(timeline_path), "Skeleton timeline should exist"

        timeline = json.loads(open(timeline_path, encoding="utf-8").read())
        assert isinstance(timeline, list)

        versions_in_timeline = [t["version"] for t in timeline]
        assert "0.0.1" in versions_in_timeline, "Baseline 0.0.1 SHOULD be in timeline"
        assert "0.0.2" in versions_in_timeline
        assert "0.0.3" in versions_in_timeline

    def test_timeline_fireball_only_exists_from_v3(self, pipeline_env):
        """timeline/fireball.json should only have a 0.0.3 snapshot (it didn't exist before)."""
        self._run_pipeline(pipeline_env)

        timeline_path = os.path.join(pipeline_env["timeline_dir"], "fireball.json")
        assert os.path.exists(timeline_path), "Fireball timeline should exist"

        timeline = json.loads(open(timeline_path, encoding="utf-8").read())
        versions_in_timeline = [t["version"] for t in timeline]
        assert "0.0.1" not in versions_in_timeline
        assert "0.0.2" not in versions_in_timeline
        assert "0.0.3" in versions_in_timeline

    def test_timeline_snapshots_contain_actual_data(self, pipeline_env):
        """Each timeline snapshot should contain the full entity data at that version."""
        self._run_pipeline(pipeline_env)

        timeline_path = os.path.join(pipeline_env["timeline_dir"], "skeleton.json")
        timeline = json.loads(open(timeline_path, encoding="utf-8").read())

        # Find the 0.0.1 snapshot and verify it has the original stats
        v1_snap = next(t for t in timeline if t["version"] == "0.0.1")
        assert v1_snap["snapshot"]["health"] == SKELETON_V1["health"]

    def test_timeline_entries_have_required_fields(self, pipeline_env):
        """Each timeline entry should have version, date, and snapshot."""
        self._run_pipeline(pipeline_env)

        for fname in os.listdir(pipeline_env["timeline_dir"]):
            if not fname.endswith(".json"):
                continue
            timeline = json.loads(open(os.path.join(pipeline_env["timeline_dir"], fname), encoding="utf-8").read())
            for entry in timeline:
                assert "version" in entry
                assert "date" in entry
                assert "snapshot" in entry
                assert isinstance(entry["snapshot"], dict)

    def test_no_patches_json_pollution_from_baseline(self, pipeline_env):
        """The 0.0.1 baseline should NEVER create a patch entry, only timeline."""
        self._run_pipeline(pipeline_env)

        patches = json.loads(open(pipeline_env["patches_path"], encoding="utf-8").read())
        baseline_patches = [p for p in patches if p["version"] == "0.0.1"]
        assert len(baseline_patches) == 0


# ===========================================================================
# Edge Case Integration Tests
# ===========================================================================


class TestMainPipelineEdgeCases:
    """Edge cases for the complete pipeline."""

    def test_single_version_baseline_only(self, tmp_path):
        """With only version 0.0.1, patches.json should be empty, timeline should exist."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        units_dir = data_dir / "units"
        units_dir.mkdir()

        game_config_path = data_dir / "game_config.json"
        game_config_path.write_text(json.dumps({"version": "0.0.1"}), encoding="utf-8")
        (units_dir / "skeleton.json").write_text(json.dumps(SKELETON_V1), encoding="utf-8")

        patches_path = data_dir / "patches.json"
        patches_path.write_text("[]", encoding="utf-8")
        timeline_dir = tmp_path / "timeline"

        def router(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "git log" in cmd_str:
                return make_git_log_response(["commit_a"])
            if "git show" in cmd_str and "game_config" in cmd_str:
                return make_git_show_response({"version": "0.0.1"})
            if "git ls-tree" in cmd_str:
                return make_ls_tree_response(["data/units/skeleton.json"])
            if "git show" in cmd_str and "skeleton" in cmd_str:
                return make_git_show_response(SKELETON_V1)
            m = MagicMock()
            m.stdout = ""
            return m

        with (
            patch("subprocess.run", side_effect=router),
            patch.object(generate_patch, "GAME_CONFIG_PATH", str(game_config_path)),
            patch.object(generate_patch, "PATCHES_FILE", str(patches_path)),
            patch.object(generate_patch, "TIMELINE_DIR", str(timeline_dir)),
            patch.object(generate_patch.config, "DATA_DIR", str(data_dir)),
            patch.object(generate_patch.config, "BASE_DIR", str(tmp_path)),
        ):
            generate_patch.main()

        patches = json.loads(patches_path.read_text(encoding="utf-8"))
        assert patches == [], "No patches should exist for baseline-only history"

        timeline_path = timeline_dir / "skeleton.json"
        assert timeline_path.exists(), "Timeline for skeleton should exist even with only baseline"

    def test_empty_git_history(self, tmp_path):
        """With no git history, should still produce timeline from disk."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        units_dir = data_dir / "units"
        units_dir.mkdir()

        game_config_path = data_dir / "game_config.json"
        game_config_path.write_text(json.dumps({"version": "0.0.1"}), encoding="utf-8")
        (units_dir / "skeleton.json").write_text(json.dumps(SKELETON_V1), encoding="utf-8")

        patches_path = data_dir / "patches.json"
        patches_path.write_text("[]", encoding="utf-8")
        timeline_dir = tmp_path / "timeline"

        def router(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "git log" in cmd_str:
                return make_git_log_response([])
            m = MagicMock()
            m.stdout = ""
            return m

        with (
            patch("subprocess.run", side_effect=router),
            patch.object(generate_patch, "GAME_CONFIG_PATH", str(game_config_path)),
            patch.object(generate_patch, "PATCHES_FILE", str(patches_path)),
            patch.object(generate_patch, "TIMELINE_DIR", str(timeline_dir)),
            patch.object(generate_patch.config, "DATA_DIR", str(data_dir)),
            patch.object(generate_patch.config, "BASE_DIR", str(tmp_path)),
        ):
            generate_patch.main()

        # Timeline should still be created from disk
        timeline_path = timeline_dir / "skeleton.json"
        assert timeline_path.exists(), "Timeline should be created from disk even with no git history"
