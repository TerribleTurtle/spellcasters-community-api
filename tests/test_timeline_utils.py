import os

import pytest
from timeline_utils import build_entity_stat_changes, compute_stat_diff, extract_field, load_timeline, resolve_entity_id


def test_resolve_entity_id():
    assert resolve_entity_id({"entity_id": "astral_monk"}) == "astral_monk"
    assert resolve_entity_id({"upgrade_id": "dev_placeholder"}) == "dev_placeholder"
    assert resolve_entity_id({"name": "No ID"}) is None
    assert resolve_entity_id(None) is None


def test_extract_field():
    snapshot = {"health": 100, "abilities": {"primary": {"damage": 50}, "passive": []}}
    assert extract_field(snapshot, "health") == 100
    assert extract_field(snapshot, "abilities.primary.damage") == 50
    assert extract_field(snapshot, "abilities.missing") is None
    assert extract_field(snapshot, "missing") is None


def test_compute_stat_diff():
    old = {"snapshot": {"health": 100, "speed": 5, "nested": {"val": 10}}}
    new = {"snapshot": {"health": 120, "speed": 5, "nested": {"val": 15}}}

    fields = ["health", "speed", "nested.val", "missing"]
    diffs = compute_stat_diff(old, new, fields)

    assert len(diffs) == 2

    # Health changed
    health_diff = next(d for d in diffs if d["field"] == "health")
    assert health_diff["old"] == 100
    assert health_diff["new"] == 120

    # Nested val changed
    nested_diff = next(d for d in diffs if d["field"] == "nested.val")
    assert nested_diff["old"] == 10
    assert nested_diff["new"] == 15


def test_compute_stat_diff_missing_handling():
    # Shows that addition/removal of a field tracks correctly
    old = {"snapshot": {"health": 100}}
    new = {"snapshot": {"health": 100, "new_stat": 50}}

    diffs = compute_stat_diff(old, new, ["health", "new_stat"])
    assert len(diffs) == 1
    assert diffs[0]["field"] == "new_stat"
    assert diffs[0]["old"] is None
    assert diffs[0]["new"] == 50


# --- Fixture-based tests using a safe tmpdir ---


@pytest.fixture
def mock_timeline_dir(tmpdir):
    # Single version (No diffs possible)
    single = [{"version": "0.0.1", "snapshot": {"health": 10}}]

    # Multi version (Diffs trackable)
    multi = [
        {"version": "0.0.1", "date": "2026-02-01", "snapshot": {"health": 100, "dps": 20}},
        {"version": "0.0.2", "date": "2026-02-02", "snapshot": {"health": 120, "dps": 20}},
        {"version": "0.0.3", "date": "2026-02-03", "snapshot": {"health": 120, "dps": 25}},
    ]

    import json

    with open(os.path.join(tmpdir, "single.json"), "w") as f:
        json.dump(single, f)
    with open(os.path.join(tmpdir, "multi.json"), "w") as f:
        json.dump(multi, f)

    return str(tmpdir)


def test_load_timeline(mock_timeline_dir):
    data = load_timeline("multi", mock_timeline_dir)
    assert len(data) == 3
    assert data[0]["version"] == "0.0.1"

    # Missing file -> empty list
    assert load_timeline("missing", mock_timeline_dir) == []


def test_build_entity_stat_changes(mock_timeline_dir):
    fields = ["health", "dps", "range"]

    # Single version -> []
    assert build_entity_stat_changes("single", mock_timeline_dir, fields) == []

    # Multi version -> diffs per version
    changes = build_entity_stat_changes("multi", mock_timeline_dir, fields)
    assert len(changes) == 2

    # Version 0.0.2 only health changed
    assert changes[0]["version"] == "0.0.2"
    assert len(changes[0]["changes"]) == 1
    assert changes[0]["changes"][0] == {"field": "health", "old": 100, "new": 120}

    # Version 0.0.3 only dps changed
    assert changes[1]["version"] == "0.0.3"
    assert len(changes[1]["changes"]) == 1
    assert changes[1]["changes"][0] == {"field": "dps", "old": 20, "new": 25}
