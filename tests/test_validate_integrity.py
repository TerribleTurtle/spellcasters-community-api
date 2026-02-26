"""
Unit tests for validate_integrity.py

Tests the core validation utility functions: registry creation,
asset existence checks, and entry asset validation.
"""

import json
import os
from unittest.mock import patch

import config
import pytest
from validate_integrity import check_asset_exists, create_registry, validate_entry_assets

# ---------------------------------------------------------------------------
# create_registry — uses real filesystem schemas
# ---------------------------------------------------------------------------


class TestCreateRegistry:
    """Tests for the schema registry builder."""

    def test_returns_populated_registry(self):
        """Should load all schemas from the V2 directory."""
        registry, schemas_map = create_registry(config.SCHEMAS_DIR)
        assert len(schemas_map) > 0, "No schemas were loaded"

    def test_known_schema_in_map(self):
        """Should include known schema files in the map."""
        _, schemas_map = create_registry(config.SCHEMAS_DIR)
        assert "units.schema.json" in schemas_map
        assert "heroes.schema.json" in schemas_map
        assert "spells.schema.json" in schemas_map

    def test_schemas_map_has_relative_keys(self):
        """Should include both filename and relative-path keys."""
        _, schemas_map = create_registry(config.SCHEMAS_DIR)
        # Check that at least one relative-path key (with /) exists
        relative_keys = [k for k in schemas_map if "/" in k]
        assert len(relative_keys) > 0, "No relative-path keys found in schemas_map"


# ---------------------------------------------------------------------------
# check_asset_exists — requires filesystem mocking
# ---------------------------------------------------------------------------


class TestCheckAssetExists:
    """Tests for the asset existence and hygiene checker."""

    def test_returns_zero_for_existing_valid_asset(self, tmp_path):
        """A valid-sized .webp file should pass with 0 warnings."""
        category_dir = tmp_path / "units"
        category_dir.mkdir()
        asset = category_dir / "skeleton.webp"
        # Create a minimal valid image-like file (1x1 pixel)
        _create_tiny_image(asset)

        cache = {}
        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "skeleton", True, cache)
        assert result == 0

    def test_returns_one_for_missing_required_asset(self, tmp_path):
        """A missing required asset should return 1 warning."""
        cache = {}
        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "nonexistent", True, cache)
        assert result == 1

    def test_returns_zero_for_missing_optional_asset(self, tmp_path):
        """A missing optional asset (is_required=False) should return 0."""
        cache = {}
        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "nonexistent", False, cache)
        assert result == 0

    def test_cache_hit_skips_validation(self, tmp_path):
        """A cached entry with matching mtime+size should skip validation."""
        category_dir = tmp_path / "units"
        category_dir.mkdir()
        asset = category_dir / "skeleton.webp"
        _create_tiny_image(asset)

        stat = os.stat(asset)
        cache = {str(asset): {"mtime": stat.st_mtime, "size": stat.st_size}}

        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "skeleton", True, cache)
        assert result == 0

    def test_oversized_image_warns(self, tmp_path):
        """An image exceeding MAX_IMG_SIZE_KB should produce a warning."""
        category_dir = tmp_path / "units"
        category_dir.mkdir()
        asset = category_dir / "big_unit.webp"
        _create_tiny_image(asset)

        cache = {}
        # Set a very low limit so the tiny image triggers the warning
        with (
            patch("validate_integrity.ASSETS_DIR", str(tmp_path)),
            patch("validate_integrity.MAX_IMG_SIZE_KB", 0),
        ):
            result = check_asset_exists("units", "big_unit", True, cache)
        assert result >= 1


# ---------------------------------------------------------------------------
# validate_entry_assets — higher-level function
# ---------------------------------------------------------------------------


