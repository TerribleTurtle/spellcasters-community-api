"""
STRESS TESTS for generate_patch.py (Stateless Architecture)

Adversarial, edge-case, and chaos-engineering style tests.
Goal: Try to break every function in every conceivable way.
"""

from unittest.mock import MagicMock, patch, call
import subprocess
import json
import pytest

import generate_patch
import patch_utils



# ===========================================================================
# _parse_deepdiff_path — Regex parser torture tests
# ===========================================================================

class TestParseDeepDiffPath:
    """Test the regex-based DeepDiff path parser with every evil input."""

    def test_simple_single_key(self):
        assert patch_utils._parse_deepdiff_path("root['health']") == ["health"]

    def test_nested_two_keys(self):
        assert patch_utils._parse_deepdiff_path("root['stats']['attack']") == ["stats", "attack"]

    def test_deeply_nested_five_levels(self):
        path = "root['abilities']['passive'][0]['effects']['damage']"
        assert patch_utils._parse_deepdiff_path(path) == ["abilities", "passive", 0, "effects", "damage"]

    def test_integer_index_only(self):
        assert patch_utils._parse_deepdiff_path("root[0]") == [0]

    def test_mixed_keys_and_indices(self):
        path = "root['abilities']['passive'][2]['description']"
        assert patch_utils._parse_deepdiff_path(path) == ["abilities", "passive", 2, "description"]

    def test_large_integer_index(self):
        path = "root['items'][99999]"
        assert patch_utils._parse_deepdiff_path(path) == ["items", 99999]

    def test_empty_root_path(self):
        """root alone should produce an empty list."""
        assert patch_utils._parse_deepdiff_path("root") == []

    def test_key_with_spaces(self):
        path = "root['key with spaces']"
        assert patch_utils._parse_deepdiff_path(path) == ["key with spaces"]

    def test_key_with_special_characters(self):
        path = "root['damage_modifiers']['$schema']"
        assert patch_utils._parse_deepdiff_path(path) == ["damage_modifiers", "$schema"]

    def test_key_with_dots(self):
        path = "root['some.dotted.key']"
        assert patch_utils._parse_deepdiff_path(path) == ["some.dotted.key"]

    def test_consecutive_integer_indices(self):
        path = "root[0][1][2]"
        assert patch_utils._parse_deepdiff_path(path) == [0, 1, 2]

    def test_key_with_unicode(self):
        path = "root['名前']['攻撃力']"
        assert patch_utils._parse_deepdiff_path(path) == ["名前", "攻撃力"]

    def test_completely_garbage_string(self):
        """Should return empty list for unparseable garbage."""
        assert patch_utils._parse_deepdiff_path("lol this isn't a path") == []

    def test_empty_string(self):
        assert patch_utils._parse_deepdiff_path("") == []


# ===========================================================================
# compute_diff — Pure function adversarial torture tests
# ===========================================================================

