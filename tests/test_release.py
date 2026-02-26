import json
import os
import sys
from unittest.mock import patch

import pytest

import release


# ---------------------------------------------------------------------------
# bump_version
# ---------------------------------------------------------------------------

class TestBumpVersion:
    def test_bump_major(self):
        assert release.bump_version("1.2.3", "major") == "2.0.0"

    def test_bump_minor(self):
        assert release.bump_version("1.2.3", "minor") == "1.3.0"

    def test_bump_patch(self):
        assert release.bump_version("1.2.3", "patch") == "1.2.4"

    def test_evil_malformed_version(self):
        """Should catch ValueError and fallback to 0.0.X depending on bump type."""
        # Parts length != 3
        assert release.bump_version("1.2", "patch") == "0.0.1"
        assert release.bump_version("invalid", "minor") == "0.1.0"
        
        # Parts length == 3 but not integers
        assert release.bump_version("1.b.3", "major") == "1.0.0"


# ---------------------------------------------------------------------------
# main (Interactive flow tests)
# ---------------------------------------------------------------------------

class TestMainIntegration:
    @pytest.fixture
    def setup_files(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        game_config = data_dir / "game_config.json"
        game_config.write_text(json.dumps({"version": "1.0.0"}), encoding="utf-8")
        
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [1.0.0] - 2026-01-01\n\nInitial release", encoding="utf-8")
        
        return {
            "DATA_DIR": str(data_dir),
            "GAME_CONFIG_PATH": str(game_config),
            "CHANGELOG_PATH": str(changelog)
        }

    def test_successful_release(self, setup_files):
        """Simulate a successful interactive 'minor' bump."""
        inputs = ["minor"]
        
        def mock_input(prompt):
            return inputs.pop(0)
            
        class MockStdin:
            def readlines(self):
                return ["Line 1\n", "Line 2\n"]
                
        with patch("release.GAME_CONFIG_PATH", setup_files["GAME_CONFIG_PATH"]), \
             patch("release.CHANGELOG_PATH", setup_files["CHANGELOG_PATH"]), \
             patch("builtins.input", side_effect=mock_input), \
             patch("sys.stdin", new_callable=lambda: MockStdin()):
             
             release.main()
             
        # Verify JSON
        config = release.load_json(setup_files["GAME_CONFIG_PATH"])
        assert config["version"] == "1.1.0"
        assert len(config["changelog"]) == 1
        assert config["changelog"][0]["version"] == "1.1.0"
        assert config["changelog"][0]["description"] == "Line 1\nLine 2"
        
        # Verify Markdown
        with open(setup_files["CHANGELOG_PATH"], encoding="utf-8") as f:
            md = f.read()
            
        assert "## [1.1.0]" in md
        assert "Line 1\nLine 2" in md
        assert "## [1.0.0]" in md # Old version still there

    def test_evil_missing_game_config(self, setup_files):
        """Should abort if game_config doesn't exist."""
        with patch("release.GAME_CONFIG_PATH", "/nonexistent/path/game_config.json"):
            with pytest.raises(SystemExit) as exc_info:
                release.main()
            assert exc_info.value.code == 1
            
    def test_evil_invalid_bump_type(self, setup_files):
        """Should abort on bad bump type."""
        with patch("release.GAME_CONFIG_PATH", setup_files["GAME_CONFIG_PATH"]), \
             patch("builtins.input", return_value="garbage"):
            with pytest.raises(SystemExit) as exc_info:
                release.main()
            assert exc_info.value.code == 1

    def test_evil_empty_notes(self, setup_files):
        """Should abort if release notes are empty."""
        class MockEmptyStdin:
            def readlines(self):
                return []
                
        with patch("release.GAME_CONFIG_PATH", setup_files["GAME_CONFIG_PATH"]), \
             patch("builtins.input", return_value="patch"), \
             patch("sys.stdin", new_callable=lambda: MockEmptyStdin()):
            with pytest.raises(SystemExit) as exc_info:
                release.main()
            assert exc_info.value.code == 1

    def test_evil_eof_during_notes(self, setup_files):
        """Should handle EOF gracefully and abort due to empty notes."""
        class MockEOFStdin:
            def readlines(self):
                raise EOFError()
                
        with patch("release.GAME_CONFIG_PATH", setup_files["GAME_CONFIG_PATH"]), \
             patch("builtins.input", return_value="patch"), \
             patch("sys.stdin", new_callable=lambda: MockEOFStdin()):
            with pytest.raises(SystemExit) as exc_info:
                release.main()
            assert exc_info.value.code == 1

    def test_evil_missing_changelog(self, setup_files, tmp_path):
        """Should create CHANGELOG.md if it doesn't exist at all."""
        missing_changelog = tmp_path / "MISSING.md"
        
        class MockStdin:
            def readlines(self):
                return ["New file notes"]
                
        with patch("release.GAME_CONFIG_PATH", setup_files["GAME_CONFIG_PATH"]), \
             patch("release.CHANGELOG_PATH", str(missing_changelog)), \
             patch("builtins.input", return_value="major"), \
             patch("sys.stdin", new_callable=lambda: MockStdin()):
             
             release.main()
             
        assert missing_changelog.exists()
        with open(missing_changelog, encoding="utf-8") as f:
            md = f.read()
            assert "# Changelog" in md
            assert "## [2.0.0]" in md
            assert "New file notes" in md