class TestValidateEntryAssets:
    """Tests for entry-level asset validation."""

    def test_skips_when_image_not_required(self):
        """Should return 0 immediately when image_required is False."""
        data = {"entity_id": "test_unit", "image_required": False}
        result = validate_entry_assets(data, "unit", "units", {})
        assert result == 0

    def test_delegates_to_check_asset_exists(self):
        """Should call check_asset_exists for entities with image_required: True."""
        data = {"entity_id": "test_unit", "image_required": True}
        with patch("validate_integrity.check_asset_exists", return_value=0) as mock_check:
            result = validate_entry_assets(data, "unit", "units", {})
            mock_check.assert_called_once_with("units", "test_unit", True, {})
            assert result == 0


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _create_tiny_image(path):
    """Creates a minimal 1x1 WebP image at the given path."""
    from PIL import Image

    img = Image.new("RGB", (1, 1), color="red")
    img.save(str(path), format="WEBP")


# ---------------------------------------------------------------------------
# cache loading & saving
# ---------------------------------------------------------------------------


class TestCacheOps:
    def test_load_save_cache_roundtrip(self, tmp_path):
        cache_file = tmp_path / ".asset_cache.json"

        # Test missing cache file
        with patch("validate_integrity.CACHE_FILE", str(cache_file)):
            from validate_integrity import load_cache, save_cache

            assert load_cache() == {}

            # Save and load
            data = {"/path/to/img": {"mtime": 123, "size": 456}}
            save_cache(data)

            assert load_cache() == data


# ---------------------------------------------------------------------------
# "Evil" Asset tests
# ---------------------------------------------------------------------------


class TestEvilAssets:
    def test_evil_corrupted_image(self, tmp_path):
        """Should catch PIL UnidentifiedImageError safely and return warning."""
        category_dir = tmp_path / "units"
        category_dir.mkdir()
        asset = category_dir / "bad.webp"

        # Create a text file posing as an image
        asset.write_text("This is not a webp image", encoding="utf-8")

        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "bad", True, {})
            # Should have handled it cleanly and returned 1 warning
            assert result == 1


# ---------------------------------------------------------------------------
# validate_timeline_metadata
# ---------------------------------------------------------------------------


class TestValidateTimelineMetadata:
    def test_skips_missing_dir(self, tmp_path):
        from validate_integrity import validate_timeline_metadata

        with patch("config.OUTPUT_DIR", str(tmp_path)):
            # "timeline" dir does not exist in tmp_path
            assert validate_timeline_metadata(None, None) == 0


# ---------------------------------------------------------------------------
# main validate_integrity loop
# ---------------------------------------------------------------------------