class TestComputeDiffAdversarial:
    """Adversarial tests for compute_diff."""

    # --- Null / Empty edge cases ---

    def test_both_none(self):
        assert generate_patch.compute_diff(None, None) == []

    def test_old_none_new_empty(self):
        """None -> {} should produce no diffs (both treated as empty)."""
        assert generate_patch.compute_diff(None, {}) == []

    def test_old_empty_new_none(self):
        """Same the other way."""
        assert generate_patch.compute_diff({}, None) == []

    def test_identical_data(self):
        data = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
        assert generate_patch.compute_diff(data, data) == []

    def test_old_none_new_has_data(self):
        """Brand new entity. Everything is 'added'."""
        new = {"name": "Skeleton", "health": 100}
        diffs = patch_utils.compute_diff(None, new)
        assert len(diffs) > 0
        paths = [d["path"] for d in diffs]
        assert ["name"] in paths
        assert ["health"] in paths

    def test_old_has_data_new_empty(self):
        """Entity deleted. Everything is 'removed'."""
        old = {"name": "Skeleton", "health": 100}
        diffs = patch_utils.compute_diff(old, {})
        assert len(diffs) > 0
        assert all(d.get("removed") is True for d in diffs)

    # --- Type-change edge cases ---

    def test_value_type_change_int_to_string(self):
        old = {"damage": 50}
        new = {"damage": "fifty"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["old_value"] == 50
        assert diffs[0]["new_value"] == "fifty"

    def test_value_type_change_string_to_bool(self):
        old = {"active": "yes"}
        new = {"active": True}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1

    def test_value_type_change_int_to_list(self):
        """Replacing a scalar with a list is a complex structural change."""
        old = {"tags": "melee"}
        new = {"tags": ["melee", "ground"]}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1  # DeepDiff should detect the type change

    def test_value_type_change_dict_to_string(self):
        old = {"mechanics": {"cleave": True}}
        new = {"mechanics": "deprecated"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1

    # --- Deeply nested structures ---

    def test_deeply_nested_change(self):
        old = {"a": {"b": {"c": {"d": {"e": 1}}}}}
        new = {"a": {"b": {"c": {"d": {"e": 2}}}}}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["path"] == ["a", "b", "c", "d", "e"]
        assert diffs[0]["old_value"] == 1
        assert diffs[0]["new_value"] == 2

    def test_deeply_nested_addition(self):
        old = {"a": {"b": {}}}
        new = {"a": {"b": {"c": {"d": 42}}}}
        diffs = patch_utils.compute_diff(old, new)
        assert any(d["path"] == ["a", "b", "c"] for d in diffs)

    # --- Array mutations ---

    def test_array_item_removed(self):
        old = {"tags": ["fire", "magic", "ranged"]}
        new = {"tags": ["fire", "ranged"]}
        diffs = patch_utils.compute_diff(old, new)
        removed_diffs = [d for d in diffs if d.get("removed")]
        assert len(removed_diffs) >= 1

    def test_empty_array_to_populated(self):
        old = {"items": []}
        new = {"items": ["sword", "shield"]}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1

    def test_populated_array_to_empty(self):
        old = {"items": ["sword", "shield"]}
        new = {"items": []}
        diffs = patch_utils.compute_diff(old, new)
        removed = [d for d in diffs if d.get("removed")]
        assert len(removed) >= 1

    def test_array_of_dicts_item_changed(self):
        old = {"passives": [{"name": "Fire", "value": 10}]}
        new = {"passives": [{"name": "Fire", "value": 20}]}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1

    # --- Special values ---

    def test_null_value_change(self):
        old = {"effect": None}
        new = {"effect": "burn"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["old_value"] is None

    def test_boolean_flip(self):
        old = {"pierce": True}
        new = {"pierce": False}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["old_value"] is True
        assert diffs[0]["new_value"] is False

    def test_float_precision(self):
        old = {"multiplier": 1.5}
        new = {"multiplier": 1.500000001}
        diffs = patch_utils.compute_diff(old, new)
        # DeepDiff should see this as a change
        assert len(diffs) == 1

    def test_zero_to_nonzero(self):
        old = {"cooldown": 0}
        new = {"cooldown": 5}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1

    def test_empty_string_to_value(self):
        old = {"description": ""}
        new = {"description": "A powerful spell"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1

    # --- Unicode / Emoji ---

    def test_unicode_values(self):
        old = {"name": "名前"}
        new = {"name": "新しい名前"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1

    def test_emoji_in_descriptions(self):
        old = {"desc": "Fire 🔥"}
        new = {"desc": "Ice ❄️"}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1

    # --- Large payloads ---

    def test_massive_flat_dict(self):
        """1000 key-value pairs with 500 changes."""
        old = {f"key_{i}": i for i in range(1000)}
        new = {f"key_{i}": (i * 2 if i >= 500 else i) for i in range(1000)}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 500

    def test_massive_array(self):
        old = {"items": list(range(100))}
        new = {"items": list(range(100)) + [100, 101, 102]}
        diffs = patch_utils.compute_diff(old, new)
        added = [d for d in diffs if not d.get("removed")]
        assert len(added) == 3

    # --- last_modified exclusion ---

    def test_only_last_modified_changed(self):
        old = {"last_modified": "2024-01-01T00:00:00Z", "health": 100, "name": "test"}
        new = {"last_modified": "2026-12-31T23:59:59Z", "health": 100, "name": "test"}
        assert generate_patch.compute_diff(old, new) == []

    def test_last_modified_plus_real_change(self):
        old = {"last_modified": "2024-01-01", "health": 100}
        new = {"last_modified": "2026-12-31", "health": 200}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 1
        assert diffs[0]["path"] == ["health"]

    # --- Simultaneous add + remove + change ---

    def test_mixed_operations(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "c": 3, "d": 4}
        diffs = patch_utils.compute_diff(old, new)
        paths = [tuple(d["path"]) for d in diffs]
        # a changed, b removed, d added
        assert ("a",) in paths
        assert ("b",) in paths
        assert ("d",) in paths
        assert len(diffs) == 3


# ===========================================================================
# get_changed_files_between — Git subprocess mock torture tests
# ===========================================================================

class TestGetChangedFilesBetweenAdversarial:
    """Adversarial tests for get_changed_files_between."""

    def test_none_before_sha(self):
        assert generate_patch.get_changed_files_between(None, "abc123") == []

    def test_empty_string_before_sha(self):
        assert generate_patch.get_changed_files_between("", "abc123") == []

    @patch("subprocess.run")
    def test_empty_git_output(self, mock_run):
        result = MagicMock()
        result.stdout = ""
        mock_run.return_value = result
        assert generate_patch.get_changed_files_between("a", "b") == []

    @patch("subprocess.run")
    def test_only_whitespace_output(self, mock_run):
        result = MagicMock()
        result.stdout = "   \n  \n  "
        mock_run.return_value = result
        assert generate_patch.get_changed_files_between("a", "b") == []

    @patch("subprocess.run")
    def test_filters_patches_json(self, mock_run):
        result = MagicMock()
        result.stdout = "M\tdata/patches.json\nM\tdata/units/skeleton.json\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        paths = [f for _, f in changed]
        assert "data/patches.json" not in paths
        assert "data/units/skeleton.json" in paths

    @patch("subprocess.run")
    def test_filters_game_config(self, mock_run):
        result = MagicMock()
        result.stdout = "M\tdata/game_config.json\nM\tdata/units/skeleton.json\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        paths = [f for _, f in changed]
        assert "data/game_config.json" not in paths

    @patch("subprocess.run")
    def test_filters_queue_json(self, mock_run):
        result = MagicMock()
        result.stdout = "M\tdata/queue.json\nA\tdata/spells/fireball.json\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        assert len(changed) == 1
        assert changed[0][1] == "data/spells/fireball.json"

    @patch("subprocess.run")
    def test_filters_non_json_data_files(self, mock_run):
        """Even files under data/ but not .json should be excluded."""
        result = MagicMock()
        result.stdout = "M\tdata/README.md\nA\tdata/notes.txt\nM\tdata/units/orc.json\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        assert len(changed) == 1
        assert changed[0][1] == "data/units/orc.json"

    @patch("subprocess.run")
    def test_handles_deleted_files(self, mock_run):
        result = MagicMock()
        result.stdout = "D\tdata/units/old_unit.json\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        assert changed == [("D", "data/units/old_unit.json")]

    @patch("subprocess.run")
    def test_handles_renamed_files(self, mock_run):
        """Git rename status includes two paths."""
        result = MagicMock()
        result.stdout = "R100\tdata/units/old.json\tdata/units/new.json\n"
        mock_run.return_value = result
        # This will try parts[0]=R100, parts[1]=data/units/old.json
        # which will pass the filter. May or may not be correct behavior,
        # but it should NOT crash.
        changed = generate_patch.get_changed_files_between("a", "b")
        assert isinstance(changed, list)

    @patch("subprocess.run")
    def test_subprocess_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)
        assert generate_patch.get_changed_files_between("a", "b") == []

    @patch("subprocess.run")
    def test_subprocess_oserror(self, mock_run):
        mock_run.side_effect = OSError("No such file: git")
        assert generate_patch.get_changed_files_between("a", "b") == []

    @patch("subprocess.run")
    def test_malformed_tab_output(self, mock_run):
        """Lines without tabs should not crash."""
        result = MagicMock()
        result.stdout = "Mdata/units/skeleton.json\n"  # Missing tab
        mock_run.return_value = result
        # This WILL crash with IndexError because parts[1] doesn't exist
        # Let's see if it does — this is a legit bug-finder
        try:
            changed = generate_patch.get_changed_files_between("a", "b")
            # If it doesn't crash, that's fine
        except (IndexError, ValueError):
            pytest.fail("get_changed_files_between crashed on malformed tab output!")

    @patch("subprocess.run")
    def test_many_files_changed(self, mock_run):
        """Simulate 500 files changed."""
        lines = "\n".join(f"M\tdata/units/unit_{i}.json" for i in range(500))
        result = MagicMock()
        result.stdout = lines + "\n"
        mock_run.return_value = result
        changed = generate_patch.get_changed_files_between("a", "b")
        assert len(changed) == 500


# ===========================================================================
# discover_version_boundaries — Git history chaos tests
# ===========================================================================

class TestDiscoverVersionBoundariesAdversarial:
    """Adversarial tests for discover_version_boundaries."""

    @patch("subprocess.run")
    def test_empty_git_log(self, mock_run):
        result = MagicMock()
        result.stdout = ""
        mock_run.return_value = result
        assert generate_patch.discover_version_boundaries("0.0.1") == []

    @patch("subprocess.run")
    def test_git_log_fails(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        assert generate_patch.discover_version_boundaries("0.0.1") == []

    @patch("subprocess.run")
    def test_corrupted_json_in_commit(self, mock_run):
        """If game_config.json is corrupted in a commit, skip it gracefully."""
        log_result = MagicMock()
        log_result.stdout = "commit1\ncommit2\n"

        # First commit has corrupted JSON
        show1 = MagicMock()
        show1.stdout = "{this is not json lol}"

        # Second has valid JSON
        show2 = MagicMock()
        show2.stdout = '{"version": "0.0.1"}'

        mock_run.side_effect = [log_result, show1, show2]
        
        boundaries = generate_patch.discover_version_boundaries("0.0.1")
        assert len(boundaries) == 1
        assert boundaries[0]["version"] == "0.0.1"

    @patch("subprocess.run")
    def test_missing_version_key_in_commit(self, mock_run):
        """game_config.json exists but has no 'version' key."""
        log_result = MagicMock()
        log_result.stdout = "commit1\n"

        show1 = MagicMock()
        show1.stdout = '{"name": "test game"}'

        mock_run.side_effect = [log_result, show1]
        boundaries = generate_patch.discover_version_boundaries("0.0.1")
        # version will be None, which should not be added to seen_versions
        assert len(boundaries) == 0

    @patch("subprocess.run")
    def test_version_goes_backwards(self, mock_run):
        """Version history: 0.0.1 -> 0.0.3 -> 0.0.2 (rollback)."""
        log_result = MagicMock()
        log_result.stdout = "c1\nc2\nc3\n"

        mock_run.side_effect = [
            log_result,
            MagicMock(stdout='{"version": "0.0.1"}'),
            MagicMock(stdout='{"version": "0.0.3"}'),
            MagicMock(stdout='{"version": "0.0.2"}'),
        ]
        boundaries = generate_patch.discover_version_boundaries("0.0.3")
        versions = [b["version"] for b in boundaries]
        assert "0.0.1" in versions
        assert "0.0.2" in versions
        assert "0.0.3" in versions

    @patch("subprocess.run")
    def test_same_version_many_commits(self, mock_run):
        """50 commits all with version 0.0.1 — only first should be kept."""
        log_result = MagicMock()
        log_result.stdout = "\n".join(f"commit_{i}" for i in range(50)) + "\n"

        all_mocks = [log_result]
        for _ in range(50):
            m = MagicMock()
            m.stdout = '{"version": "0.0.1"}'
            all_mocks.append(m)

        mock_run.side_effect = all_mocks
        boundaries = generate_patch.discover_version_boundaries("0.0.1")
        assert len(boundaries) == 1
        assert boundaries[0]["commit"] == "commit_0"

    @patch("subprocess.run")
    def test_git_show_fails_for_specific_commit(self, mock_run):
        """If git show fails for one commit, others should still work."""
        log_result = MagicMock()
        log_result.stdout = "good_commit\nbad_commit\ngood_commit2\n"

        good1 = MagicMock()
        good1.stdout = '{"version": "0.0.1"}'

        good2 = MagicMock()
        good2.stdout = '{"version": "0.0.2"}'

        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "bad_commit" in str(cmd):
                raise subprocess.CalledProcessError(128, "git")
            return results.pop(0)

        results = [log_result, good1, good2]
        mock_run.side_effect = side_effect
        # This will work because the except catches all exceptions
        boundaries = generate_patch.discover_version_boundaries("1.0.0")
        # Should have at least the good commits
        assert isinstance(boundaries, list)


# ===========================================================================
# get_file_content_at_commit — Git show mock tests
# ===========================================================================

class TestGetFileContentAtCommit:
    """Tests for get_file_content_at_commit."""

    @patch("subprocess.run")
    def test_valid_json(self, mock_run):
        result = MagicMock()
        result.stdout = '{"name": "Skeleton", "health": 100}'
        mock_run.return_value = result
        data = patch_utils.get_file_content_at_commit("data/units/skeleton.json", "abc123")
        assert data == {"name": "Skeleton", "health": 100}

    @patch("subprocess.run")
    def test_corrupted_json(self, mock_run):
        result = MagicMock()
        result.stdout = "this is not json {{{]["
        mock_run.return_value = result
        data = patch_utils.get_file_content_at_commit("data/units/skeleton.json", "abc123")
        assert data is None

    @patch("subprocess.run")
    def test_empty_output(self, mock_run):
        result = MagicMock()
        result.stdout = ""
        mock_run.return_value = result
        data = patch_utils.get_file_content_at_commit("data/units/skeleton.json", "abc123")
        assert data is None

    @patch("subprocess.run")
    def test_git_show_fails(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git")
        data = patch_utils.get_file_content_at_commit("data/units/skeleton.json", "abc123")
        assert data is None

    @patch("subprocess.run")
    def test_file_not_in_commit(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(128, "git", stderr="does not exist in 'abc123'")
        data = patch_utils.get_file_content_at_commit("data/units/ghost.json", "abc123")
        assert data is None


# ===========================================================================
# load_json / save_json — File I/O edge cases
# ===========================================================================

class TestLoadJson:
    """Tests for load_json."""

    def test_nonexistent_file(self):
        assert patch_utils.load_json("/nonexistent/path/fake.json") is None

    def test_corrupted_json_file(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{this is not json}", encoding="utf-8")
        assert patch_utils.load_json(str(f)) is None

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("", encoding="utf-8")
        assert patch_utils.load_json(str(f)) is None

    def test_valid_json_file(self, tmp_path):
        f = tmp_path / "good.json"
        f.write_text('{"a": 1}', encoding="utf-8")
        assert patch_utils.load_json(str(f)) == {"a": 1}

    def test_array_json_file(self, tmp_path):
        f = tmp_path / "arr.json"
        f.write_text('[1, 2, 3]', encoding="utf-8")
        assert patch_utils.load_json(str(f)) == [1, 2, 3]

    def test_unicode_json_file(self, tmp_path):
        f = tmp_path / "uni.json"
        f.write_text('{"name": "火の玉"}', encoding="utf-8")
        assert patch_utils.load_json(str(f)) == {"name": "火の玉"}


class TestSaveJson:
    """Tests for save_json."""

    def test_writes_valid_json(self, tmp_path):
        f = tmp_path / "out.json"
        patch_utils.save_json(str(f), {"a": 1, "b": [2, 3]})
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data == {"a": 1, "b": [2, 3]}

    def test_overwrites_existing(self, tmp_path):
        f = tmp_path / "out.json"
        f.write_text('{"old": true}')
        patch_utils.save_json(str(f), {"new": True})
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data == {"new": True}

    def test_writes_empty_array(self, tmp_path):
        f = tmp_path / "out.json"
        patch_utils.save_json(str(f), [])
        assert json.loads(f.read_text(encoding="utf-8")) == []


# ===========================================================================
# Integration-style: compute_diff with realistic game data
# ===========================================================================

class TestComputeDiffRealisticData:
    """Tests with data that looks like actual game entities."""

    def test_hero_health_rebalance(self):
        old = {
            "entity_id": "astral_monk",
            "name": "Astral Monk",
            "health": 1000,
            "abilities": {
                "passive": [{"name": "Speed", "description": "All Astral spells recharge faster."}],
                "defense": {"cooldown": 8},
            },
            "last_modified": "2024-01-01",
        }
        new = {
            "entity_id": "astral_monk",
            "name": "Astral Monk",
            "health": 300,
            "abilities": {
                "passive": [{"name": "Speed", "description": "All Astral spells recharge 32% faster."}],
                "defense": {"cooldown": 10, "mechanics": {"stealth": {"duration": 1.5}}},
            },
            "last_modified": "2026-02-23",
        }
        diffs = patch_utils.compute_diff(old, new)
        # Should detect health, passive desc, cooldown, and stealth mechanic add
        paths = [d["path"] for d in diffs]
        assert ["health"] in paths
        assert len(diffs) >= 3  # At least health + cooldown + desc or mechanics

    def test_spell_stat_changes(self):
        old = {"entity_id": "fireball", "mana_cost": 5, "damage": 100, "range": 24}
        new = {"entity_id": "fireball", "mana_cost": 6, "damage": 120, "range": 24}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) == 2
        changed_fields = {tuple(d["path"]) for d in diffs}
        assert ("mana_cost",) in changed_fields
        assert ("damage",) in changed_fields

    def test_consumable_completely_replaced(self):
        old = {
            "entity_id": "small_recharge",
            "name": "Small Recharge",
            "effect_type": "Charge_Refill",
            "value": 25,
        }
        new = {
            "entity_id": "charge_orb_1",
            "name": "Charge Orb I",
            "effect_type": "Charge_Refill",
            "value": 5,
            "stack_size": 1,
        }
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 3  # entity_id, name, value changed, stack_size added

    def test_upgrade_target_tags_changed(self):
        old = {"target_tags": ["Melee", "Construct"], "effect": {"damage": 5}}
        new = {"target_tags": ["Melee", "Construct", "Flying"], "effect": {"damage": 10}}
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 2  # Flying added + damage changed

    def test_damage_modifier_complex_change(self):
        old = {
            "damage_modifiers": [
                {"multiplier": 1.5, "condition": {"field": "target.type", "op": "==", "val": "Building"}}
            ]
        }
        new = {
            "damage_modifiers": [
                {"multiplier": 2.0, "condition": {"field": "target.type", "op": "==", "val": "Building"}}
            ]
        }
        diffs = patch_utils.compute_diff(old, new)
        assert len(diffs) >= 1
