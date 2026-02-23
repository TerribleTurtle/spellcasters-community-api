import json
import os
import sys
from unittest.mock import patch

import pytest

# Ensure scripts module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import build_api  # noqa: E402


@pytest.fixture
def temp_output_dir(tmp_path):
    """Creates a temporary directory for build output."""
    d = tmp_path / "api_v1"
    d.mkdir()
    return str(d)


@pytest.fixture
def build_output(temp_output_dir):
    """
    Runs the build_api.main() once and returns the output directory.
    """
    with patch("build_api.OUTPUT_DIR", temp_output_dir):
        # Prevent sys.exit() from stopping the test runner if build fails
        with patch("sys.exit") as mock_exit:
            build_api.main()

            # Ensure it didn't exit with error
            if mock_exit.called:
                args = mock_exit.call_args[0]
                assert args[0] == 0, f"Build script exited with error code {args[0]}"

    return temp_output_dir


def test_build_api_generates_files(build_output):
    """
    Verifies that the build generated the expected key files.
    """
    expected_files = ["all_data.json", "units.json", "spells.json", "game_config.json"]

    for fname in expected_files:
        path = os.path.join(build_output, fname)
        assert os.path.exists(path), f"Expected build artifact {fname} not found."

        # Verify valid JSON
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
            assert content, f"{fname} is empty"


def test_all_data_structure(build_output):
    """
    Verifies that all_data.json contains the aggregated keys.
    """
    all_data_path = os.path.join(build_output, "all_data.json")
    with open(all_data_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "build_info" in data
    assert "units" in data
    assert "spells" in data
    assert isinstance(data["units"], list)