class TestMainLoop:
    def test_validate_integrity_runs_clean_on_real_data(self):
        """Full integration: run validate_integrity against actual project data.

        This exercises: data loading, schema registry, tag indexing,
        per-folder validation loop, asset checks, upgrade tag checks,
        game_config validation, patch history validation, timeline validation,
        and cache save.
        """
        from validate_integrity import validate_integrity

        # The project data should be valid. validate_integrity calls sys.exit(1)
        # only if errors > 0. If data is clean, it returns normally.
        # If it calls sys.exit(1), it means there's actually bad data — which is
        # a real bug the test should surface.
        validate_integrity()

    def test_validate_integrity_catches_schema_error(self, tmp_path):
        """Should count errors when data doesn't match schema."""
        from validate_integrity import validate_integrity

        data_dir = tmp_path / "data"
        schemas_dir = tmp_path / "schemas" / "v2"
        assets_dir = tmp_path / "assets"
        output_dir = tmp_path / "api" / "v2"

        # Create minimal structure
        for d in [data_dir, schemas_dir, assets_dir, output_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Create a units schema
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "units",
            "type": "object",
            "required": ["entity_id", "name"],
            "properties": {
                "entity_id": {"type": "string"},
                "name": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "image_required": {"type": "boolean"},
            },
        }
        (schemas_dir / "units.schema.json").write_text(json.dumps(schema), encoding="utf-8")

        # Create a unit data file that FAILS validation (missing required "name")
        units_dir = data_dir / "units"
        units_dir.mkdir()
        (units_dir / "bad_unit.json").write_text(
            json.dumps({"entity_id": "bad_unit", "image_required": False, "tags": ["test"]}), encoding="utf-8"
        )

        with (
            patch("validate_integrity.SCHEMAS_DIR", str(schemas_dir)),
            patch("validate_integrity.DATA_DIR", str(data_dir)),
            patch("validate_integrity.ASSETS_DIR", str(assets_dir)),
            patch("config.OUTPUT_DIR", str(output_dir)),
            patch("validate_integrity.CACHE_FILE", str(tmp_path / ".cache.json")),
        ):
            with pytest.raises(SystemExit) as exc_info:
                validate_integrity()
            assert exc_info.value.code == 1

    def test_upgrade_tag_warning(self, tmp_path):
        """Should warn when an upgrade targets a tag no unit has."""
        from validate_integrity import validate_integrity

        data_dir = tmp_path / "data"
        schemas_dir = tmp_path / "schemas" / "v2"
        assets_dir = tmp_path / "assets"
        output_dir = tmp_path / "api" / "v2"

        for d in [data_dir, schemas_dir, assets_dir, output_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Minimal upgrade schema that accepts anything
        upgrade_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "upgrades",
            "type": "object",
        }
        (schemas_dir / "upgrades.schema.json").write_text(json.dumps(upgrade_schema), encoding="utf-8")

        # Create upgrade data referencing nonexistent tag
        upgrades_dir = data_dir / "upgrades"
        upgrades_dir.mkdir()
        (upgrades_dir / "evil_upgrade.json").write_text(
            json.dumps({"entity_id": "evil_upgrade", "target_tags": ["nonexistent_tag"], "image_required": False}),
            encoding="utf-8",
        )

        with (
            patch("validate_integrity.SCHEMAS_DIR", str(schemas_dir)),
            patch("validate_integrity.DATA_DIR", str(data_dir)),
            patch("validate_integrity.ASSETS_DIR", str(assets_dir)),
            patch("config.OUTPUT_DIR", str(output_dir)),
            patch("validate_integrity.CACHE_FILE", str(tmp_path / ".cache.json")),
            patch("validate_integrity.FOLDER_TO_SCHEMA", {"upgrades": "upgrade"}),
            patch("validate_integrity.SCHEMA_FILES", {"upgrade": "upgrades.schema.json"}),
        ):
            # No errors (schemas pass) but there will be warnings for the orphan tag
            validate_integrity()


class TestTimelineMetadataIntegration:
    def test_validates_real_timeline(self):
        """Run validate_timeline_metadata against real project schemas if timeline exists."""
        from validate_integrity import create_registry, validate_timeline_metadata

        registry, schemas_map = create_registry(config.SCHEMAS_DIR)
        result = validate_timeline_metadata(registry, schemas_map)
        assert isinstance(result, int)

    def test_catches_invalid_timeline(self, tmp_path):
        """Should count errors when timeline data doesn't match schema."""
        from validate_integrity import create_registry, validate_timeline_metadata

        schemas_dir = tmp_path / "schemas"
        schemas_dir.mkdir()

        timeline_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "timeline_entry",
            "type": "object",
            "required": ["version"],
            "properties": {"version": {"type": "string"}},
        }
        (schemas_dir / "timeline_entry.schema.json").write_text(json.dumps(timeline_schema), encoding="utf-8")

        # Create invalid timeline file (missing required "version")
        timeline_dir = tmp_path / "output" / "timeline"
        timeline_dir.mkdir(parents=True)
        (timeline_dir / "snap.json").write_text('{"bad": true}', encoding="utf-8")

        registry, schemas_map = create_registry(str(schemas_dir))

        with patch("config.OUTPUT_DIR", str(tmp_path / "output")), patch("config.PATCH_HISTORY_DIR", "timeline"):
            errors = validate_timeline_metadata(registry, schemas_map)
        assert errors >= 1
