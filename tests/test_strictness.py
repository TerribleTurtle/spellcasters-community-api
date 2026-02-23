"""
Schema Strictness Tests

Verifies that JSON schemas correctly reject invalid data payloads
(e.g., property shadowing, empty strings, bad ID formats).
Pytest port of scripts/verify_strictness.py.
"""

import copy

import pytest
from jsonschema import ValidationError, validators
from validate_integrity import SCHEMAS_DIR, create_registry


@pytest.fixture(scope="session")
def hero_validator():
    """Builds a validator for the hero schema using the full registry."""
    registry, schemas_map = create_registry(SCHEMAS_DIR)

    schema_filename = "heroes.schema.json"
    assert schema_filename in schemas_map, f"{schema_filename} not found in registry"

    hero_uri = schemas_map[schema_filename]
    resolver = registry.resolver()
    resolved = resolver.lookup(hero_uri)
    schema = resolved.contents

    ValidatorClass = validators.validator_for(schema)
    return ValidatorClass(schema, registry=registry)


@pytest.fixture
def valid_hero():
    """A minimal valid hero payload for testing."""
    return {
        "entity_id": "test_hero",
        "name": "Test Hero",
        "category": "Spellcaster",
        "class": "Conqueror",
        "difficulty": 1,
        "health": 100,
        "movement_type": "Ground",
        "population": 0,
        "image_required": False,
        "description": "A test hero.",
        "tags": ["test"],
        "abilities": {
            "passive": [],
            "primary": {"name": "Hit", "description": "Hits stuff", "damage": 10},
            "defense": {"name": "Block", "description": "Blocks stuff"},
            "ultimate": {"name": "Win", "description": "Wins game"},
        },
        "last_modified": "2026-01-01T00:00:00Z",
    }


def test_valid_hero_baseline(hero_validator, valid_hero):
    """A valid hero payload should pass schema validation."""
    hero_validator.validate(valid_hero)  # Should not raise


def test_rejects_unknown_property(hero_validator, valid_hero):
    """An unknown property on abilities.primary should be rejected by unevaluatedProperties: false."""
    invalid = copy.deepcopy(valid_hero)
    invalid["abilities"]["primary"]["garbage_stat"] = 999

    with pytest.raises(ValidationError):
        hero_validator.validate(invalid)


def test_rejects_empty_name(hero_validator, valid_hero):
    """An empty string for 'name' should be rejected by minLength: 1."""
    invalid = copy.deepcopy(valid_hero)
    invalid["name"] = ""

    with pytest.raises(ValidationError):
        hero_validator.validate(invalid)


def test_rejects_bad_entity_id(hero_validator, valid_hero):
    """A non-snake_case entity_id should be rejected by pattern validation."""
    invalid = copy.deepcopy(valid_hero)
    invalid["entity_id"] = "Bad ID with Spaces"

    with pytest.raises(ValidationError):
        hero_validator.validate(invalid)
