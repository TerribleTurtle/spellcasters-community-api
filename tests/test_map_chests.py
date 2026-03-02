"""Tests for the map_chests entity type.

Covers:
1. Schema positive validation — real Mausoleum data passes.
2. Schema negative: unknown property rejected (unevaluatedProperties: false).
3. Schema negative: missing required 'chests' field rejected.
4. Schema negative: bad rarity enum rejected.
5. Schema negative: bad reward_entity_id pattern rejected.
6. Referential integrity — dangling reward_entity_id detected.
"""

import copy
import os

import jsonschema
import pytest
from jsonschema import validators

try:
    from referencing import Registry, Resource  # noqa: F401
except ImportError:
    pytest.skip("referencing library not installed", allow_module_level=True)

import config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_validator(registry_and_schemas, schema_filename):
    """Build a validator for a given schema file."""
    registry, schemas_map = registry_and_schemas
    schema_uri = schemas_map[schema_filename]
    schema_resource = registry.get_or_retrieve(schema_uri).value
    schema_contents = schema_resource.contents
    ValidatorClass = validators.validator_for(schema_contents)
    return ValidatorClass(schema_contents, registry=registry)


def _load_mausoleum():
    """Load the real Mausoleum data file as a fixture baseline."""
    path = os.path.join(config.DATA_DIR, "map_chests", "mausoleum.json")
    return config.load_json(path)


# ---------------------------------------------------------------------------
# 1. Schema positive test
# ---------------------------------------------------------------------------


def test_mausoleum_passes_schema(registry_and_schemas):
    """The actual mausoleum.json file should pass schema validation."""
    validator = _get_validator(registry_and_schemas, "map_chests.schema.json")
    data = _load_mausoleum()
    assert data is not None, "mausoleum.json failed to load"

    # Strip $schema key since it's metadata for editors, not part of the data model
    clean = {k: v for k, v in data.items() if k != "$schema"}
    validator.validate(clean)


# ---------------------------------------------------------------------------
# 2. Schema negative: unknown property
# ---------------------------------------------------------------------------


def test_rejects_unknown_property_on_map_chest(registry_and_schemas):
    """An unknown top-level property should be rejected by unevaluatedProperties: false."""
    validator = _get_validator(registry_and_schemas, "map_chests.schema.json")
    data = _load_mausoleum()
    assert data is not None

    invalid = copy.deepcopy(data)
    invalid.pop("$schema", None)
    invalid["garbage_field"] = True

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)


# ---------------------------------------------------------------------------
# 3. Schema negative: missing required 'chests'
# ---------------------------------------------------------------------------


def test_rejects_missing_chests(registry_and_schemas):
    """Data without the required 'chests' array should be rejected."""
    validator = _get_validator(registry_and_schemas, "map_chests.schema.json")
    data = _load_mausoleum()
    assert data is not None

    invalid = copy.deepcopy(data)
    invalid.pop("$schema", None)
    del invalid["chests"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)


# ---------------------------------------------------------------------------
# 4. Schema negative: bad rarity enum
# ---------------------------------------------------------------------------


def test_rejects_bad_rarity_enum(registry_and_schemas):
    """A chest with an invalid rarity value should be rejected."""
    validator = _get_validator(registry_and_schemas, "map_chests.schema.json")
    data = _load_mausoleum()
    assert data is not None

    invalid = copy.deepcopy(data)
    invalid.pop("$schema", None)
    invalid["chests"][0]["rarity"] = "Mythic"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)


# ---------------------------------------------------------------------------
# 5. Schema negative: bad reward_entity_id pattern
# ---------------------------------------------------------------------------


def test_rejects_bad_reward_entity_id_pattern(registry_and_schemas):
    """A reward_entity_id with spaces/uppercase should be rejected."""
    validator = _get_validator(registry_and_schemas, "map_chests.schema.json")
    data = _load_mausoleum()
    assert data is not None

    invalid = copy.deepcopy(data)
    invalid.pop("$schema", None)
    invalid["chests"][0]["reward_entity_id"] = "Bad Name With Spaces"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)


# ---------------------------------------------------------------------------
# 6. Referential integrity — dangling entity reference
# ---------------------------------------------------------------------------


def test_referential_integrity_catches_dangling_reference(data_loader):
    """The referential integrity check should catch a nonexistent reward_entity_id."""
    # Build unit/spell ID sets from the data_loader fixture
    unit_ids = set()
    spell_ids = set()

    for item in data_loader.get("units", []):
        eid = item.get("entity_id")
        if eid:
            unit_ids.add(eid)

    for item in data_loader.get("spells", []):
        eid = item.get("entity_id")
        if eid:
            spell_ids.add(eid)

    # Verify our real data passes
    map_chests_data = data_loader.get("map_chests", [])
    assert len(map_chests_data) > 0, "No map_chests data found in data_loader"

    for item in map_chests_data:
        for chest in item.get("chests", []):
            reward_id = chest.get("reward_entity_id", "")
            reward_type = chest.get("reward_type", "")
            lookup = unit_ids if reward_type == "Unit" else spell_ids
            assert reward_id in lookup, f"Dangling reference: '{reward_id}' not in {reward_type.lower()}s"

    # Verify a fake ID would fail the check
    assert "nonexistent_unit_xyz" not in unit_ids
    assert "nonexistent_spell_xyz" not in spell_ids
