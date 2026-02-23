"""
Unit tests for validate_integrity.py

Tests the core validation utility functions: registry creation,
asset existence checks, and entry asset validation.
"""

import os
from unittest.mock import patch

import config
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
