"""Tests for CLI error handling."""

import subprocess
import sys


def test_cli_invalid_flag():
    """Test that invalid CLI flag returns non-zero exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "--badflag"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0

