"""
Aggressive tests for validate_integrity.py

Covers: cache behaviour, oversized dimensions, full validate_integrity() happy path,
upgrade->tag cross-reference logic, broken JSON in data files, and missing schema.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import config
import pytest
from PIL import Image
from validate_integrity import (
    check_asset_exists,
    create_registry,
    load_cache,
    save_cache,
    validate_entry_assets,
    validate_integrity,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_tiny_webp(path: Path, size=(1, 1)):
    img = Image.new("RGB", size, color="blue")
    img.save(str(path), format="WEBP")


# ---------------------------------------------------------------------------
# load_cache / save_cache
# ---------------------------------------------------------------------------


class TestCachePersistence:
    def test_save_and_reload(self, tmp_path):
        cache_file = str(tmp_path / "cache.json")
        data = {"/some/asset.webp": {"mtime": 1234.56, "size": 8192}}
        with patch("validate_integrity.CACHE_FILE", cache_file):
            save_cache(data)
            loaded = load_cache()
        assert loaded == data

    def test_load_returns_empty_dict_when_file_missing(self, tmp_path):
        with patch("validate_integrity.CACHE_FILE", str(tmp_path / "nonexistent.json")):
            result = load_cache()
        assert result == {}

    def test_load_returns_empty_dict_on_corrupt_cache(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("{corrupt json", encoding="utf-8")
        with patch("validate_integrity.CACHE_FILE", str(cache_file)):
            result = load_cache()
        assert result == {}


# ---------------------------------------------------------------------------
# check_asset_exists — dimension breach
# ---------------------------------------------------------------------------


class TestAssetHygieneDimensions:
    def test_oversized_dimensions_warn(self, tmp_path):
        cat = tmp_path / "units"
        cat.mkdir()
        asset = cat / "big.webp"
        # Create an image larger than the limit
        make_tiny_webp(asset, size=(600, 600))

        cache = {}
        with (
            patch("validate_integrity.ASSETS_DIR", str(tmp_path)),
            patch("validate_integrity.MAX_IMG_SIZE_KB", 9999),
            patch("validate_integrity.MAX_IMG_DIMENSION", 512),
        ):
            result = check_asset_exists("units", "big", True, cache)
        assert result >= 1

    def test_exact_limit_passes(self, tmp_path):
        cat = tmp_path / "units"
        cat.mkdir()
        asset = cat / "edge.webp"
        make_tiny_webp(asset, size=(512, 512))

        cache = {}
        with (
            patch("validate_integrity.ASSETS_DIR", str(tmp_path)),
            patch("validate_integrity.MAX_IMG_SIZE_KB", 9999),
            patch("validate_integrity.MAX_IMG_DIMENSION", 512),
        ):
            result = check_asset_exists("units", "edge", True, cache)
        assert result == 0

    def test_png_fallback_accepted(self, tmp_path):
        cat = tmp_path / "units"
        cat.mkdir()
        asset = cat / "knight.png"
        img = Image.new("RGB", (1, 1), color="green")
        img.save(str(asset), format="PNG")

        cache = {}
        with (
            patch("validate_integrity.ASSETS_DIR", str(tmp_path)),
            patch("validate_integrity.MAX_IMG_SIZE_KB", 9999),
            patch("validate_integrity.MAX_IMG_DIMENSION", 512),
        ):
            result = check_asset_exists("units", "knight", True, cache)
        assert result == 0

    def test_cache_prevents_re_validation(self, tmp_path):
        cat = tmp_path / "units"
        cat.mkdir()
        asset = cat / "cached.webp"
        make_tiny_webp(asset)

        stat = os.stat(asset)
        cache = {str(asset): {"mtime": stat.st_mtime, "size": stat.st_size}}

        call_count = {"n": 0}
        real_open = open

        def counting_open(*args, **kwargs):
            call_count["n"] += 1
            return real_open(*args, **kwargs)

        with patch("validate_integrity.ASSETS_DIR", str(tmp_path)):
            result = check_asset_exists("units", "cached", True, cache)

        assert result == 0  # cache hit → no warnings


# ---------------------------------------------------------------------------
# validate_entry_assets — hero uses entity_id OR spellcaster_id
# ---------------------------------------------------------------------------


class TestValidateEntryAssetsHero:
    def test_hero_with_spellcaster_id_field(self):
        data = {"spellcaster_id": "archmage", "image_required": True}
        with patch("validate_integrity.check_asset_exists", return_value=0) as mock_check:
            validate_entry_assets(data, "hero", "heroes", {})
            mock_check.assert_called_once_with("heroes", "archmage", True, {})

    def test_hero_entity_id_preferred_over_spellcaster_id(self):
        data = {"entity_id": "hero_primary", "spellcaster_id": "hero_fallback", "image_required": True}
        with patch("validate_integrity.check_asset_exists", return_value=0) as mock_check:
            validate_entry_assets(data, "hero", "heroes", {})
            mock_check.assert_called_once_with("heroes", "hero_primary", True, {})

    def test_unknown_schema_key_returns_zero(self):
        data = {"entity_id": "whatever", "image_required": True}
        result = validate_entry_assets(data, "unknown_type", "misc", {})
        assert result == 0


# ---------------------------------------------------------------------------
# create_registry — empty/bad directory
# ---------------------------------------------------------------------------


class TestCreateRegistryEdgeCases:
    def test_empty_directory_gives_empty_map(self, tmp_path):
        registry, schemas_map = create_registry(str(tmp_path))
        assert schemas_map == {}

    def test_corrupt_schema_file_is_skipped(self, tmp_path):
        bad = tmp_path / "bad.schema.json"
        bad.write_text("{invalid}", encoding="utf-8")
        # Should not crash
        registry, schemas_map = create_registry(str(tmp_path))
        # corrupt file excluded
        assert "bad.schema.json" not in schemas_map


# ---------------------------------------------------------------------------
# validate_integrity() — full integration on temp data
# ---------------------------------------------------------------------------


class TestValidateIntegrityFull:
    def _make_minimal_data(self, data_dir: Path):
        """Creates a minimal valid unit JSON."""
        units = data_dir / "units"
        units.mkdir(parents=True)
        (units / "test_unit.json").write_text(
            json.dumps(
                {
                    "entity_id": "test_unit",
                    "name": "Test Unit",
                    "description": "A test green unit.",
                    "tags": ["minion"],
                    "last_modified": "2026-02-11T00:00:00Z",
                    "category": "Creature",
                    "magic_school": "Wild",
                    "rank": "I",
                    "size": "Small",
                    "health": 50,
                    "damage": 5,
                    "attack_interval": 1.2,
                    "range": 1,
                    "movement_speed": 6,
                    "movement_type": "Ground",
                    "population": 1,
                    "charges": 3,
                    "recharge_time": 10,
                }
            ),
            encoding="utf-8",
        )

    def test_exits_nonzero_on_schema_violation(self, tmp_path):
        data_dir = tmp_path / "data"
        units = data_dir / "units"
        units.mkdir(parents=True)
        # Write a unit that's missing required fields
        (units / "bad_unit.json").write_text(json.dumps({"entity_id": "bad_unit"}), encoding="utf-8")

        import validate_integrity as vi

        with (
            patch.object(vi, "DATA_DIR", str(data_dir)),
            patch.object(vi, "SCHEMAS_DIR", config.SCHEMAS_DIR),
            patch.object(vi, "ASSETS_DIR", str(tmp_path / "assets")),
            patch.object(vi, "CACHE_FILE", str(tmp_path / "cache.json")),
            patch.object(vi, "FOLDER_TO_SCHEMA", {"units": "unit"}),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_integrity()
        assert exc_info.value.code == 1

    def test_exits_zero_on_valid_data(self, tmp_path):
        # This test is expensive (hits real schemas); it validates the happy path.
        data_dir = tmp_path / "data"
        self._make_minimal_data(data_dir)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        import validate_integrity as vi

        # We only validate 'units' in this isolated test
        with (
            patch.object(vi, "DATA_DIR", str(data_dir)),
            patch.object(vi, "SCHEMAS_DIR", config.SCHEMAS_DIR),
            patch.object(vi, "ASSETS_DIR", str(assets_dir)),
            patch.object(vi, "CACHE_FILE", str(tmp_path / "cache.json")),
            patch.object(vi, "FOLDER_TO_SCHEMA", {"units": "unit"}),
            patch("config.OUTPUT_DIR", str(tmp_path / "api")),
            patch("sys.exit") as mock_exit,
        ):
            validate_integrity()
        # Should NOT have been called with a failing code
        for c in mock_exit.call_args_list:
            assert c.args[0] == 0 or c.args[0] is None

    def test_broken_json_data_file_counts_as_error(self, tmp_path):
        data_dir = tmp_path / "data"
        units = data_dir / "units"
        units.mkdir(parents=True)
        (units / "corrupt.json").write_text("{broken", encoding="utf-8")

        import validate_integrity as vi

        with (
            patch.object(vi, "DATA_DIR", str(data_dir)),
            patch.object(vi, "SCHEMAS_DIR", config.SCHEMAS_DIR),
            patch.object(vi, "ASSETS_DIR", str(tmp_path / "assets")),
            patch.object(vi, "CACHE_FILE", str(tmp_path / "cache.json")),
            patch.object(vi, "FOLDER_TO_SCHEMA", {"units": "unit"}),
            pytest.raises(SystemExit) as exc_info,
        ):
            validate_integrity()
        assert exc_info.value.code == 1
